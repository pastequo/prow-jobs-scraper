import os
import re
import sys

import event
import prowjob
import step
from google.cloud import storage


def main() -> None:

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            jobs = prowjob.prowjobs_from_string(f.read())
    else:
        jobs = prowjob.prowjobs_from_url(os.environ["JOB_LIST_URL"])

    steps = []
    for j in jobs.items:
        steps.extend(step.create_job_steps(j))

    event_store = event.EventStoreElastic()
    for s in steps:
        event_store.push(s)

    event_store.refresh()


if __name__ == "__main__":
    main()
