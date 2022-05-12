from unittest.mock import MagicMock

import pkg_resources
import pytest
from pytest_httpserver import HTTPServer

from prowjobscraper import prowjob, scraper, step


def test_non_assisted_jobs_are_filtered_out():
    jobs = prowjob.ProwJobs.create_from_string(
        pkg_resources.resource_string(__name__, f"scraper_assets/prowjob.json")
    )

    event_store = MagicMock()
    event_store.scan_build_ids.return_value = []

    step_extractor = MagicMock()
    step_extractor.parse_prow_jobs.return_value = []

    scrape = scraper.Scraper(event_store, step_extractor)

    jobs.items[0].spec.job = "we-don-t-say-the-name"
    jobs.items[0].status.state = "success"
    scrape.execute(jobs.copy(deep=True))
    event_store.index_prow_jobs.assert_called_once_with([])

    event_store.reset_mock()
    jobs.items[0].spec.job = "e2e-blala-assisted"
    jobs.items[0].status.state = "pending"
    scrape.execute(jobs.copy(deep=True))
    event_store.index_prow_jobs.assert_called_once_with([])

    event_store.reset_mock()
    jobs.items[0].spec.job = "e2e-blala-assisted"
    jobs.items[0].status.state = "success"
    jobs.items[0].status.description = "Overridden by Batman"
    scrape.execute(jobs.copy(deep=True))
    event_store.index_prow_jobs.assert_called_once_with([])


def test_assisted_jobs_are_not_filtered_out():
    jobs = prowjob.ProwJobs.create_from_string(
        pkg_resources.resource_string(__name__, f"scraper_assets/prowjob.json")
    )

    event_store = MagicMock()
    event_store.scan_build_ids.return_value = []

    step_extractor = MagicMock()
    step_extractor.parse_prow_jobs.return_value = []

    scrape = scraper.Scraper(event_store, step_extractor)

    jobs.items[0].spec.job = "e2e-blala-assisted"
    jobs.items[0].status.state = "success"
    scrape.execute(jobs.copy(deep=True))
    event_store.index_prow_jobs.assert_called_once_with(jobs.items)

    event_store.reset_mock()
    jobs.items[0].spec.job = "something-e2e-blala-assisted-test"
    jobs.items[0].status.state = "failure"
    scrape.execute(jobs.copy(deep=True))
    event_store.index_prow_jobs.assert_called_once_with(jobs.items)


def test_existing_jobs_in_event_store_are_filtered_out():
    jobs = prowjob.ProwJobs.create_from_string(
        pkg_resources.resource_string(__name__, f"scraper_assets/prowjob.json")
    )

    event_store = MagicMock()
    event_store.scan_build_ids.return_value = [jobs.items[0].status.build_id]

    step_extractor = MagicMock()
    step_extractor.parse_prow_jobs.return_value = []

    scrape = scraper.Scraper(event_store, step_extractor)
    jobs.items[0].spec.job = "e2e-blala-assisted"
    jobs.items[0].status.state = "success"
    scrape.execute(jobs.copy(deep=True))
    event_store.index_prow_jobs.assert_called_once_with([])


def test_jobs_and_steps_are_indexed():
    jobstep = step.JobStep.parse_raw(
        pkg_resources.resource_string(__name__, f"scraper_assets/jobstep.json")
    )
    jobs = prowjob.ProwJobs(items=[jobstep.job])

    event_store = MagicMock()
    event_store.scan_build_ids.return_value = []

    step_extractor = MagicMock()
    step_extractor.parse_prow_jobs.return_value = [jobstep]

    scrape = scraper.Scraper(event_store, step_extractor)
    scrape.execute(jobs.copy(deep=True))
    event_store.index_prow_jobs.assert_called_once_with(jobs.items)
    event_store.index_job_steps.assert_called_once_with([jobstep])
