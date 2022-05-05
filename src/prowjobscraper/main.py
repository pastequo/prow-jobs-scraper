import os
import sys

from prowjobscraper import event, prowjob, step


def main() -> None:
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            jobs = prowjob.prowjobs_from_string(f.read())
    else:
        jobs = prowjob.prowjobs_from_url(os.environ["JOB_LIST_URL"])

    event_store = event.EventStoreElastic()
    known_build_ids = event_store.scan_build_ids()

    # filter out jobs already in ES
    jobs.items[:] = [j for j in jobs.items if j.status.build_id not in known_build_ids]
    print(f"{len(jobs.items)} jobs will be processed")

    steps = []
    for j in jobs.items:
        steps.extend(step.create_job_steps(j))

    print(f"{len(jobs.items)} jobs will be pushed to ES")
    event_store.index_prowjobs(jobs.items)
    print(f"{len(steps)} steps will be pushed to ES")
    event_store.index_job_steps(steps)


if __name__ == "__main__":
    main()
