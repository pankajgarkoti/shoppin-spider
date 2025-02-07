# Basic Web Crawler to Find Product Pages

To get started, first build the docker image:
```bash
docker build -t spider .
```

Run the container by executing:
```bash
docker run -d -p 8000:8000 spider
```

The test script is called `mock.py` once the docker container is up and running, you can execute `python3 mock.py` to initiate a test run of the crawler.
