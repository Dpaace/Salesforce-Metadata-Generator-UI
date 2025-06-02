import json
import pytest
from unittest.mock import patch
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

@patch("app.requests.post")
def test_deploy_to_salesforce_success(mock_post, client):
    logger.info("Starting test: /deploy-to-salesforce route")

    payload = {
        "access_token": "dummy_token",
        "instance_url": "https://dummy.salesforce.com",
        "zip_file": "UEsDBBQAAAAI"  # Dummy base64-encoded ZIP string prefix
    }

    # Fake SOAP response
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "<deployResult><status>Success</status></deployResult>"

    response = client.post("/deploy-to-salesforce", data=json.dumps(payload), content_type="application/json")

    # Check response
    assert response.status_code == 200
    assert "<deployResult>" in response.text
    logger.info("Response status and body confirmed")

    # Verify that correct URL and headers were used
    expected_url = "https://dummy.salesforce.com/services/Soap/m/63.0"
    expected_headers = {
        "Content-Type": "text/xml",
        "SOAPAction": "deploy"
    }

    mock_post.assert_called_once()
    called_url = mock_post.call_args[0][0]
    called_headers = mock_post.call_args[1]["headers"]
    called_data = mock_post.call_args[1]["data"]

    assert called_url == expected_url
    assert called_headers == expected_headers
    assert "<ZipFile>UEsDBBQAAAAI" in called_data
    assert "<rollbackOnError>true</rollbackOnError>" in called_data
    logger.info("SOAP request format and endpoint verified")

    logger.info("Test completed successfully.")
