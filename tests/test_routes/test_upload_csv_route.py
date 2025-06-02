import json
import pytest
from unittest.mock import patch
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

@patch("app.requests.post")
def test_upload_csv_success(mock_post, client):
    logger.info("Starting test: /upload-csv route")

    payload = {
        "access_token": "dummy_token",
        "instance_url": "https://dummy.salesforce.com",
        "object_name": "Account",
        "records": [
            {"attributes": {"type": "Account"}, "Name": "Test Account 1"},
            {"attributes": {"type": "Account"}, "Name": "Test Account 2"}
        ]
    }

    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"hasErrors": False}

    response = client.post("/upload-csv", data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    assert response.data.decode("utf-8") == "Success"
    logger.info("Response status and content verified")

    expected_url = "https://dummy.salesforce.com/services/data/v63.0/composite/tree/Account/"
    expected_headers = {
        "Authorization": "Bearer dummy_token",
        "Content-Type": "application/json"
    }

    mock_post.assert_called_once()
    assert mock_post.call_args[0][0] == expected_url
    assert mock_post.call_args[1]["headers"] == expected_headers
    assert mock_post.call_args[1]["json"] == {"records": payload["records"]}

    logger.info("Salesforce request verified")
    logger.info("Test completed successfully")
