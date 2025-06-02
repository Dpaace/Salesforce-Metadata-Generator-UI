import json
import io
import zipfile
import os
import pytest
from unittest.mock import patch
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

@patch("app.create_standard_metadata_folder")
def test_generate_standard_zip_success(mock_create_standard_metadata_folder, client):
    logger.info("Starting test: /generate-standard-zip route")

    payload = {
        "objects": [
            {
                "objectName": "Account",
                "fields": [
                    {"apiName": "Region__c", "label": "Region", "type": "Picklist"}
                ]
            }
        ],
        "access_token": "dummy_token",
        "instance_url": "https://dummy.salesforce.com"
    }

    def fake_standard_metadata_folder(base_folder, objects, access_token, instance_url):
        logger.info(f"Simulating standard metadata folder creation: {base_folder}")
        os.makedirs(base_folder, exist_ok=True)
        with open(os.path.join(base_folder, "standard_dummy.txt"), "w") as f:
            f.write("standard test content")
        logger.info("Dummy file created")

    mock_create_standard_metadata_folder.side_effect = fake_standard_metadata_folder

    response = client.post("/generate-standard-zip", data=json.dumps(payload), content_type="application/json")
    logger.info("POST /generate-standard-zip sent")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"

    zip_bytes = io.BytesIO(response.data)
    with zipfile.ZipFile(zip_bytes, 'r') as zip_file:
        file_list = zip_file.namelist()
        logger.info(f"Files in returned ZIP: {file_list}")
        assert "standard_dummy.txt" in file_list
        assert len(file_list) >= 1
        logger.info("ZIP contains standard_dummy.txt")

    logger.info("Test completed successfully.")
