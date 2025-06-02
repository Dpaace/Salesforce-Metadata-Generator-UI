import requests
import time
import base64
import zipfile
import io
import xml.etree.ElementTree as ET
import os

# ----------------------------
# STEP 1: Retrieve request
# ----------------------------
def retrieve_layout_metadata(access_token, instance_url, layout_full_name):
    url = f"{instance_url}/services/Soap/m/63.0"
    headers = {
        "Content-Type": "text/xml",
        "SOAPAction": "retrieve"
    }

    soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:met="http://soap.sforce.com/2006/04/metadata">
      <env:Header>
        <met:SessionHeader>
          <met:sessionId>{access_token}</met:sessionId>
        </met:SessionHeader>
      </env:Header>
      <env:Body>
        <met:retrieve>
          <met:retrieveRequest>
            <met:apiVersion>63.0</met:apiVersion>
            <met:singlePackage>true</met:singlePackage>
            <met:unpackaged>
              <met:types>
                <met:members>{layout_full_name}</met:members>
                <met:name>Layout</met:name>
              </met:types>
            </met:unpackaged>
          </met:retrieveRequest>
        </met:retrieve>
      </env:Body>
    </env:Envelope>"""

    response = requests.post(url, data=soap_body.encode("utf-8"), headers=headers)
    if response.status_code != 200:
        raise Exception(f"Retrieve request failed: {response.status_code}\n{response.text}")

    tree = ET.fromstring(response.text)
    namespace = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                 'sf': 'http://soap.sforce.com/2006/04/metadata'}
    return tree.find('.//sf:id', namespace).text

# ----------------------------
# STEP 2: Poll until ZIP is ready
# ----------------------------
def check_retrieve_status(access_token, instance_url, retrieve_id):
    url = f"{instance_url}/services/Soap/m/63.0"
    headers = {
        "Content-Type": "text/xml",
        "SOAPAction": "checkRetrieveStatus"
    }

    soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:met="http://soap.sforce.com/2006/04/metadata">
      <env:Header>
        <met:SessionHeader>
          <met:sessionId>{access_token}</met:sessionId>
        </met:SessionHeader>
      </env:Header>
      <env:Body>
        <met:checkRetrieveStatus>
          <met:asyncProcessId>{retrieve_id}</met:asyncProcessId>
          <met:includeZip>true</met:includeZip>
        </met:checkRetrieveStatus>
      </env:Body>
    </env:Envelope>"""

    response = requests.post(url, headers=headers, data=soap_body.encode("utf-8"))
    if response.status_code != 200:
        raise Exception(f"Retrieve status check failed: {response.status_code}\n{response.text}")
    return response.text

# ----------------------------
# STEP 3: Extract XML from ZIP
# ----------------------------
def extract_layout_from_response(xml_response, target_file_keyword='Layout'):
    tree = ET.ElementTree(ET.fromstring(xml_response))
    namespace = {
        'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
        'm': 'http://soap.sforce.com/2006/04/metadata'
    }

    result = tree.find('.//m:result', namespace)

    # Handle failure
    status = result.find('m:status', namespace)
    if status is not None and status.text == 'Failed':
        error_msg = result.find('m:messages/m:problem', namespace)
        if error_msg is not None:
            raise Exception(f"Metadata retrieve failed: {error_msg.text}")
        else:
            raise Exception("Metadata retrieve failed with unknown error.")

    done = result.find('m:done', namespace).text.lower() == 'true'
    if not done:
        return None

    zip_base64 = result.find('m:zipFile', namespace).text
    zip_data = base64.b64decode(zip_base64)

    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
        for file_name in zip_file.namelist():
            if target_file_keyword in file_name and file_name.endswith('.layout'):
                print(f"[+] Found: {file_name}")
                with zip_file.open(file_name) as f:
                    return f.read().decode('utf-8')

    raise Exception("Layout XML not found in ZIP.")

# ----------------------------
# EXECUTION
# ----------------------------
# access_token = '00DdM00000B48zI!AQEAQP6GFVeamFnzVkHHyp4Ivcak8Nk8MfOI6ek5eWHb8R1elkKgJA5P4TS3L4Q1qR7JMtTaQ6P6ZDdgismJaY9TJHEVN3aj'  # Replace this
# instance_url = 'https://ssadminlearn123-dev-ed.develop.my.salesforce.com'  # Replace this
# layout_full_name = 'Account-Account Test Layout'  # Layout you want to retrieve

# print("[*] Starting layout retrieval...")
# try:
#     retrieve_id = retrieve_layout_metadata(access_token, instance_url, layout_full_name)
#     print(f"[+] Retrieve ID: {retrieve_id}")
# except Exception as e:
#     raise RuntimeError(f"Retrieve failed: {e}")

# MAX_ATTEMPTS = 10
# WAIT_SECONDS = 3

# for attempt in range(MAX_ATTEMPTS):
#     print(f"Polling attempt {attempt + 1}...")
#     try:
#         status_response = check_retrieve_status(access_token, instance_url, retrieve_id)
#         layout_xml = extract_layout_from_response(status_response)
#         if layout_xml:
#             print("Layout XML retrieved.")
#             break
#     except Exception as e:
#         print(str(e))
#         break
#     time.sleep(WAIT_SECONDS)
# else:
#     raise TimeoutError("Retrieval timed out.")

# # output_file = layout_full_name.replace(" ", "_") + ".layout-meta.xml"
# output_file = layout_full_name + ".layout"
# with open(output_file, "w", encoding="utf-8") as f:
#     f.write(layout_xml)

# print(f"Layout saved to: {output_file}")
# print("\nPreview (first 500 characters):")
# print(layout_xml[:500])
