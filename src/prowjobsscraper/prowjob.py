from datetime import datetime
from typing import Optional

import requests
from pydantic import BaseModel, HttpUrl


class ProwJobSpec(BaseModel):
    job: str
    type: str


class ProwJobStatus(BaseModel):
    state: Optional[str] = None
    url: Optional[HttpUrl] = None
    startTime: Optional[datetime] = None
    pendingTime: Optional[datetime] = None
    completionTime: Optional[datetime] = None
    build_id: Optional[str] = None
    description: Optional[str] = None


class ProwJob(BaseModel):
    spec: ProwJobSpec
    status: ProwJobStatus


class ProwJobs(BaseModel):
    """
    ProwJobs represents the data structure returned by Prow's API
    (e.g.: https://prow.ci.openshift.org/prowjobs.js?omit=annotations,labels,decoration_config,pod_spec)
    """

    items: list[ProwJob]

    @classmethod
    def create_from_url(cls, url: str) -> "ProwJobs":
        r = requests.get(url)
        return cls.create_from_string(r.text)

    @classmethod
    def create_from_string(cls, data) -> "ProwJobs":
        jobs = cls.parse_raw(data)
        return jobs
