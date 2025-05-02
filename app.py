from flask import Flask, request, send_file, render_template_string
import os
import shutil
from utils.generate_metadata import create_metadata_folder
import zipfile
import uuid
from flask import request, jsonify
import requests

PORT = 5000
REDIRECT_URI = f'http://localhost:{PORT}/redirect.html'
app = Flask(__name__)


@app.route('/generate', methods=['POST'])
def generate_metadata():
    objects = request.get_json()

    session_id = str(uuid.uuid4())
    base_folder = f'metadata/{session_id}'
    os.makedirs(base_folder, exist_ok=True)

    create_metadata_folder(base_folder, objects)

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


from flask import request, jsonify
import requests

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



if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=PORT)
