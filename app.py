from flask import Flask, request, send_file
import os
import shutil
from utils.generate_metadata import create_metadata_folder
import zipfile
import uuid

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_metadata():
    data = request.get_json()

    object_label = data['objectLabel']
    object_api_name = data['objectApiName']
    object_plural_label = data['objectPluralLabel']
    fields = data['fields']

    session_id = str(uuid.uuid4())
    base_folder = f'metadata/{session_id}'
    os.makedirs(base_folder, exist_ok=True)

    create_metadata_folder(base_folder, object_label, object_api_name, object_plural_label, fields)

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
def index():
    return open('templates/index.html').read()

if __name__ == '__main__':
    app.run(debug=True)
