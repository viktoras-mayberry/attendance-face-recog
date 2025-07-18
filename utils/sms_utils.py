from twilio.rest import Client
import os

twilio_client = None

def init_twilio(app=None):
    global twilio_client
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    if app:
        account_sid = app.config.get('TWILIO_ACCOUNT_SID', account_sid)
        auth_token = app.config.get('TWILIO_AUTH_TOKEN', auth_token)
    twilio_client = Client(account_sid, auth_token)

def send_sms(to, body, from_=None):
    global twilio_client
    if not twilio_client:
        raise Exception('Twilio client not initialized. Call init_twilio() first.')
    from_number = from_ or os.environ.get('TWILIO_PHONE_NUMBER')
    message = twilio_client.messages.create(
        body=body,
        from_=from_number,
        to=to
    )
    return message.sid 