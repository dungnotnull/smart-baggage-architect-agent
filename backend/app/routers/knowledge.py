"""Knowledge crawler API endpoints."""

from fastapi import APIRouter

from app.services.knowledge_crawler import knowledge_crawler

router = APIRouter()


@router.post("/crawl")
async def run_crawl() -> dict:
    """Execute a full weekly crawl of all configured research sources."""
    result = knowledge_crawler.run_weekly_crawl()
    return result


@router.post("/crawl/arxiv")
async def crawl_arxiv(query: str = "object detection mobile real-time") -> dict:
    """Search ArXiv for papers matching a query."""
    papers = knowledge_crawler.crawl_arxiv(query)
    return {"query": query, "papers_found": len(papers), "papers": papers}


@router.post("/crawl/huggingface")
async def crawl_huggingface(tag: str = "object-detection") -> dict:
    """Fetch papers from HuggingFace Papers by tag."""
    papers = knowledge_crawler.crawl_huggingface_papers(tag)
    return {"tag": tag, "papers_found": len(papers), "papers": papers}
