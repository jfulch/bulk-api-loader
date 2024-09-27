import os
from nicegui import ui

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
                #client_id = ui.input(label='Client ID').style('width: 600px;')
                #client_secret = ui.input(label='Client Secret').style('width: 600px;')
            
            submit_button = ui.button('Submit').style('margin-top: 20px;')

            def handle_submit():
                os.environ['ZUORA_AUTH_URL'] = zuora_auth_url.value
                os.environ['API_URL'] = zuora_api_url.value
                os.environ['ZUORA_OBJ'] = zuora_object.value
                os.environ['ACTION'] = action.value
                os.environ['ZUORA_USER_NAME'] = zuora_user_name.value
                os.environ['ZUORA_PASSWORD'] = zuora_password.value
                #os.environ['CLIENT_ID'] = client_id.value
                #os.environ['CLIENT_SECRET'] = client_secret.value

                # Call zuora_import.py or any other processing function here

            submit_button.on('click', handle_submit)

ui.run()