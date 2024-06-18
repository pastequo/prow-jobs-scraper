FROM registry.access.redhat.com/ubi9/python-311:latest

ARG version=latest

LABEL com.redhat.component prow-jobs-scraper
LABEL description "Fetching data about prow jobs to elasticsearch"
LABEL summary "Fetching data about prow jobs to elasticsearch"
LABEL io.k8s.description "Fetching data about prow jobs to elasticsearch"
LABEL distribution-scope public
LABEL name prow-jobs-scraper
LABEL release ${version}
LABEL version ${version}
LABEL url https://github.com/openshift-assisted/prow-jobs-scraper
LABEL vendor "Red Hat, Inc."
LABEL maintainer "Red Hat"

# License
COPY LICENSE /license/

COPY --chown=1001:0 . .

RUN pip install --upgrade pip && make install
