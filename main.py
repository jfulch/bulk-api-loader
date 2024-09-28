import os
from nicegui import ui
import subprocess
import json

@ui.page('/')
def main_page():
    with ui.card().style('width: 50%; max-width: 2000px; margin: auto; padding: 20px;'):
        with ui.column().style('align-items: center;'):
            ui.label('Zuora Bulk API Upload Form').style('font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px;')
            
            with ui.column().style('gap: 10px; align-items: center;'):
                zuora_auth_url = ui.input(label='Zuora Auth URL').style('width: 600px;')
                zuora_api_url = ui.input(label='Zuora API URL').style('width: 600px;')
                zuora_object = ui.input(label='Zuora Object').style('width: 600px;')
                action = ui.select(label='Action', options=['Create', 'Update'], value='Update').style('width: 600px;')
                zuora_user_name = ui.input(label='Zuora User Name').style('width: 600px;')
                zuora_password = ui.input(label='Zuora Password').props('type=password').style('width: 600px;')
                csv_file = ui.upload(label='Upload CSV File').style('width: 600px;')
                #client_id = ui.input(label='Client ID').style('width: 600px;')
                #client_secret = ui.input(label='Client Secret').style('width: 600px;')
            
            submit_button = ui.button('Submit').style('margin-top: 20px;')
            loading_spinner = ui.spinner().style('display: none; margin-top: 20px;')
            log_display = ui.textarea(label='Log').props('readonly').style('width: 600px; height: 200px; margin-top: 20px;')

            def handle_submit():
                print("Submit button clicked")  # Debug log
                os.environ['ZUORA_AUTH_URL'] = zuora_auth_url.value
                os.environ['API_URL'] = zuora_api_url.value
                os.environ['ZUORA_OBJ'] = zuora_object.value
                os.environ['ACTION'] = action.value
                os.environ['ZUORA_USER_NAME'] = zuora_user_name.value
                os.environ['ZUORA_PASSWORD'] = zuora_password.value
                #os.environ['CLIENT_ID'] = client_id.value
                #os.environ['CLIENT_SECRET'] = client_secret.value

                # Show loading spinner and clear log
                loading_spinner.style('display: block;')
                log_display.value = ''

            def on_upload(event):
                print("File uploaded")  # Debug log
                uploaded_file = event['file']
                if uploaded_file['name'].endswith('.csv'):
                    file_content = uploaded_file['content'].decode('utf-8')
                    print("File content received")  # Debug log
                    # Pass the file content to the zuora_import_basic_auth.py script
                    process = subprocess.Popen(['python3', 'zuora_import_basic_auth.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate(input=json.dumps(file_content))
                    print("Subprocess completed")  # Debug log
                    # Hide loading spinner
                    loading_spinner.style('display: none;')
                    # Update log display
                    log_display.value = stdout + '\n' + stderr
                    print("Log updated")  # Debug log
                else:
                    ui.notify('Please upload a CSV file.', color='red')

            csv_file.on('upload', on_upload)
            submit_button.on('click', handle_submit)

ui.run()