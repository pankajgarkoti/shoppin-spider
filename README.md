# Basic Web Crawler to Find Product Pages

To get started, first build the docker image:
```bash
docker build -t spider .
```

Run the container by executing:
```bash
docker run -d -p 8000:8000 spider
```

The test script is called `mock.py` - once the docker container is up and running, you can execute `python3 mock.py` to initiate a test run of the crawler.
# Basic Web Crawler to Find Product Pages

To get started, first build the docker image:
```bash
docker build -t spider .
```

Run the container by executing:
```bash
docker run -d -p 8000:8000 spider
```

The test script is called `mock.py` - once the docker container is up and running, you can execute `python3 mock.py` to initiate a test run of the crawler.
# Basic Web Crawler to Find Product Pages

This project is a web crawler designed to identify and collect product pages from various websites. It is built using Python and leverages FastAPI for the API layer, SQLModel for database interactions, and asyncio for asynchronous operations. The system is containerized using Docker for easy deployment.

## Features

- **Asynchronous Crawling**: Utilizes `aiohttp` and `asyncio` for efficient, non-blocking web crawling.
- **Product URL Filtering**: Identifies product pages using regex patterns.
- **Job Management**: Supports multiple concurrent crawling jobs with status tracking.
- **REST API**: Provides endpoints to start a crawl and check the status of a job.
- **Dockerized**: Easily deployable using Docker.

## Components

### 1. Web Crawler

The core of the system is the `WebCrawler` class, which manages the crawling process. It uses a queue to manage URLs to be visited and a set to track visited URLs. The crawler fetches pages asynchronously and parses them using BeautifulSoup to extract links.

### 2. API

The API is built using FastAPI and provides endpoints to start a new crawling job and to check the status of an existing job. The `start_crawler` endpoint initiates a new crawl, while the `get_job_status` endpoint retrieves the status and results of a crawl.


```19:54:src/api/crud.py
@_router.post("/jobs")
async def start_crawler(config: CrawlerConfig, background_tasks: BackgroundTasks):
    """Start a new crawler job in the background."""
    ...


@_router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and results of a crawler job.
    """
    ...
```


### 3. Database Models

The system uses SQLModel to define database models for storing crawled data and job information. The `CrawlingJobManager` and `CrawledDataManager` classes handle database operations.


```10:139:src/core/models/crawled_data.py
class CrawledData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str
    url: str
    content: str


class CrawlingJob(SQLModel, table=True):
    job_id: str = Field(primary_key=True)
    completed: bool = Field(default=False)
    max_pages: int = Field(default=100)

    starting_urls: List["CrawlingJobStartingURL"] = Relationship(back_populates="job")
    visited_urls: List["CrawlingJobVisitedURL"] = Relationship(back_populates="job")
    product_urls: List["CrawlingJobProductURL"] = Relationship(back_populates="job")


class CrawlingJobStartingURL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="crawlingjob.job_id")
    url: str

    job: CrawlingJob = Relationship(back_populates="starting_urls")


class CrawlingJobVisitedURL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="crawlingjob.job_id")
    url: str

    job: CrawlingJob = Relationship(back_populates="visited_urls")


class CrawlingJobProductURL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="crawlingjob.job_id")
    url: str

    job: CrawlingJob = Relationship(back_populates="product_urls")


class CrawlingJobManager:
    def __init__(self):
        self.engine = engine
        SQLModel.metadata.create_all(self.engine)

    def add_job(self, job_id: str, starting_urls: list[str], max_pages: int):
        """Add a new crawling job to the database."""
        with Session(self.engine) as session:
            crawling_job = CrawlingJob(
                job_id=job_id,
                starting_urls=[
                    CrawlingJobStartingURL(url=url, job_id=job_id)
                    for url in starting_urls
                ],
                max_pages=max_pages,
                visited_urls=[],
                product_urls=[],
            )
            session.add(crawling_job)
            session.commit()

    def update_job(
        self,
        job_id: str,
        completed: bool,
        visited_urls: list[str],
        product_urls: list[str],
    ):
        """Update the crawling job in the database."""
        with Session(self.engine) as session:
            query = select(CrawlingJob).where(CrawlingJob.job_id == job_id)
            results = session.exec(query).all()
            if results:
                crawling_job: CrawlingJob = results[0]
                crawling_job.visited_urls = [
                    CrawlingJobVisitedURL(url=url, job_id=job_id)
                    for url in visited_urls
                ]
                crawling_job.product_urls = [
                    CrawlingJobProductURL(url=url, job_id=job_id)
                    for url in product_urls
                ]
                crawling_job.completed = completed
                session.add(crawling_job)
                session.commit()
                return True
            else:
                return False

    def get_job_status(self, job_id: str):
        """Get the status of a crawling job."""
        with Session(self.engine) as session:
            query = select(CrawlingJob).where(CrawlingJob.job_id == job_id)
            results = session.exec(query).all()
            if results:
                crawling_job: CrawlingJob = results[0]
                return {
                    "job_id": crawling_job.job_id,
                    "completed": crawling_job.completed,
                    "visited_urls": [
                        visited.url for visited in crawling_job.visited_urls
                    ],
                    "product_urls": [
                        product_url.url for product_url in crawling_job.product_urls
                    ],
                    "max_pages": crawling_job.max_pages,
                }
            else:
                return None


class CrawledDataManager:
    def __init__(self):
        self.engine = engine
        SQLModel.metadata.create_all(self.engine)

    def save(self, job_id: str, url: str, content: str):
        """Save the crawled page content to the database."""
        with Session(self.engine) as session:
            crawled_data = CrawledData(job_id=job_id, url=url, content=content)
            session.add(crawled_data)
            session.commit()

    def get_results(self, job_id: str):
        """Return a list of visited URLs by a job ID."""
        with Session(self.engine) as session:
            query = select(CrawledData).where(CrawledData.job_id == job_id)
            results = session.exec(query)
            return [result.model_dump() for result in results]
```


