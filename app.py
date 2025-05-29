from flask import Flask, request, send_file, render_template_string
import os
import shutil
from utils.generate_metadata import create_metadata_folder
from utils.standard_generator import create_standard_metadata_folder
import zipfile
import uuid
from flask import request, jsonify
import requests

from retrieve_standard_layout import (
    retrieve_layout_metadata,
    check_retrieve_status,
    extract_layout_from_response,
)
import time

PORT = 5000
REDIRECT_URI = f"http://localhost:{PORT}/redirect.html"
app = Flask(__name__)


@app.route("/generate", methods=["POST"])
def generate_metadata():
    # objects = request.get_json()
    # session_id = str(uuid.uuid4())
    # base_folder = f'metadata/{session_id}'
    # os.makedirs(base_folder, exist_ok=True)
    # create_metadata_folder(base_folder, objects)

    payload = request.get_json()
    objects = payload.get("objects")
    access_token = payload.get("access_token")
    instance_url = payload.get("instance_url")

    session_id = str(uuid.uuid4())
    base_folder = f"metadata/{session_id}"
    os.makedirs(base_folder, exist_ok=True)

    # Pass tokens to create_metadata_folder
    create_metadata_folder(base_folder, objects, access_token, instance_url)

    zip_path = f"{base_folder}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_folder):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, base_folder)
                zipf.write(filepath, arcname)

    shutil.rmtree(base_folder)

    return send_file(zip_path, as_attachment=True)


@app.route("/generate-standard-zip", methods=["POST"])
def generate_standard_zip():
    data = request.get_json()
    objects = data.get("objects")
    access_token = data.get("access_token")
    instance_url = data.get("instance_url")

    if not all([objects, access_token, instance_url]):
        return jsonify({"error": "Missing required fields"}), 400

    session_id = str(uuid.uuid4())
    base_folder = f"standardmetadata/{session_id}"
    os.makedirs(base_folder, exist_ok=True)

    try:
        create_standard_metadata_folder(
            base_folder, objects, access_token, instance_url
        )
    except Exception as e:
        return jsonify({"error": f"Metadata generation failed: {str(e)}"}), 500

    zip_path = f"standardmetadata_{session_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_folder):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, base_folder)
                zipf.write(filepath, arcname)

    return send_file(zip_path, as_attachment=True)


@app.route("/")
def oauth():
    with open("templates/oauth.html") as f:
        html = f.read()
    # Inject the redirect_uri directly into the template
    return render_template_string(html, redirect_uri=REDIRECT_URI)


@app.route("/redirect.html")
def oauth_redirect():
    return open("templates/redirect.html").read()


@app.route("/select")
def select():
    return open("templates/select.html").read()


@app.route("/custom")
def index():
    return open("templates/custom.html").read()


@app.route("/standard")
def standard():
    return open("templates/standard.html").read()


@app.route("/success")
def deploy_success():
    return "<h1 style='text-align:center;margin-top:100px;'>🎉 Congrats! Now you can register data.</h1>"


@app.route("/deploying")
def deploying_screen():
    return open("templates/deploying.html").read()


@app.route("/upload")
def upload_page():
    return open("templates/upload.html").read()


@app.route("/upload-csv", methods=["POST"])
def upload_csv_batch():
    data = request.get_json()
    access_token = data.get("access_token")
    instance_url = data.get("instance_url")
    object_name = data.get("object_name")
    records = data.get("records", [])

    if not all([access_token, instance_url, object_name, records]):
        return "Missing data", 400

    url = f"{instance_url}/services/data/v63.0/composite/tree/{object_name}/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json={"records": records})

    if response.status_code in [200, 201] and not response.json().get("hasErrors"):
        return "Success"
    else:
        return response.text, 500


@app.route("/exchange-token", methods=["POST"])
def exchange_token():
    data = request.json
    client_id = data.get("client_id")
    redirect_uri = data.get("redirect_uri")
    code = data.get("code")
    client_secret = ""  # Optional: fill if your app requires it

    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code": code,
    }

    if client_secret:
        payload["client_secret"] = client_secret

    response = requests.post(
        "https://login.salesforce.com/services/oauth2/token", data=payload
    )

    return jsonify(response.json())


@app.route("/deploy-to-salesforce", methods=["POST"])
def deploy_to_salesforce():
    data = request.json
    access_token = data.get("access_token")
    instance_url = data.get("instance_url")
    zip_file = data.get("zip_file")

    if not all([access_token, instance_url, zip_file]):
        return jsonify({"error": "Missing required fields"}), 400

    soap_envelope = f"""
    <env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
      <env:Header>
        <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
          <sessionId>{access_token}</sessionId>
        </SessionHeader>
      </env:Header>
      <env:Body>
        <deploy xmlns="http://soap.sforce.com/2006/04/metadata">
          <ZipFile>{zip_file}</ZipFile>
          <DeployOptions>
            <performRetrieve>false</performRetrieve>
            <rollbackOnError>true</rollbackOnError>
            <singlePackage>true</singlePackage>
          </DeployOptions>
        </deploy>
      </env:Body>
    </env:Envelope>
    """.strip()

    try:
        soap_url = f"{instance_url}/services/Soap/m/63.0"
        headers = {"Content-Type": "text/xml", "SOAPAction": "deploy"}

        response = requests.post(soap_url, headers=headers, data=soap_envelope)
        return response.text, response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/check-deploy-status", methods=["POST"])
