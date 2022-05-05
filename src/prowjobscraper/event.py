import os
from datetime import datetime, timedelta
from typing import Any, Iterator

from elasticsearch import Elasticsearch, helpers
from pydantic import BaseModel

from prowjobscraper.prowjob import ProwJob
from prowjobscraper.step import JobStep


class JobDetails(BaseModel):
    build_id: str
    duration: int
    name: str
    start_time: datetime
    state: str
    type: str


class JobEvent(BaseModel):
    job: JobDetails

    @classmethod
    def create_from_prowjob(cls, job: ProwJob):
        job_duration = timedelta(seconds=0)
        if job.status.completionTime and job.status.startTime:
            job_duration = job.status.completionTime - job.status.startTime

        return cls(
            job=JobDetails(
                build_id=job.status.build_id,
                duration=job_duration.seconds,
                name=job.spec.job,
                start_time=job.status.startTime,
                state=job.status.state,
                type=job.spec.type,
            )
        )


class StepDetails(BaseModel):
    duration: int
    name: str
    state: str


class StepEvent(BaseModel):
    job: JobDetails
    step: StepDetails

    @classmethod
    def create_from_job_step(cls, step: JobStep):
        return cls(
            job=JobEvent.create_from_prowjob(step.job).job,
            step=StepDetails(
                duration=step.duration.seconds,
                name=step.name,
                state=step.state,
            ),
        )


class EventStoreElastic:
    def __init__(self):
        self._client = Elasticsearch(
            os.environ["ES_URL"],
            http_auth=(os.environ["ES_USER"], os.environ["ES_PASSWORD"]),
            verify_certs=False,
            ssl_show_warn=False,
        )

        # Let's create one index per week
        now = datetime.now()
        self._step_index = "{}-{}".format(
            os.environ["ES_STEP_INDEX"], now.strftime("%Y.%W")
        )
        self._job_index = "{}-{}".format(
            os.environ["ES_JOB_INDEX"], now.strftime("%Y.%W")
        )

        a_week_ago = now - timedelta(weeks=1)
        self._previous_job_index = "{}-{}".format(
            os.environ["ES_JOB_INDEX"], a_week_ago.strftime("%Y.%W")
        )

        print(self._client.info())

    def _gen_documents(
        self, index: str, data: Iterator[dict[str, Any]]
    ) -> Iterator[dict[str, Any]]:
        for d in data:
            yield {
                "_index": index,
                **d,
            }

    def index_job_steps(self, steps: list[JobStep]):
        if not self._client.indices.exists(index=self._step_index):
            self._client.indices.create(
                index=self._step_index,  # body=self._step_schema
            )

        step_events = (StepEvent.create_from_job_step(s).dict() for s in steps)
        helpers.bulk(
            self._client, self._gen_documents(index=self._step_index, data=step_events)
        )

        self._client.indices.refresh(index=self._step_index)

    def index_prowjobs(self, jobs: list[ProwJob]):
        if not self._client.indices.exists(index=self._job_index):
            self._client.indices.create(
                index=self._job_index,  # body=self._job_schema
            )

        job_events = (JobEvent.create_from_prowjob(j).dict() for j in jobs)
        helpers.bulk(
            self._client, self._gen_documents(index=self._job_index, data=job_events)
        )

        self._client.indices.refresh(index=self._job_index)

    def scan_build_ids(self) -> set[int]:
        results = helpers.scan(
            self._client,
            index=f"{self._job_index},{self._previous_job_index}",
            ignore_unavailable=True,
            query={"_source": False, "fields": ["job.build_id"]},
        )
        return {int(build_id) for r in results for build_id in r["fields"]["job.build_id"]}
