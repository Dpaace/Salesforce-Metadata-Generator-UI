import json
import io
import zipfile
import os
import pytest
import logging
from unittest.mock import patch

# Set up logger
logger = logging.getLogger(__name__)

@patch("app.create_metadata_folder")
def test_generate_metadata_success(mock_create_metadata_folder, client):
    logger.info("Starting test: /generate route")

    payload = {
        "objects": [
            {
                "objectName": "TestObject__c",
                "fields": [
                    {"apiName": "Test_Field__c", "label": "Test Field", "type": "Text"}
                ]
            }
        ],
        "access_token": "dummy_token",
        "instance_url": "https://dummy.salesforce.com"
    }

    def fake_create_metadata_folder(base_folder, objects, access_token, instance_url):
        logger.info(f"Simulating metadata folder creation: {base_folder}")
        os.makedirs(base_folder, exist_ok=True)
        with open(os.path.join(base_folder, "dummy.txt"), "w") as f:
            f.write("test content")
        logger.info("Dummy file created")

    mock_create_metadata_folder.side_effect = fake_create_metadata_folder

    response = client.post("/generate", data=json.dumps(payload), content_type="application/json")
    logger.info("POST /generate sent")

    assert response.status_code == 200
    logger.info("Status code 200 confirmed")

    assert response.headers["Content-Type"] == "application/zip"

    zip_bytes = io.BytesIO(response.data)
    with zipfile.ZipFile(zip_bytes, 'r') as zip_file:
        file_list = zip_file.namelist()
        logger.info(f"Files in returned ZIP: {file_list}")
        assert "dummy.txt" in file_list
        assert len(file_list) >= 1
        logger.info("ZIP contains dummy.txt")

    logger.info(" Test completed successfully.")