def check_deploy_status():
    data = request.json
    access_token = data.get("access_token")
    instance_url = data.get("instance_url")
    deploy_id = data.get("deploy_id")

    if not all([access_token, instance_url, deploy_id]):
        return jsonify({"error": "Missing required fields"}), 400

    soap_envelope = f"""
    <env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
      <env:Header>
        <SessionHeader xmlns="http://soap.sforce.com/2006/04/metadata">
          <sessionId>{access_token}</sessionId>
        </SessionHeader>
      </env:Header>
      <env:Body>
        <checkDeployStatus xmlns="http://soap.sforce.com/2006/04/metadata">
          <id>{deploy_id}</id>
          <includeDetails>true</includeDetails>
        </checkDeployStatus>
      </env:Body>
    </env:Envelope>
    """.strip()

    headers = {"Content-Type": "text/xml", "SOAPAction": "checkDeployStatus"}

    try:
        response = requests.post(
            f"{instance_url}/services/Soap/m/63.0", headers=headers, data=soap_envelope
        )
        return response.text, response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def merge_fields_into_layout(layout_xml: str, field_api_names: list[str]) -> str:
    import xml.etree.ElementTree as ET

    ns = {"ns": "http://soap.sforce.com/2006/04/metadata"}
    ET.register_namespace("", ns["ns"])  # Register default namespace

    root = ET.fromstring(layout_xml)

    # Create one new section with all fields
    section = ET.Element("layoutSections")
    ET.SubElement(section, "customLabel").text = "true"
    ET.SubElement(section, "detailHeading").text = "true"
    ET.SubElement(section, "editHeading").text = "true"
    ET.SubElement(section, "label").text = "Custom Fields"

    column1 = ET.SubElement(section, "layoutColumns")
    column2 = ET.SubElement(section, "layoutColumns")  # Empty second column

    for api_name in field_api_names:
        layout_item = ET.Element("layoutItems")
        ET.SubElement(layout_item, "behavior").text = "Edit"
        ET.SubElement(layout_item, "field").text = api_name
        column1.append(layout_item)

    ET.SubElement(section, "style").text = "TwoColumnsTopToBottom"

    # Find last layoutSections and insert after
    layout_sections = root.findall("ns:layoutSections", ns)
    if layout_sections:
        last_section = layout_sections[-1]
        parent = root
        index = list(parent).index(last_section)
        parent.insert(index + 1, section)
    else:
        root.append(section)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        root, encoding="unicode"
    )


# def generate_object_file(object_name: str, field_api_name: str, label: str) -> str:
#     return f"""<?xml version="1.0" encoding="UTF-8"?>
# <CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
#     <fields>
#         <fullName>{field_api_name}</fullName>
#         <externalId>false</externalId>
#         <label>{label}</label>
#         <required>false</required>
#         <trackHistory>false</trackHistory>
#         <trackTrending>false</trackTrending>
#         <type>Text</type>
#         <length>255</length>
#     </fields>
#     <deploymentStatus>Deployed</deploymentStatus>
#     <sharingModel>ReadWrite</sharingModel>
# </CustomObject>"""


def generate_object_file(object_name: str, fields: list[dict]) -> str:
    def build_field_block(field: dict) -> str:
        base = f"""    <fields>
        <fullName>{field['apiName']}</fullName>
        <externalId>false</externalId>
        <label>{field['label']}</label>
        <required>{str(field.get('required', False)).lower()}</required>
        <trackHistory>false</trackHistory>
        <trackTrending>false</trackTrending>"""

        field_type = field.get("type", "Text")

        if field_type == "Text":
            base += f"""
        <type>Text</type>
        <length>255</length>"""
        elif field_type == "Number":
            base += f"""
        <type>Number</type>
        <precision>18</precision>
        <scale>2</scale>"""
        elif field_type == "Date":
            base += f"""
        <type>Date</type>"""
        elif field_type == "Checkbox":
            base += f"""
        <type>Checkbox</type>
        <defaultValue>false</defaultValue>"""
        elif field_type == "Picklist":
            picklist_vals = field.get("picklistValues", "")
            picklist_items = []

            # Support both string and list inputs
            if isinstance(picklist_vals, str):
                picklist_items = [
                    v.strip() for v in picklist_vals.split(",") if v.strip()
                ]
            elif isinstance(picklist_vals, list):
                picklist_items = [
                    v.strip() for v in picklist_vals if isinstance(v, str) and v.strip()
                ]

            picklist_entries = ""
            for val in picklist_items:
                picklist_entries += f"""
                <value>
                    <fullName>{val}</fullName>
                    <default>false</default>
                </value>"""

            base += f"""
                <type>Picklist</type>
                <valueSet>
                    <valueSetDefinition>
                        {picklist_entries}
                    </valueSetDefinition>
                    <restricted>true</restricted>
                </valueSet>"""
        return base

    field_blocks = "\n".join([build_field_block(f) for f in fields])

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
{field_blocks}
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ReadWrite</sharingModel>
</CustomObject>"""


def generate_package_xml(object_name: str, layout_name: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>{object_name}</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>{layout_name}</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Admin</members>
        <name>Profile</name>
    </types>
    <version>63.0</version>
</Package>"""


