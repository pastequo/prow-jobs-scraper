from datetime import datetime

import requests
from pydantic import BaseModel, HttpUrl


class ProwJobSpec(BaseModel):
    job: str
    type: str


class ProwJobStatus(BaseModel):
    state: str = None
    url: HttpUrl = None
    startTime: datetime = None
    pendingTime: datetime = None
    completionTime: datetime = None
    build_id: int = None


class ProwJob(BaseModel):
    spec: ProwJobSpec
    status: ProwJobStatus


class ProwJobs(BaseModel):
    items: list[ProwJob]


def retrieve_prowjobs(url: str) -> ProwJobs:
    r = requests.get(url)
    return create_prowjobs(r.text)


def create_prowjobs(data: str) -> ProwJobs:
    return ProwJobs.parse_raw(data)
