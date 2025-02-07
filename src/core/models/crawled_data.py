from typing import List, Optional
from sqlalchemy import create_engine
from sqlmodel import Relationship, SQLModel, Field, Session, select


DATABASE_URL = "sqlite:///crawled_data.db"
engine = create_engine(DATABASE_URL)


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
