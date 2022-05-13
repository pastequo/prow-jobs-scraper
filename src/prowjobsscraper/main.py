import logging
import sys

from google.cloud import storage  # type: ignore
from opensearchpy import OpenSearch

from prowjobsscraper import config, event, prowjob, scraper, step


def main() -> None:
    logging.basicConfig(stream=sys.stdout, level=config.LOG_LEVEL)
    # root = logging.getLogger()
    # handler = logging.StreamHandler(sys.stdout)
    # handler.setLevel(config.LOG_LEVEL)
    # formatter = logging.Formatter(
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # )
    # handler.setFormatter(formatter)
    # root.addHandler(handler)

    es_client = OpenSearch(
        config.ES_URL,
        http_auth=(config.ES_USER, config.ES_PASSWORD),
        verify_certs=False,
        ssl_show_warn=False,
    )
    event_store = event.EventStoreElastic(
        client=es_client,
        job_index_basename=config.ES_JOB_INDEX,
        step_index_basename=config.ES_STEP_INDEX,
    )

    gcloud_client = storage.Client.create_anonymous_client()
    step_extractor = step.StepExtractor(client=gcloud_client)

    jobs = prowjob.ProwJobs.create_from_url(config.JOB_LIST_URL)
    scrape = scraper.Scraper(event_store, step_extractor)
    scrape.execute(jobs)


if __name__ == "__main__":
    main()
