import os
import csv
import json
import requests
from dotenv import load_dotenv
from tqdm import tqdm 

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
INSTANCE_URL = os.getenv("INSTANCE_URL")
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH")

MAX_BATCH_SIZE = 1
OBJECT_API_NAME = "Mass_Upload__c"

# Step 1: Get the access token
def get_access_token():
    token_url = "https://login.salesforce.com/services/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": REFRESH_TOKEN
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Token refresh failed: {response.text}")

# Step 2: Read CSV file and return list of dicts
def read_csv_records(csv_path):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

# Step 3: Break into batches of 200, format for composite API
def batch_records(records):
    batches = []
    for i in range(0, len(records), MAX_BATCH_SIZE):
        chunk = records[i:i + MAX_BATCH_SIZE]
        formatted = [{
            "attributes": { "type": OBJECT_API_NAME, "referenceId": f"rec{i+j+1}" },
            "Model_No__c": r["Model_No__c"],
            "Position__c": r["Position__c"],
            "Type__c": r["Type__c"],
            "OwnerId": r["OwnerId"]
        } for j, r in enumerate(chunk)]
        batches.append(formatted)
    return batches

# Step 4: Upload a single batch
def upload_batch(batch, token, batch_num):
    url = f"{INSTANCE_URL}/services/data/v63.0/composite/tree/{OBJECT_API_NAME}/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={"records": batch})

    if response.status_code in [200, 201]:
        result = response.json()
        if result.get("hasErrors"):
            print(f"Batch {batch_num:02}: Partial errors")
        else:
            print(f"Batch {batch_num:02}: Success")
    else:
        print(f"Batch {batch_num:02}: Failed (HTTP {response.status_code})")
        print("Error details:")
        print(json.dumps(response.json(), indent=2))
        exit(1)


# Step 5: Main
if __name__ == "__main__":
    try:
        access_token = get_access_token()
        print(" Access token refreshed successfully.")

        all_records = read_csv_records(CSV_FILE_PATH)
        batches = batch_records(all_records)
        print(f"Total records: {len(all_records)} → {len(batches)} batches of {MAX_BATCH_SIZE}")

        for idx, batch in enumerate(tqdm(batches, desc="Uploading Batches", unit="batch")):
            upload_batch(batch, access_token, idx + 1)

    except Exception as e:
        print(f"Error: {e}")