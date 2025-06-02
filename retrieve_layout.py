import requests
import time
import base64
import zipfile
import io
import xml.etree.ElementTree as ET

# -----------------------------------------
# STEP 1: Start the retrieve request
# -----------------------------------------
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

# -----------------------------------------
# STEP 2: Poll until the ZIP is ready
# -----------------------------------------
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

# -----------------------------------------
# STEP 3: Extract layout XML from ZIP in memory
# -----------------------------------------
def extract_layout_from_response(xml_response, target_file_keyword='Layout'):
    tree = ET.ElementTree(ET.fromstring(xml_response))
    namespace = {
        'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
        'm': 'http://soap.sforce.com/2006/04/metadata'
    }

    result = tree.find('.//m:result', namespace)

    # Detect failed status
    status = result.find('m:status', namespace)
    if status is not None and status.text == 'Failed':
        error_msg = result.find('m:messages/m:problem', namespace)
        if error_msg is not None:
            raise Exception(f"Metadata retrieve failed: {error_msg.text}")
        else:
            raise Exception("Metadata retrieve failed with unknown error.")

    done = result.find('m:done', namespace).text.lower() == 'true'
    if not done:
        return None  # not ready yet

    zip_base64 = result.find('m:zipFile', namespace).text
    zip_data = base64.b64decode(zip_base64)

    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
        for file_name in zip_file.namelist():
            if target_file_keyword in file_name and file_name.endswith('.layout'):
                print(f"[+] Found: {file_name}")
                with zip_file.open(file_name) as f:
                    return f.read().decode('utf-8')

    raise Exception(" Layout XML not found in the retrieved ZIP.")

# -----------------------------------------
# MERGE
# -----------------------------------------
def generate_layout_xml(object_api_name, fields, existing_layout_xml=None):
    import xml.etree.ElementTree as ET
    

    new_field_names = set()
    for field in fields:
        name = field.get('apiName') or field.get('label', '').replace(' ', '_') + '__c'
        new_field_names.add(name)

    all_fields = set(new_field_names)
    all_fields.add("Name")  # Always required

    if existing_layout_xml:
        ns = {'ns': 'http://soap.sforce.com/2006/04/metadata'}
        root = ET.fromstring(existing_layout_xml)
        for item in root.findall(".//ns:layoutItems", ns):
            field_elem = item.find("ns:field", ns)  # <-- fixed here!
            if field_elem is not None and field_elem.text:
                all_fields.add(field_elem.text.strip())

    layout_items = ""
    for field_name in sorted(all_fields):
        if field_name == "Name":
            layout_items += f"""
            <layoutItems>
                <behavior>Required</behavior>
                <field>{field_name}</field>
            </layoutItems>"""
        else:
            layout_items += f"""
            <layoutItems>
                <behavior>Edit</behavior>
                <field>{field_name}</field>
            </layoutItems>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
    <layoutSections>
        <customLabel>false</customLabel>
        <detailHeading>true</detailHeading>
        <editHeading>true</editHeading>
        <label>Information</label>
        <layoutColumns>
            {layout_items}
        </layoutColumns>
        <style>TwoColumnsTopToBottom</style>
    </layoutSections>
</Layout>"""




# -----------------------------------------
# MAIN EXECUTION
# -----------------------------------------
# if __name__ == "__main__":
#     access_token = '00DdM00000B48zI!AQEAQFwJnM6PGhTQs_fTdeswxdcfZTnszDe6GBb4Fn8LzXgdh6oaWMpLpo_1w5K4.Db9f6oX3ZeYYXqTxSk3B.vMqTo9VT1b'
#     instance_url = 'https://ssadminlearn123-dev-ed.develop.my.salesforce.com'
#     layout_full_name = 'Account-Account Layout'  # e.g., 'Custom_Object__c-Custom_Object Layout'
#     # layout_full_name = 'Mass_Upload__c-Mass Upload Layout'
#     # layout_full_name = 'Case-Case Layout'
    
#     print("[*] Starting layout retrieval...")
#     try:
#         retrieve_id = retrieve_layout_metadata(access_token, instance_url, layout_full_name)
#         print(f"[+] Retrieve request ID: {retrieve_id}")
#     except Exception as e:
#         print(f"Failed to start retrieve: {str(e)}")
#         exit(1)

#     # Polling loop
#     MAX_ATTEMPTS = 10
#     WAIT_SECONDS = 3

#     for attempt in range(MAX_ATTEMPTS):
#         print(f"Polling attempt {attempt + 1}...")
#         try:
#             status_response = check_retrieve_status(access_token, instance_url, retrieve_id)
#             layout_xml = extract_layout_from_response(status_response)
#             if layout_xml:
#                 print("Layout XML retrieved successfully.")
#                 print(layout_xml[:1000])  # preview first 1000 chars
#                 break
#         except Exception as e:
#             print(str(e))
#             break

#         print(f"Not ready yet. Sleeping {WAIT_SECONDS} seconds...\n")
#         time.sleep(WAIT_SECONDS)
#     else:
#         print("Retrieval timed out after multiple attempts.")
        
#     # Define new fields you want to add
#     new_fields = [
#         {'apiName': 'Today__c'}
#     ]

#     if layout_xml:
#         print("[*] Merging new fields into layout...")
#         final_xml = generate_layout_xml("Account", new_fields, existing_layout_xml=layout_xml)
#     else:
#         print("[*] No existing layout found. Generating new layout XML...")
#         final_xml = generate_layout_xml("Account", new_fields, existing_layout_xml=None)

#     # Save the merged layout XML to a file
#     output_file = f"{layout_full_name}.layout-meta.xml"
#     with open(output_file, "w", encoding="utf-8") as f:
#         f.write(final_xml)

#     print(f"\nFinal layout XML written to: {output_file}")





