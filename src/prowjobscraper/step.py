from datetime import timedelta

from google.cloud import exceptions, storage
from junitparser import Failure, JUnitXml
from prowjob import ProwJob
from pydantic import BaseModel


class JobStep(BaseModel):
    job: ProwJob
    name: str
    state: str
    duration: timedelta
    details: str = None


def download_junit(job: ProwJob) -> str:
    http_path = job.status.url.path.split("/")
    bucket = http_path[3]
    blob_path = job.status.url.path.split("/")[4:] + ["artifacts", "junit_operator.xml"]

    storage_client = storage.Client.create_anonymous_client()
    bucket = storage_client.bucket(bucket)
    blob = bucket.blob("/".join(blob_path))
    return blob.download_as_string()


def parse_junit_suite_into_steps(job: ProwJob, junit: str) -> list[JobStep]:
    steps = []
    xml = JUnitXml.fromstring(junit)
    for suite in xml:
        for case in suite:
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

            steps.append(
                JobStep(
                    job=job,
                    name=case.name,
                    state=state,
                    duration=duration,
                    details=details,
                )
            )

    return steps


def create_job_steps(job: ProwJob) -> list[JobStep]:
    try:
        junit = download_junit(job)
    except exceptions.NotFound as e:
        print(f"No junit file found for job {job.spec.job}: {e}")
        return []

    return parse_junit_suite_into_steps(job, junit)
