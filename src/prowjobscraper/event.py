import os
from datetime import datetime
from os import environ

from elasticsearch import Elasticsearch
from pydantic import BaseModel
from step import JobStep


class Event(BaseModel):
    build_id: str
    job_duration: int
    job_name: str
    job_start_time: datetime
    job_state: str
    job_type: str
    step_duration: int
    step_name: str
    step_state: str


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
        self._index = "{}-{}".format(os.environ["ES_INDEX"], now.strftime("%Y.%W"))
        print(self._client.info())

    def push(self, step: JobStep) -> None:
        event = self.event_from_step(step)
        print(f"Push event {event}...")
        self._client.index(index=self._index, document=event.dict())

    def refresh(self):
        self._client.indices.refresh(index=self._index)

    @staticmethod
    def event_from_step(step: JobStep) -> Event:
        job_duration = step.job.status.completionTime - step.job.status.startTime
        return Event(
            build_id=step.job.status.build_id,
            job_duration=job_duration.seconds,
            job_name=step.job.spec.job,
            job_start_time=step.job.status.startTime,
            job_state=step.job.status.state,
            job_type=step.job.spec.type,
            step_duration=step.duration.seconds,
            step_name=step.name,
            step_state=step.state,
        )
