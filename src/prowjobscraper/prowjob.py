import re
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
    build_id: Optional[int] = None
    description: Optional[str] = None


class ProwJob(BaseModel):
    spec: ProwJobSpec
    status: ProwJobStatus


class ProwJobs(BaseModel):
    items: list[ProwJob]


def is_assisted_job(j: ProwJob) -> bool:
    if j.status.state not in ("success", "failure"):
        return False
    elif not re.search("e2e-.*-assisted", j.spec.job):
        return False
    elif j.status.description and "Overridden" in j.status.description:
        # exclude overrriden builds
        # the url points to github instead of prow
        return False

    return True


def prowjobs_from_url(url: str) -> ProwJobs:
    r = requests.get(url)
    return prowjobs_from_string(r.text)


def prowjobs_from_string(data: str) -> ProwJobs:
    jobs = ProwJobs.parse_raw(data)
    jobs.items[:] = [j for j in jobs.items if is_assisted_job(j)]
    return jobs
