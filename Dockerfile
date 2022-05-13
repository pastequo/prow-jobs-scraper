FROM registry.access.redhat.com/ubi8/python-39:latest

COPY . .

RUN make install

ENTRYPOINT [ "prow-jobs-scraper" ]