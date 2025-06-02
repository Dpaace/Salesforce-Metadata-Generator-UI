import pytest
from unittest.mock import patch, Mock
import base64
import zipfile
import io

# -----------------------------
# Test for retrieve_layout_metadata
# -----------------------------
@patch("requests.post")
def test_retrieve_layout_metadata(mock_post):
    from retrieve_standard_layout import retrieve_layout_metadata

    # Mocked XML response
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:sf="http://soap.sforce.com/2006/04/metadata">
        <soapenv:Body>
            <sf:retrieveResponse>
                <sf:result>
                    <sf:id>TEST_ID_123</sf:id>
                </sf:result>
            </sf:retrieveResponse>
        </soapenv:Body>
    </soapenv:Envelope>"""

    mock_post.return_value = Mock(status_code=200, text=xml_response)

    result = retrieve_layout_metadata(
        access_token="dummy_token",
        instance_url="https://dummy.salesforce.com",
        layout_full_name="Account-Layout"
    )

    assert result == "TEST_ID_123"


# -----------------------------
# Test for check_retrieve_status
# -----------------------------
@patch("requests.post")
def test_check_retrieve_status(mock_post):
    from retrieve_standard_layout import check_retrieve_status

    mock_response_text = "<status>Success</status>"
    mock_post.return_value = Mock(status_code=200, text=mock_response_text)

    result = check_retrieve_status(
        access_token="dummy_token",
        instance_url="https://dummy.salesforce.com",
        retrieve_id="ASYNC_ID"
    )

    assert "Success" in result


# -----------------------------
# Test for extract_layout_from_response
# -----------------------------
def test_extract_layout_from_response_valid():
    from retrieve_standard_layout import extract_layout_from_response

    layout_content = "<Layout>This is layout content</Layout>"
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("TestLayout.layout", layout_content)

    b64_zip = base64.b64encode(mem_zip.getvalue()).decode("utf-8")

    mock_response = f"""<?xml version="1.0" encoding="UTF-8"?>
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

    result = extract_layout_from_response(mock_response)
    assert "This is layout content" in result
