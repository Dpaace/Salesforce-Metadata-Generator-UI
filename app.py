from flask import Flask, request, send_file, render_template_string
import os
import shutil
from utils.generate_metadata import create_metadata_folder
import zipfile
import uuid
from flask import request, jsonify
import requests

from retrieve_standard_layout import retrieve_layout_metadata, check_retrieve_status, extract_layout_from_response
import time


PORT = 5000
REDIRECT_URI = f'http://localhost:{PORT}/redirect.html'
app = Flask(__name__)


@app.route('/generate', methods=['POST'])
def generate_metadata():
    # objects = request.get_json()

    # session_id = str(uuid.uuid4())
    # base_folder = f'metadata/{session_id}'
    # os.makedirs(base_folder, exist_ok=True)

    # create_metadata_folder(base_folder, objects)
    
    payload = request.get_json()
    objects = payload.get('objects')
    access_token = payload.get('access_token')
    instance_url = payload.get('instance_url')

    session_id = str(uuid.uuid4())
    base_folder = f'metadata/{session_id}'
    os.makedirs(base_folder, exist_ok=True)

    # Pass tokens to create_metadata_folder
    create_metadata_folder(base_folder, objects, access_token, instance_url)

    zip_path = f'{base_folder}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_folder):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, base_folder)
                zipf.write(filepath, arcname)

    shutil.rmtree(base_folder)

    return send_file(zip_path, as_attachment=True)

@app.route('/')
def oauth():
    with open('templates/oauth.html') as f:
        html = f.read()
    # Inject the redirect_uri directly into the template
    return render_template_string(html, redirect_uri=REDIRECT_URI)

@app.route('/redirect.html')
def oauth_redirect():
    return open('templates/redirect.html').read()

@app.route('/index')
def index():
    return open('templates/index.html').read()
  
@app.route('/standard')
def standard():
    return open('templates/standard.html').read()

@app.route('/success')
def deploy_success():
    return "<h1 style='text-align:center;margin-top:100px;'>🎉 Congrats! Now you can register data.</h1>"

@app.route('/deploying')
def deploying_screen():
    return open('templates/deploying.html').read()

@app.route('/exchange-token', methods=['POST'])
def exchange_token():
    data = request.json
    client_id = data.get('client_id')
    redirect_uri = data.get('redirect_uri')
    code = data.get('code')
    client_secret = ''  # Optional: fill if your app requires it

    payload = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': code
    }

    if client_secret:
        payload['client_secret'] = client_secret

    response = requests.post('https://login.salesforce.com/services/oauth2/token', data=payload)

    return jsonify(response.json())




@app.route('/deploy-to-salesforce', methods=['POST'])
def deploy_to_salesforce():
    data = request.json
    access_token = data.get('access_token')
    instance_url = data.get('instance_url')
    zip_file = data.get('zip_file')

    if not all([access_token, instance_url, zip_file]):
        return jsonify({'error': 'Missing required fields'}), 400

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
        headers = {
            "Content-Type": "text/xml",
            "SOAPAction": "deploy"
        }

        response = requests.post(soap_url, headers=headers, data=soap_envelope)
        return response.text, response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-deploy-status', methods=['POST'])
def check_deploy_status():
    data = request.json
    access_token = data.get('access_token')
    instance_url = data.get('instance_url')
    deploy_id = data.get('deploy_id')

    if not all([access_token, instance_url, deploy_id]):
        return jsonify({'error': 'Missing required fields'}), 400

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

    headers = {
        "Content-Type": "text/xml",
        "SOAPAction": "checkDeployStatus"
    }

    try:
        response = requests.post(f"{instance_url}/services/Soap/m/63.0", headers=headers, data=soap_envelope)
        return response.text, response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
      
def append_field_to_layout(layout_xml: str, field_api_name: str) -> str:
    new_section = f"""
    <layoutSections>
        <customLabel>true</customLabel>
        <detailHeading>true</detailHeading>
        <editHeading>true</editHeading>
        <label>Custom Fields</label>
        <layoutColumns>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>{field_api_name}</field>
            </layoutItems>
        </layoutColumns>
        <layoutColumns/>
        <style>TwoColumnsTopToBottom</style>
    </layoutSections>"""
    
    idx = layout_xml.rfind("</layoutSections>")
    if idx == -1:
        raise ValueError("No layoutSections found")
    
    return layout_xml[:idx + len("</layoutSections>")] + new_section + layout_xml[idx + len("</layoutSections>"):]
  
def generate_object_file(object_name: str, field_api_name: str, label: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <fullName>{field_api_name}</fullName>
        <externalId>false</externalId>
        <label>{label}</label>
        <required>false</required>
        <trackHistory>false</trackHistory>
        <trackTrending>false</trackTrending>
        <type>Text</type>
    </fields>
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
    <version>63.0</version>
</Package>"""




@app.route('/append-field', methods=['POST'])
def append_field():
    # access_token = '00DdM00000B48zI!AQEAQP6GFVeamFnzVkHHyp4Ivcak8Nk8MfOI6ek5eWHb8R1elkKgJA5P4TS3L4Q1qR7JMtTaQ6P6ZDdgismJaY9TJHEVN3aj'  # Replace this
    # instance_url = 'https://ssadminlearn123-dev-ed.develop.my.salesforce.com'
    data = request.get_json()
    access_token = "00DdM00000B48zI!AQEAQP6GFVeamFnzVkHHyp4Ivcak8Nk8MfOI6ek5eWHb8R1elkKgJA5P4TS3L4Q1qR7JMtTaQ6P6ZDdgismJaY9TJHEVN3aj"
    instance_url = "https://ssadminlearn123-dev-ed.develop.my.salesforce.com"
    object_name = data['objectName']
    field_api_name = data['fieldAPIName']
    
    layout_full_name = f"{object_name}-{object_name} Layout"

    try:
        retrieve_id = retrieve_layout_metadata(access_token, instance_url, layout_full_name)
        for _ in range(10):
            xml_response = check_retrieve_status(access_token, instance_url, retrieve_id)
            layout_xml = extract_layout_from_response(xml_response)
            if layout_xml:
                break
            time.sleep(2)
        
        if not layout_xml:
            return jsonify({"error": "Layout not retrieved"}), 500
        
        updated_layout = append_field_to_layout(layout_xml, field_api_name)

        return jsonify({"updatedLayoutXml": updated_layout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=PORT)
