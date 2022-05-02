import re
import sys

import config
import prowjob
import step
import event
from google.cloud import storage


def main() -> None:
    event_store = event.EventStoreElastic()

    # 1 - Get jobs
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            jobs = prowjob.create_prowjobs(f.read())
    else:
        jobs = prowjob.retrieve_prowjobs(config.JOB_LIST_URL)

    print(f"* {len(jobs.items)}")
    # 2 - Filter jobs on:
    # - .items[].status.state == failure or success
    # - .items[].spec.job | grep -E "e2e-.*-assisted"
    jobs.items[:] = [j for j in jobs.items if j.status.state in ("success", "failure")]
    jobs.items[:] = [j for j in jobs.items if re.search("e2e-.*-assisted", j.spec.job)]

    print(f"** {len(jobs.items)}")

    # 3 - From jq .items[].status.url
    #     Build GCS URI
    #     https://prow.ci.openshift.org/view/gs/origin-ci-test/logs/periodic-ci-shiftstack-shiftstack-ci-main-monitor-mecha-az0/1519676767458037760
    # Becomes
    #     gs://origin-ci-test/logs/periodic-ci-shiftstack-shiftstack-ci-main-monitor-mecha-az0/1519676767458037760

    # 4 - Download JUnit report
    #     Append "artifacts/junit_operator.xml" to the GCS URI

    steps = []
    for j in jobs.items:
        steps.extend(step.create_job_steps(j))

    print(f"*** {len(steps)}")

    # 5 - Parse the JUnit test and push data to ES
    #     - push job details in job index (job_name, build_id, job_duration, job_state)
    #     - push job details + step details in step index (job_name, build_id, job_duration, job_state, step_name, step_duration, step_state)

    for s in steps:
        event_store.push(s)

    event_store.refresh()


if __name__ == "__main__":
    main()
