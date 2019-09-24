import os
from pyfcm import FCMNotification

def notification(registrationId, title, body):
    push_service = FCMNotification(api_key=os.environ.get("FCM_API_KEY"))
    registration_id = registrationId
    message_title = title
    message_body = body
    if type(registrationId) == str:
        result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)
    elif type(registrationId) == list:
        result = push_service.notify_multiple_devices(registration_ids=registration_id, message_title=message_title, message_body=message_body)
    else:
        raise Exception('registration id should be a string or a list of strings')