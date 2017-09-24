import json
import logging
import os
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template


def generate_new_bitcoin_address(tx_id):
    url = 'https://api.blockchain.info/v2/receive'

    callback_url = 'https://{}/callback/{}?secret={}'.format(
        os.environ['HTTP_HOST'],
        tx_id,
        os.environ['APP_SECRET']
    )

    params = {
        'xpub': os.environ.get('XPUB'),
        'callback_url': callback_url,
        'key': os.environ.get('BLOCKCHAIN_API_KEY')
    }
    # logging.info(params)
    # return {"address": "19jJyiC6DnKyKvPg38eBE8R6yCSXLLEjqw", "index": 23, "callback": "https://mystore.com?invoice_id=058921123"}

    form_data = urllib.urlencode(params)
    result = urlfetch.fetch(
        url=url + '?' + form_data,
    )

    logging.info(result.content)
    result_json = json.loads(result.content)
    return result_json



def recaptcha_verify(self, recaptcha_input):
    response = {}
    url = 'https://www.google.com/recaptcha/api/siteverify'
    params = {
        'secret': os.environ.get('RECAPTCHA_SECRET'),
        'response': recaptcha_input,
        'remoteip': os.environ.get('REMOTE_ADDR', '')
    }

    form_data = urllib.urlencode(params)
    result = urlfetch.fetch(
        url=url + '?' + form_data,
        headers={
            'Cache-Control': 'max-age=0, must-revalidate',
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
        }
    )

    logging.info(result.content)
    verify_rs = json.loads(result.content)
    logging.info(verify_rs)
    response["status"] = verify_rs.get("success", False)
    response['message'] = verify_rs.get('error-codes', None) or "Unspecified error."
    return response


def render(self, template_path, param={}, content_type="text/html", status=200):
    """
      Generic template display module
    """
    self.response.headers['Content-Type'] = content_type

    if status != 200:
        self.response.set_status(status)

    if content_type != "text/html":
        self.response.headers['cache-control'] = "no-cache, no-store, max-age=0, must-revalidate"

    params = {}
    params.update(param)

    path = os.path.join(os.path.dirname(__file__), template_path)
    self.response.out.write(template.render(path, params))


def json_response(self, data):

    response_text = json.dumps(data)
    self.response.headers['Content-Type'] = "application/json"
    self.response.out.write(response_text)


