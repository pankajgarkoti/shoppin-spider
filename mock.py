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
