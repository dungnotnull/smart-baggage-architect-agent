"""Knowledge crawler service -- automated SECOND-KNOWLEDGE-BRAIN.md updater."""

import re
from datetime import datetime
from pathlib import Path

from app.config import settings

CRAWL_SOURCES = {
    "arxiv": {
        "base_url": "https://arxiv.org/search/",
        "categories": ["cs.CV", "cs.AI", "cs.LG"],
        "queries": [
            "object detection mobile real-time",
            "luggage suitcase item recognition",
            "travel recommendation personalization",
            "bin packing optimization heuristics",
            "on-device inference edge deployment",
            "vision language model zero-shot",
        ],
        "max_results_per_query": 5,
    },
    "huggingface_papers": {
        "base_url": "https://huggingface.co/papers",
        "tags": ["object-detection", "mobile", "travel", "optimization"],
    },
}


class KnowledgeCrawlerService:
    """Crawl research sources and update SECOND-KNOWLEDGE-BRAIN.md."""

    def __init__(self, knowledge_brain_path: str | None = None):
        base_dir = Path(settings.airline_policies_dir).parent.parent
        self.knowledge_brain_path = Path(
            knowledge_brain_path or str(base_dir / "SECOND-KNOWLEDGE-BRAIN.md")
        )

    def crawl_arxiv(self, query: str, max_results: int = 5) -> list[dict]:
        """Search ArXiv for relevant papers."""
        try:
            import asyncio

            from crawl4ai import AsyncWebCrawler

            url = (
                f"{CRAWL_SOURCES['arxiv']['base_url']}"
                f"?query={query.replace(' ', '+')}"
                f"&searchtype=all&start=0"
            )

            async def _crawl():
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url)
                    return result

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, _crawl()).result()
            else:
                result = asyncio.run(_crawl())

            return self._parse_arxiv_results(result.markdown, max_results)
        except ImportError:
            return []
        except Exception:
            return []

    def crawl_huggingface_papers(self, tag: str) -> list[dict]:
        """Fetch papers from HuggingFace Papers by tag."""
        try:
            import asyncio

            from crawl4ai import AsyncWebCrawler

            url = f"{CRAWL_SOURCES['huggingface_papers']['base_url']}?tag={tag}"

            async def _crawl():
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url)
                    return result

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, _crawl()).result()
            else:
                result = asyncio.run(_crawl())

            return self._parse_hf_results(result.markdown)
        except Exception:
            return []

    def _parse_arxiv_results(self, markdown: str, max_results: int = 5) -> list[dict]:
        """Parse ArXiv search results from markdown."""
        papers = []
        pattern = re.compile(
            r"(?:Title|title)[:\s]+(.+?)(?:\n|Authors)", re.IGNORECASE
        )
        for match in pattern.finditer(markdown):
            if len(papers) >= max_results:
                break
            papers.append({
                "title": match.group(1).strip(),
                "source": "arxiv",
                "crawled_at": datetime.utcnow().isoformat(),
            })
        return papers

    def _parse_hf_results(self, markdown: str) -> list[dict]:
        """Parse HuggingFace Papers results from markdown."""
        papers = []
        pattern = re.compile(r"\[([^\]]+)\]\(/papers/([^\)]+)\)")
        for match in pattern.finditer(markdown):
            papers.append({
                "title": match.group(1).strip(),
                "hf_id": match.group(2).strip(),
                "source": "huggingface_papers",
                "crawled_at": datetime.utcnow().isoformat(),
            })
        return papers

    def update_knowledge_brain(self, new_entries: list[dict]) -> int:
        """Append new research entries to SECOND-KNOWLEDGE-BRAIN.md."""
        if not new_entries or not self.knowledge_brain_path.exists():
            return 0

        with open(self.knowledge_brain_path, encoding="utf-8") as f:
            content = f.read()

        existing_titles = set(re.findall(r"\| (.+?) \|.*\|.*\|.*\|.*\|", content))
        rows_added = 0

        for entry in new_entries:
            title = entry.get("title", "").strip()
            if not title or title in existing_titles:
                continue

            date_stamp = entry.get("crawled_at", datetime.utcnow().isoformat())[:10]
            source = entry.get("source", "unknown")

            insertion_point = content.find("## Knowledge Update Log")
            if insertion_point == -1:
                table_header = (
                    "\n\n## Knowledge Update Log\n\n"
                    "| Date | Type | Entry Summary | Source |\n"
                    "|------|------|---------------|--------|\n"
                )
                content += table_header
                insertion_point = len(content)

            row = (
                f"| {date_stamp} | {source} | {title} | Auto-crawled |\n"
                f"<!-- Added: {date_stamp} | Source: {source} -->\n"
            )
            content = content[:insertion_point] + row + content[insertion_point:]
            rows_added += 1

        with open(self.knowledge_brain_path, "w", encoding="utf-8") as f:
            f.write(content)

        return rows_added

    def run_weekly_crawl(self) -> dict:
        """Execute a full weekly crawl of all configured sources."""
        all_entries: list[dict] = []

        for query in CRAWL_SOURCES["arxiv"]["queries"]:
            papers = self.crawl_arxiv(query)
            all_entries.extend(papers)

        for tag in CRAWL_SOURCES["huggingface_papers"]["tags"]:
            papers = self.crawl_huggingface_papers(tag)
            all_entries.extend(papers)

        rows_added = self.update_knowledge_brain(all_entries)

        return {
            "crawl_timestamp": datetime.utcnow().isoformat(),
            "total_entries_found": len(all_entries),
            "new_entries_added": rows_added,
            "sources_queried": list(CRAWL_SOURCES.keys()),
        }


knowledge_crawler = KnowledgeCrawlerService()
