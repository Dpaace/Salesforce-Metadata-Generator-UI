import json
import pytest
from unittest.mock import patch
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

@patch("app.requests.post")
def test_check_deploy_status_success(mock_post, client):
    logger.info("Starting test: /check-deploy-status route")

    payload = {
        "access_token": "dummy_token",
        "instance_url": "https://dummy.salesforce.com",
        "deploy_id": "0Afxxxxxxxxxxxx"
    }

    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "<checkDeployStatusResponse><status>InProgress</status></checkDeployStatusResponse>"

    response = client.post("/check-deploy-status", data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    assert "<checkDeployStatusResponse>" in response.text
    logger.info("Response status and body confirmed")

    expected_url = "https://dummy.salesforce.com/services/Soap/m/63.0"
    expected_headers = {
        "Content-Type": "text/xml",
        "SOAPAction": "checkDeployStatus"
    }

    mock_post.assert_called_once()
    called_url = mock_post.call_args[0][0]
    called_headers = mock_post.call_args[1]["headers"]
    called_data = mock_post.call_args[1]["data"]

    assert called_url == expected_url
    assert called_headers == expected_headers
    assert "<id>0Afxxxxxxxxxxxx</id>" in called_data
    assert "<includeDetails>true</includeDetails>" in called_data
    logger.info("SOAP request format and endpoint verified")

    logger.info("Test completed successfully")
