import base64
import zipfile
import io
import requests
from unittest.mock import patch
from retrieve_layout import (
    generate_layout_xml,
    extract_layout_from_response,
    check_retrieve_status,
    retrieve_layout_metadata,
)


def test_generate_layout_xml_no_existing():
    fields = [
        {"label": "Region", "apiName": "Region__c"},
        {"label": "Status", "apiName": "Status__c"},
    ]

    result = generate_layout_xml("Account", fields)

    assert "<layoutItems>" in result
    assert "<field>Region__c</field>" in result
    assert "<field>Status__c</field>" in result
    assert "<field>Name</field>" in result


def test_extract_layout_from_response_valid():
    layout_content = "<Layout>This is layout</Layout>"
    mem_zip = io.BytesIO()
    
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("Account-Test Layout.layout", layout_content)

    b64_zip = base64.b64encode(mem_zip.getvalue()).decode("utf-8")

    mock_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:m="http://soap.sforce.com/2006/04/metadata">
      <soapenv:Body>
        <m:retrieveResponse>
          <m:result>
            <m:done>true</m:done>
            <m:zipFile>{b64_zip}</m:zipFile>
          </m:result>
        </m:retrieveResponse>
      </soapenv:Body>
    </soapenv:Envelope>"""

    output = extract_layout_from_response(mock_xml)
    assert "This is layout" in output



@patch("retrieve_layout.requests.post")
def test_retrieve_layout_metadata_success(mock_post):
    dummy_response = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:sf="http://soap.sforce.com/2006/04/metadata">
      <soapenv:Body>
        <sf:retrieveResponse>
          <sf:result>
            <sf:id>123456789</sf:id>
          </sf:result>
        </sf:retrieveResponse>
      </soapenv:Body>
    </soapenv:Envelope>"""
    
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = dummy_response

    retrieve_id = retrieve_layout_metadata("access_token", "https://dummy.salesforce.com", "Account-Account Layout")
    assert retrieve_id == "123456789"

@patch("retrieve_layout.requests.post")
def test_check_retrieve_status_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "<status>Dummy</status>"

    response = check_retrieve_status("access_token", "https://dummy.salesforce.com", "async_id")
    assert "<status>Dummy</status>" in response
    
    

# pytest tests/test_utils/test_retrieve_layout.py --html=reports/test_retrieve_layout.html