def generate_profile_xml(
    object_name: str, fields: list[dict], profile_name: str = "Admin"
) -> str:
    permissions = "\n".join(
        [
            f"""    <fieldPermissions>
        <field>{object_name}.{field['apiName']}</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>"""
            for field in fields
        ]
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
{permissions}
</Profile>"""


@app.route("/append-field", methods=["POST"])
def append_field():
    data = request.get_json()
    access_token = "00DdM00000B48zI!AQEAQP29dyQ7qNtx626f6O5IbCVHy9fzLiil2ZDfW.1XJ.tAeQCufoAMMHTIMu6nr9zLptl90lDiV_ObavqqyNQTcf42EDlq"
    instance_url = "https://ssadminlearn123-dev-ed.develop.my.salesforce.com"
    object_name = data["objectName"]
    fields = data["fields"]

    layout_full_name = f"{object_name}-{object_name} Layout"

    try:
        retrieve_id = retrieve_layout_metadata(
            access_token, instance_url, layout_full_name
        )
        for _ in range(10):
            xml_response = check_retrieve_status(
                access_token, instance_url, retrieve_id
            )
            layout_xml = extract_layout_from_response(xml_response)
            if layout_xml:
                break
            time.sleep(2)

        if not layout_xml:
            return jsonify({"error": "Layout not retrieved"}), 500

        # Append all fields to layout
        layout_xml = merge_fields_into_layout(
            layout_xml, [f["apiName"] for f in fields]
        )

        field_blocks = ""

        for f in fields:
            label = f["label"]
            api_name = f["apiName"]
            field_type = f.get("type", "Text")
            required = "true" if f.get("required") else "false"

            # Common field header
            xml = f"""    <fields>
                <fullName>{api_name}</fullName>
                <label>{label}</label>
                <required>{required}</required>
                <trackHistory>false</trackHistory>
                <trackTrending>false</trackTrending>
                <externalId>false</externalId>
            """

            # Field-type-specific attributes
            if field_type == "Text":
                xml += """        <type>Text</type>
                <length>255</length>
            </fields>"""
            elif field_type == "Date":
                xml += """        <type>Date</type>
            </fields>"""
            elif field_type == "Number":
                xml += """        <type>Number</type>
                <precision>18</precision>
                <scale>2</scale>
            </fields>"""
            elif field_type == "Checkbox":
                xml += """        <type>Checkbox</type>
                <defaultValue>false</defaultValue>
            </fields>"""
            elif field_type == "Picklist":
                picklist_values = f.get("picklistValues", [])

                # Ensure it's a list (handle if accidentally passed as comma string)
                if isinstance(picklist_values, str):
                    values = [
                        v.strip() for v in picklist_values.split(",") if v.strip()
                    ]
                elif isinstance(picklist_values, list):
                    values = [
                        v.strip()
                        for v in picklist_values
                        if isinstance(v, str) and v.strip()
                    ]
                else:
                    values = []

                entries = ""
                for val in values:
                    entries += f"""            <value>
                          <fullName>{val}</fullName>
                          <default>false</default>
                          <label>{val}</label>
                      </value>\n"""

                xml += f"""        <type>Picklist</type>
                      <valueSet>
                          <valueSetDefinition>
          {entries.strip()}
                          </valueSetDefinition>
                          <restricted>true</restricted>
                      </valueSet>
                  </fields>"""

            field_blocks += xml + "\n"

        object_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
            {field_blocks}
                <deploymentStatus>Deployed</deploymentStatus>
                <sharingModel>ReadWrite</sharingModel>
            </CustomObject>"""

        profile_xml = generate_profile_xml(object_name, fields)

        package_xml = generate_package_xml(object_name, layout_full_name)

        return jsonify(
            {
                "layoutXml": layout_xml,
                "objectXml": object_xml,
                "profileXml": profile_xml,
                "packageXml": package_xml,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=PORT)
