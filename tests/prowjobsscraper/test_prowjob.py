import json
from typing import Final

import pkg_resources
import pytest
from pydantic import ValidationError
from pytest_httpserver import HTTPServer

from prowjobsscraper import prowjob

INVALID_RESPONSE_FROM_PROW: Final[
    str
] = """
{"invalid": "value"}
"""


def test_invalid_json_from_prow_should_throw_an_exception(httpserver: HTTPServer):
    httpserver.expect_request("/jobs").respond_with_json(INVALID_RESPONSE_FROM_PROW)
    with pytest.raises(ValidationError):
        prowjob.ProwJobs.create_from_url(httpserver.url_for("/jobs"))


def test_valid_json_from_prow_should_be_successfully_parsed(httpserver: HTTPServer):
    response = pkg_resources.resource_string(
        __name__, f"prowjob_assets/valid_prow_response.json"
    )
    expected = json.loads(
        pkg_resources.resource_string(
            __name__, f"prowjob_assets/expected_prowjobs.json"
        )
    )
    httpserver.expect_request("/jobs").respond_with_data(response)
    jobs = prowjob.ProwJobs.create_from_url(httpserver.url_for("/jobs"))
    assert jobs.json() == json.dumps(expected)
