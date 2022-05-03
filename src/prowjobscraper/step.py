from datetime import timedelta

from google.cloud import exceptions, storage
from junitparser import Failure, JUnitXml
from prowjob import ProwJob
from pydantic import BaseModel, HttpUrl, NoneStr


class JobStep(BaseModel):
    job: ProwJob
    name: str
    state: str
    duration: timedelta
    details: str = None


def get_bucket_and_path_to_junit(url: HttpUrl) -> tuple[str, str]:
    http_path = url.path.split("/")
    bucket_name = http_path[3]
    blob_path = url.path.split("/")[4:] + ["artifacts", "junit_operator.xml"]

    return bucket_name, "/".join(blob_path)


def download_junit(job: ProwJob) -> str:
    bucket_name, blob_path = get_bucket_and_path_to_junit(job.status.url)

    storage_client = storage.Client.create_anonymous_client()
    gcs_bucket = storage_client.bucket(bucket_name)
    gcs_blob = gcs_bucket.blob(blob_path)
    return gcs_blob.download_as_string()


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
