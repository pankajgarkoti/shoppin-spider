from fastapi import HTTPException, BackgroundTasks
from fastapi.routing import APIRouter
from pydantic import BaseModel
from typing import List
import uuid

from src.core.crawler import WebCrawler
from src.core.models.crawled_data import CrawlingJobManager, CrawledDataManager
from src.core.utils import filter_product_urls

_router = APIRouter()


class CrawlerConfig(BaseModel):
    starting_urls: List[str]
    max_pages: int = 100


@_router.post("/jobs")
async def start_crawler(config: CrawlerConfig, background_tasks: BackgroundTasks):
    """Start a new crawler job in the background."""
    job_id = str(uuid.uuid4())
    crawler = WebCrawler(job_id=job_id)

    background_tasks.add_task(crawler.run, config.starting_urls, config.max_pages)
    return {
        "job_id": job_id,
        "message": "Crawling started successfully.",
    }


@_router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and results of a crawler job.
    """
    job_manager = CrawlingJobManager()
    data_manager = CrawledDataManager()

    job = job_manager.get_job_status(job_id)

    if job:
        results = data_manager.get_results(job_id)
        visited_urls = [result["url"] for result in results]
        product_urls = filter_product_urls(visited_urls)

        return {
            "job_id": job_id,
            "completed": job["completed"],
            "visited_urls": visited_urls,
            "product_urls": product_urls,
            "max_pages": job["max_pages"],
        }

    raise HTTPException(status_code=404, detail="Job not found")
