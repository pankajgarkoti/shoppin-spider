from bs4 import BeautifulSoup
from collections import deque
import logging


import asyncio
import logging
from aiohttp import ClientSession
from collections import deque
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from src.core.models.crawled_data import (
    CrawledDataManager,
    CrawlingJobManager,
)
from src.core.utils import filter_product_urls


class WebCrawler:
    def __init__(
        self,
        job_id: str,
    ):
        self.visited = set()
        self.job_id = job_id
        self.queue = deque()
        self.data_manager = CrawledDataManager()
        self.job_manager = CrawlingJobManager()

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        self.headers = {
            "User-Agent": "Shoppin' Crawler",
            "From": "garkotipankaj@gmail.com",
        }
        self.delay = 0.2

    def add_starting_urls(self, urls: list[str]):
        """Add multiple starting URLs to the queue."""
        for url in urls:
            self.queue.append((self.job_id, url))

    async def fetch(self, session: ClientSession, url: str):
        """Fetch a URL asynchronously."""
        try:
            async with session.get(url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logging.warning(f"HTTP Error {response.status} for {url}")
                    return None
        except asyncio.TimeoutError:
            logging.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    async def crawl_single_url(
        self, session: ClientSession, start_url: str, max_pages: int
    ):
        """Crawl starting from a single URL."""
        pages_crawled = 0
        queue = deque([(self.job_id, start_url)])  # Local queue for each starting URL
        visited = set()  # Local visited set

        while queue and pages_crawled < max_pages:
            job_id, url = queue.popleft()

            if url in visited:
                continue

            try:
                logging.info(f"Crawling: {url}")
                await asyncio.sleep(self.delay)

                content = await self.fetch(session, url)
                if content is None:  # Handle fetch failures
                    continue

                self.data_manager.save(job_id, url, content)

                soup = BeautifulSoup(content, "html.parser")

                for link in soup.find_all("a"):
                    href = link.get("href")
                    if href:
                        full_url = urljoin(url, href)
                        if full_url not in visited:
                            queue.append((job_id, full_url))

                visited.add(url)
                pages_crawled += 1

            except Exception as e:
                logging.error(f"Error crawling {url}: {str(e)}")
        return visited, pages_crawled

    async def crawl(self, starting_urls: list[str], max_pages=100):
        """Main crawling method using asyncio.gather to run concurrently for each starting url."""
        total_pages_crawled = 0
        all_visited = set()

        async with ClientSession() as session:
            tasks = [
                self.crawl_single_url(session, url, max_pages) for url in starting_urls
            ]
            results = await asyncio.gather(*tasks)

        for visited, pages_crawled in results:
            total_pages_crawled += pages_crawled
            all_visited.update(visited)

        logging.info(f"Crawling completed. Visited {total_pages_crawled} pages.")
        return list(all_visited)

    async def run(self, starting_urls: list[str], max_pages=100):
        """Start the crawling process."""
        self.job_manager.add_job(
            job_id=self.job_id, starting_urls=starting_urls, max_pages=max_pages
        )

        visited_urls = await self.crawl(starting_urls, max_pages)

        self.job_manager.update_job(
            job_id=self.job_id,
            completed=True,
            visited_urls=visited_urls,
            product_urls=filter_product_urls(visited_urls),
        )
