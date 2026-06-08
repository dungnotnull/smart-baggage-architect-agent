"""Airline policy web scraper using crawl4ai for automatic refreshes."""

import hashlib
from datetime import datetime
from pathlib import Path

import yaml

from app.config import settings
from app.services.airline_policy import policy_engine

AIRLINE_SCRAPING_TARGETS: dict[str, dict] = {
    "AA": {"url": "https://www.aa.com/i18n/travel-info/baggage/", "selector": ".baggage-info"},
    "UA": {"url": "https://www.united.com/en/us/fly/travel/baggage/", "selector": ".baggage-content"},
    "DL": {"url": "https://www.delta.com/us/en/baggage/overview", "selector": ".baggage-overview"},
    "WN": {"url": "https://www.southwest.com/air/baggage/", "selector": ".baggage-rules"},
    "BA": {"url": "https://www.britishairways.com/en-gb/information/baggage-essentials", "selector": ".baggage-info"},
    "LH": {"url": "https://www.lufthansa.com/us/en/baggage", "selector": ".baggage-section"},
    "EK": {"url": "https://www.emirates.com/english/help/baggage/", "selector": ".baggage-detail"},
    "SQ": {"url": "https://www.singaporeair.com/en_UK/plan-travel/baggage/", "selector": ".baggage-content"},
}


class AirlinePolicyScraper:
    """Scrape airline websites for baggage policy updates."""

    def __init__(self, policies_dir: Path | None = None):
        self.policies_dir = policies_dir or Path(settings.airline_policies_dir)
        self.diff_log: list[dict] = []

    def scrape_airline(self, iata_code: str) -> dict | None:
        """Scrape a single airline's baggage policy page."""
        target = AIRLINE_SCRAPING_TARGETS.get(iata_code.upper())
        if not target:
            return None

        try:
            import asyncio

            from crawl4ai import AsyncWebCrawler

            async def _scrape():
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=target["url"])
                    return result

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, _scrape()).result()
            else:
                result = asyncio.run(_scrape())

            return {
                "iata_code": iata_code.upper(),
                "url": target["url"],
                "content_hash": hashlib.sha256(result.markdown.encode()).hexdigest()[:16],
                "scraped_at": datetime.utcnow().isoformat(),
                "content_length": len(result.markdown),
                "content_preview": result.markdown[:500],
            }
        except ImportError:
            return {
                "iata_code": iata_code.upper(),
                "url": target["url"],
                "error": "crawl4ai not installed",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "iata_code": iata_code.upper(),
                "url": target["url"],
                "error": str(e),
                "scraped_at": datetime.utcnow().isoformat(),
            }

    def scrape_all_configured(self) -> list[dict]:
        """Scrape all configured airline policy pages."""
        results = []
        for iata_code in AIRLINE_SCRAPING_TARGETS:
            result = self.scrape_airline(iata_code)
            if result:
                results.append(result)
        return results

    def check_policy_freshness(self, iata_code: str) -> dict:
        """Check if a policy YAML needs updating based on hash comparison."""
        yaml_path = self.policies_dir / f"{iata_code.upper()}.yaml"
        if not yaml_path.exists():
            return {"iata_code": iata_code.upper(), "status": "missing", "needs_update": True}

        with open(yaml_path, encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        last_verified = yaml_content.get("last_verified", "2000-01-01")
        last_date = datetime.fromisoformat(last_verified)
        days_since = (datetime.utcnow() - last_date).days

        return {
            "iata_code": iata_code.upper(),
            "last_verified": last_verified,
            "days_since_verification": days_since,
            "needs_update": days_since > 30,
            "status": "stale" if days_since > 30 else "fresh",
        }

    def refresh_policy_from_scrape(self, iata_code: str, scraped_data: dict) -> bool:
        """Update YAML file with new data from scrape (preserving structure)."""
        yaml_path = self.policies_dir / f"{iata_code.upper()}.yaml"
        if not yaml_path.exists():
            return False

        with open(yaml_path, encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        old_hash = yaml_content.get("_content_hash", "")
        new_hash = scraped_data.get("content_hash", "")

        if new_hash and new_hash != old_hash:
            yaml_content["_content_hash"] = new_hash
            yaml_content["last_verified"] = datetime.utcnow().strftime("%Y-%m-%d")
            yaml_content["_last_scrape_url"] = scraped_data["url"]

            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True)

            policy_engine.invalidate_cache(iata_code)
            self.diff_log.append({
                "iata_code": iata_code.upper(),
                "old_hash": old_hash,
                "new_hash": new_hash,
                "updated_at": datetime.utcnow().isoformat(),
            })
            return True

        return False


airline_scraper = AirlinePolicyScraper()
