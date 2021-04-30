import requests

from log import error, warn, info, debug


def send_http_post_request(**kwargs):
    if not any(k in kwargs for k in ['url', 'data']):
        error(f"Invalids HTTP request kwargs: {kwargs}")
        return
    headers = {
        'user-agent': "gotoiot",
        'content-type': "application/json"
        }
    if 'headers' in kwargs and isinstance(kwargs['headers'], dict):
        headers.update(kwargs['headers'])
    response = requests.request("POST", kwargs['url'], data=kwargs['data'], headers=headers)
    return response.text