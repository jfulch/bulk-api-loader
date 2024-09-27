import csv
import requests
import time
import logging
import os
import json

# Values from user input
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')  # File to import, default if not set
zuora_obj = os.getenv('ZUORA_OBJ')  # Zuora object to update
action = os.getenv('ACTION')  # Action to perform

# Read values from environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ZUORA_AUTH_URL = os.getenv('ZUORA_AUTH_URL')
API_URL = os.getenv('API_URL')
ZUORA_USER_NAME = os.getenv('ZUORA_USER_NAME')
ZUORA_PASSWORD = os.getenv('ZUORA_PASSWORD')

# Configure logging to write only to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler()
])

def read_data_from_csv(file_path):
    data = []
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)
    return data

def get_new_token(retries=3, delay=5):
    logging.info(f"Request URL: {ZUORA_AUTH_URL}")
    logging.info(f"Request URL: {CLIENT_ID}")
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    for attempt in range(retries):
        try:
            response = requests.post(ZUORA_AUTH_URL, data=payload, headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            })
            logging.info(f"Payload: {json.dumps(payload)}")  # Log the payload with pretty-print
            response.raise_for_status()    
            return response.json()['access_token']
        except requests.exceptions.RequestException as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

def log_last_successful_record(record_id):
    logging.info(f"Last successful record ID: {record_id}")

def log_failed_record(record_id, status_code, response_text):
    logging.error(f"Failed record ID: {record_id}, Status Code: {status_code}, Response: {response_text}")

def update_zuora_object(api_url, data, zuora_obj, headers):
    last_successful_id = None
    update_url = f'{api_url}/v1/action/update'
    logging.info(f"Update URL: {update_url}")
    batch_size = 50
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        try:
            logging.info(f"Processing batch with records: {[record['Id'] for record in batch]}")  # Log the IDs of the batch
            payload = {
                "objects": batch,
                "type": zuora_obj
            }
            logging.info(f"Payload: {json.dumps(payload)}")  # Log the payload with pretty-print
            response = requests.post(update_url, json=payload, headers=headers)
            if response.status_code == 200:
                logging.info(f"Successfully updated batch with records: {[record['Id'] for record in batch]}")
                last_successful_id = batch[-1]['Id']
            elif response.status_code == 401:  # Unauthorized, token might have expired
                logging.warning("Token expired, refreshing token...")
                headers['Authorization'] = f'Bearer {get_new_token()}'
                response = requests.post(update_url, json=payload, headers=headers)
                if response.status_code == 200:
                    logging.info(f"Successfully updated batch with records: {[record['Id'] for record in batch]} after refreshing token")
                    last_successful_id = batch[-1]['Id']
                else:
                    logging.error(f"Failed to update batch with records: {[record['Id'] for record in batch]} after refreshing token, Status Code: {response.status_code}, Response: {response.text}")
                    for record in batch:
                        log_failed_record(record['Id'], response.status_code, response.text)
                    log_last_successful_record(last_successful_id)
            else:
                logging.error(f"Failed to update batch with records: {[record['Id'] for record in batch]}, Status Code: {response.status_code}, Response: {response.text}")
                for record in batch:
                    log_failed_record(record['Id'], response.status_code, response.text)
                log_last_successful_record(last_successful_id)
        except KeyError as e:
            logging.error(f"KeyError: {e} in batch with records: {[record['Id'] for record in batch]}")
            for record in batch:
                log_failed_record(record.get('Id', 'Unknown'), 'KeyError', str(e))
            log_last_successful_record(last_successful_id)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            for record in batch:
                log_failed_record(record.get('Id', 'Unknown'), 'Exception', str(e))
            log_last_successful_record(last_successful_id)

def create_zuora_object(api_url, data, zuora_obj, headers):
    create_url = f'{api_url}/v1/object/{zuora_obj}'
    logging.info(f"Create URL: {create_url}")
    for record in data:
        try:
            payload = {key: record[key] for key in record}  # Dynamically construct payload from CSV headers
            logging.info(f"Payload: {json.dumps(payload, indent=2)}")  # Log the payload with pretty-print
            response = requests.post(create_url, json=payload, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("Success"):
                    logging.info(f"Successfully created record with ID: {response_data['Id']}")
                else:
                    logging.error(f"Failed to create record: {response_data}")
                    log_failed_record(response_data.get('Id', 'Unknown'), response.status_code, response.text)
            elif response.status_code == 401:  # Unauthorized, token might have expired
                logging.warning("Token expired, refreshing token...")
                headers['Authorization'] = f'Bearer {get_new_token()}'
                response = requests.post(create_url, json=payload, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get("Success"):
                        logging.info(f"Successfully created record with ID: {response_data['Id']} after refreshing token")
                    else:
                        logging.error(f"Failed to create record: {response_data}")
                        log_failed_record(response_data.get('Id', 'Unknown'), response.status_code, response.text)
                else:
                    logging.error(f"Failed to create record after refreshing token, Status Code: {response.status_code}, Response: {response.text}")
                    log_failed_record('Unknown', response.status_code, response.text)
            else:
                logging.error(f"Failed to create record, Status Code: {response.status_code}, Response: {response.text}")
                log_failed_record('Unknown', response.status_code, response.text)
        except KeyError as e:
            logging.error(f"KeyError: {e} in record")
            log_failed_record('Unknown', 'KeyError', str(e))
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            log_failed_record('Unknown', 'Exception', str(e))

if __name__ == "__main__":
    headers = {
        'Authorization': f'Bearer {get_new_token()}',  # Get initial token
        'Content-Type': 'application/json'
    }

    data = read_data_from_csv(CSV_FILE_PATH)

    if action == 'update':
        update_zuora_object(API_URL, data, zuora_obj, headers)
    elif action == 'create':
        create_zuora_object(API_URL, data, zuora_obj, headers)
    else:
        logging.error("Invalid action. Please enter 'update' or 'create'")