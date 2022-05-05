FROM registry.access.redhat.com/ubi8/python-39:latest

COPY . .

RUN pip install .

ENTRYPOINT [ "prow-job-scraper" ]