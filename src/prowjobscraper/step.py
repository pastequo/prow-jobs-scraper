import logging
from datetime import timedelta
from typing import Optional

from google.cloud import exceptions, storage  # type: ignore
from junitparser import Failure, JUnitXml, TestCase  # type: ignore
from pydantic import BaseModel, HttpUrl

from prowjobscraper.prowjob import ProwJob, ProwJobs

logger = logging.getLogger(__name__)


class JobStep(BaseModel):
    """
    A JobStep represents a step in a ProwJob.
    """

    job: ProwJob
    name: str
    state: str
    duration: timedelta
    details: Optional[str] = None

    @classmethod
    def create_from_junit_testcase(cls, job: ProwJob, case: TestCase) -> "JobStep":
        state = "success"
        details = None
        for res in case.result:
            if isinstance(res, Failure):
                state = "failure"
                details = res.text
                break

        duration = timedelta(0)
        if case.time:
            duration = timedelta(seconds=float(case.time))
        return cls(
            job=job,
            name=case.name,
            state=state,
            duration=duration,
            details=details,
        )


class StepExtractor:
    """
    StepExtractor allows to parse ProwJobs into JobSteps.
    """

    def __init__(self, client: storage.Client):
        self._client = client

    def parse_prow_jobs(self, jobs: ProwJobs) -> list[JobStep]:
        """
        For each ProwJob in ProwJob, retrieve the resulting junit file stored in Prow's GCS bucket and parse it in order to produce JobSteps.
        TODO: see if returning a generator would be benefic on memory comsumption
        """
        steps = []
        for j in jobs.items:
            steps.extend(self._create_job_steps(j))
        return steps

    def _get_bucket_and_path_to_junit(self, url: HttpUrl) -> tuple[str, str]:
        if url.path is None:
            raise ValueError("url.path is not set")

        http_path = url.path.split("/")
        bucket_name = http_path[3]
        blob_path = url.path.split("/")[4:] + ["artifacts", "junit_operator.xml"]

        return bucket_name, "/".join(blob_path)

    def _download_junit(self, job: ProwJob) -> str:
        if job.status.url is None:
            raise ValueError("job.status.url is not set")

        bucket_name, blob_path = self._get_bucket_and_path_to_junit(job.status.url)
        gcs_bucket = self._client.bucket(bucket_name)
        gcs_blob = gcs_bucket.blob(blob_path)
        return gcs_blob.download_as_string()

    def _parse_junit_suite_into_steps(self, job: ProwJob, junit: str) -> list[JobStep]:
        steps = []
        xml = JUnitXml.fromstring(junit)
        for suite in xml:
            for case in suite:
                steps.append(JobStep.create_from_junit_testcase(job, case))

        return steps

    def _create_job_steps(self, job: ProwJob) -> list[JobStep]:
        try:
            junit = self._download_junit(job)
        except exceptions.ClientError as e:
            logger.info("No junit file found for job: %s %s", job, e)
            return []

        return self._parse_junit_suite_into_steps(job, junit)
