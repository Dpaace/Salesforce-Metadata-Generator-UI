import json
import pytest
from unittest.mock import patch
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

@patch("app.requests.post")
def test_exchange_token_success(mock_post, client):
    logger.info("Starting test: /exchange-token route")

    # Payload we'll send to the route
    payload = {
        "client_id": "dummy_client_id",
        "redirect_uri": "http://localhost:5000/redirect.html",
        "code": "dummy_auth_code"
    }

    # Mock Salesforce's token response
    mocked_salesforce_response = {
        "access_token": "dummy_access_token",
        "instance_url": "https://dummy.salesforce.com",
        "id": "https://login.salesforce.com/id/00Dxx0000001gEREAY/005xx000001Sv6UABC",
        "token_type": "Bearer",
        "issued_at": "1627688517123",
        "signature": "dummy_signature"
    }

    # Configure the mock
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mocked_salesforce_response

    # Make the actual request to our Flask app
    response = client.post("/exchange-token", data=json.dumps(payload), content_type="application/json")

    # Assertions
    assert response.status_code == 200
    logger.info("Status code 200 confirmed")

    response_data = response.get_json()
    assert response_data["access_token"] == "dummy_access_token"
    assert response_data["instance_url"] == "https://dummy.salesforce.com"
    logger.info("Response data verified")

    # Ensure the payload was passed correctly to requests.post
    expected_payload = {
        "grant_type": "authorization_code",
        "client_id": "dummy_client_id",
        "redirect_uri": "http://localhost:5000/redirect.html",
        "code": "dummy_auth_code"
    }

    mock_post.assert_called_once_with(
        "https://login.salesforce.com/services/oauth2/token",
        data=expected_payload
    )
    logger.info("Payload sent to Salesforce verified")

    logger.info("Test completed successfully.")