### 4. Utilities

A utility function `filter_product_urls` is used to identify product pages based on specific URL patterns.


```4:42:src/core/utils.py
def filter_product_urls(urls: list[str]) -> list[str]:
    """
    From a list of URLs select the ones that are product pages.
    The product pages are identified by the presence of specific patterns in the URL.

    Common patterns detected:
    - /p/, /product/, /item/ in the path
    - Product IDs/SKUs (alphanumeric sequences)
    - Category hierarchies leading to products
    - Product detail or PDP indicators

    Args:
        urls (list[str]): list of URLs
    Returns:
        list[str]: list of product URLs
    """

    patterns_regex = [
        r"/p/[\w-]+",  # /p/ followed by product identifier
        r"/product/[\w-]+",  # /product/ followed by identifier
        r"/item/[\w-]+",  # /item/ followed by identifier
        r"/[\w-]+/[\w-]+/p/[\w-]+",  # category/subcategory/p/product structure
        r"/pd/[\w-]+",  # product detail pages
        r"/[\w-]+/\d+\.html",  # product pages with numeric IDs
        r"/products?/[\w-]{6,}",  # /product(s)/ with longer identifiers
        r"/catalog/product/view/id/\d+",  # common ecommerce platform pattern
        r"/dp/[A-Z0-9]{10}",  # Amazon-style product identifiers
        r"-pid-\d+",  # PID based product identifiers
    ]

    # Combine all patterns with OR operator
    combined_pattern = "|".join(f"({pattern})" for pattern in patterns_regex)

    # Filter URLs that match any of the patterns
    product_urls = [
        url for url in urls if re.search(combined_pattern, url, re.IGNORECASE)
    ]

    return product_urls
```


## Setup and Usage

### Prerequisites

- Docker
- Python 3.11

### Building and Running the Docker Container

1. **Build the Docker Image**:
   ```bash
   docker build -t spider .
   ```

2. **Run the Docker Container**:
   ```bash
   docker run -d -p 8000:8000 spider
   ```

### Running the Crawler

Once the Docker container is running, you can initiate a test run of the crawler using the `mock.py` script:

```bash
python3 mock.py
```

This script submits a job to the API and continuously polls for its status.


```1:40:mock.py
import json
import time
import requests

SERVICE_URL = "http://localhost:8000"

def submit_job(starting_urls: list[str]):
    payload = {"starting_urls": starting_urls, "max_pages": 200}
    response = requests.post(SERVICE_URL + "/jobs", json=payload)
    response.raise_for_status()
    res = response.json()

    return res["job_id"]


def get_job_status(job_id: str):
    response = requests.get(SERVICE_URL + f"/jobs/{job_id}")
    response.raise_for_status()
    res = response.json()

    return res


def mock():
    starting_urls = ["https://www.amazon.com", "https://flipkart.com"]

    job_id = submit_job(starting_urls)

    while True:
        # poll the job status endpoint
        job_status = get_job_status(job_id)
        print("===========")
        print(json.dumps(job_status, indent=4))
        print("===========")
        time.sleep(1)


if __name__ == "__main__":
    mock()
```

## Conclusion

This web crawler is a robust solution for identifying and collecting product pages from the web. Its asynchronous design and REST API make it scalable and easy to integrate into larger systems. The use of Docker ensures that it can be deployed consistently across different environments.

# Disclosure: I used cursor to generate this README file from the codebase.