#!/usr/bin/env python

import datetime
import logging
import os
import webapp2
from utils import generate_new_bitcoin_address
from utils import json_response
from utils import recaptcha_verify
from utils import render
from models import Transaction


class MainHandler(webapp2.RequestHandler):
    def get(self):
        render(self, 'template/index.html', {'current_page': 'home'})


class MakePaymentHandler(webapp2.RequestHandler):
    def get(self):
        render(self, 'template/payment.html', {
            'current_page': 'payment',
            'recaptcha_sitekey': os.environ.get('RECAPTCHA_SITEKEY')
        })

    def post(self):
        if not os.environ.get('SKIP_RECAPTCHA_TEST'):
            recaptcha_response = self.request.get('recaptcha-response')

            if not recaptcha_response:
                return json_response(self, {'success': False, 'message': 'MISSING_PARAMETER'})

            # verify captcha challenge
            recaptcha_result = recaptcha_verify(self, recaptcha_response)
            logging.info(recaptcha_result)
            logging.info(recaptcha_result['status'])

            if not recaptcha_result['status']:
                return json_response(self, {'success': False, 'message': 'CAPTCHA_VERIFICATION_FAILED'})


        # create a new transaction for this payment
        new_transaction = Transaction()
        new_transaction.populate(
            is_mainnet=True,
        )
        new_transaction.put()

        # Generate new bitcoin address for this transaction
        address_result = generate_new_bitcoin_address(new_transaction.key.id())

        if 'message' in address_result:
            return json_response(self, {
                'success': False,
                'message': address_result['message']
            })

        new_transaction.payment_address = address_result['address']
        new_transaction.put()

        return json_response(self, {
            'success': True,
            'message': 'TRANSACTION_CREATED',
            'data': {
                'tx_id': new_transaction.key.id()
            }
        })


class PaymentTransactionHandler(webapp2.RequestHandler):
    def get(self, tx_id):

        tx = Transaction.get_by_id(int(tx_id))

        if not tx:
            self.response.write('Transaction {} not found'.format(tx_id))
            return

        render(self, 'template/transaction.html', {
            'current_page': 'payment',
            'tx': tx
        })


class ReceivedPaymentHandler(webapp2.RequestHandler):
    def get(self):
        complete = self.request.get('complete', '')
        payment_status_target = (complete == '')  # blank `complete` query string: completed list
        tx_query = Transaction.query()
        tx_query = tx_query.filter(Transaction.payment_complete == payment_status_target)
        tx_query = tx_query.order(-Transaction.create_time)
        transactions = tx_query.fetch()

        render(self, 'template/received.html', {
            'current_page': 'received',
            'transactions': transactions,
            'complete': complete,
        })



class CallbackHandler(webapp2.RequestHandler):
    def get(self, tx_id):
        secret = self.request.get('secret')
        transaction_hash = self.request.get('transaction_hash')
        value = self.request.get('value')
        if not secret:
            logging.debug('Missing secret')
            self.response.write("Invalid request")
            return

        if secret != os.environ.get('APP_SECRET'):
            logging.debug('Invalid secret')
            self.response.write("Invalid request")
            return

        transaction = Transaction.get_by_id(int(tx_id))

        if not transaction:
            logging.debug('Transaction not found')
            self.response.write("Invalid Transaction ID")
            return

        if not transaction_hash or not value:
            logging.debug('Missing parameter transaction_hash or value')
            self.response.write("Missing parameter")
            return

        transaction.payment_time = datetime.datetime.now()
        transaction.amount = float(value)
        transaction.payment_complete = True
        transaction.tx_id = transaction_hash
        transaction.put()

        self.response.write('ok')



app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/payment/<tx_id:\d+>', PaymentTransactionHandler),
    webapp2.Route('/callback/<tx_id:\d+>', CallbackHandler),
    webapp2.Route('/payment', MakePaymentHandler),
    webapp2.Route('/received', ReceivedPaymentHandler),
], debug=True)
