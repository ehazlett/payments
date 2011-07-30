#!/usr/bin/env python

import unittest
from payments.paypal import AdaptivePaymentsAPI, ExpressCheckoutAPI
from datetime import datetime, timedelta
try:
    from payments import local_settings
except ImportError:
    pass

class TestAdaptivePaymentsAPI(unittest.TestCase):
    def setUp(self):
        self.api_username = getattr(local_settings, 'API_USERNAME', None)
        self.api_password = getattr(local_settings, 'API_PASSWORD', None)
        self.api_signature = getattr(local_settings, 'API_SIGNATURE', None)
        self.api_app_id = getattr(local_settings, 'API_APP_ID', None)
        self.adaptive_api = AdaptivePaymentsAPI(self.api_username, self.api_password, \
            self.api_signature, self.api_app_id, 'http://site.com', 'http://site.com', \
            'http://site.com', debug=True)

    def test_get_payment_details(self):
        receivers = {
            'receiver@domain.com': '100.00',
        }
        resp = self.adaptive_api.request_payment(sender_email='sender@domain.com', receivers=receivers,\
            memo='Test Payment')
        resp = self.adaptive_api.get_payment_details(resp['payKey'])
        self.assertEqual(resp['responseEnvelope.ack'].lower(), 'success')
        self.assertTrue(resp.has_key('senderEmail'))

    def test_get_preapproval_details(self):
        end_date = (datetime.now() + timedelta(days=30)).isoformat()
        resp = self.adaptive_api.setup_preapproval(sender_email='sender@domain.com', ending_date=end_date, \
            max_amount_per_payment=200, max_number_of_payments=60, max_total_amount_of_payments=5000)
        self.assertEqual(resp['responseEnvelope.ack'].lower(), 'success')
        preapproval_key = resp['preapprovalKey']
        resp = self.adaptive_api.get_preapproval_details(preapproval_key)
        self.assertEqual(resp['responseEnvelope.ack'].lower(), 'success')
        self.assertTrue(resp.has_key('status'))
        self.assertTrue(resp.has_key('senderEmail'))

    def test_request_pay(self):
        receivers = {
            'receiver@domain.com': '100.00',
        }
        resp = self.adaptive_api.request_payment(sender_email='sender@domain.com', receivers=receivers,\
            memo='Test Payment')
        self.assertEqual(resp['responseEnvelope.ack'].lower(), 'success')
        self.assertTrue(resp.has_key('payKey'))

    def test_setup_preapproval(self):
        end_date = (datetime.now() + timedelta(days=30)).isoformat()
        resp = self.adaptive_api.setup_preapproval(sender_email='sender@domain.com', ending_date=end_date, \
            max_amount_per_payment=200, max_number_of_payments=60, max_total_amount_of_payments=5000)
        self.assertEqual(resp['responseEnvelope.ack'].lower(), 'success')
        self.assertTrue(resp.has_key('preapprovalKey'))

class TestExpressCheckoutAPI(unittest.TestCase):
    def setUp(self):
        self.api_username = getattr(local_settings, 'API_USERNAME', None)
        self.api_password = getattr(local_settings, 'API_PASSWORD', None)
        self.api_signature = getattr(local_settings, 'API_SIGNATURE', None)
        self.api = ExpressCheckoutAPI(self.api_username, self.api_password, self.api_signature,\
            'http://site.com', 'http://site.com', 'http://site.com', debug=True)

    def test_set_express_checkout(self):
        vars = {
            'MAXAMT': 50,
            'NOSHIPPING': 1,
            'ALLOWNOTE': 0,
            'SOLUTIONTYPE': 'Mark',
            'PAYMENTREQUEST_0_AMT': 0,
            'PAYMENTREQUEST_0_PAYMENTACTION': 'Authorization',
            'L_PAYMENTREQUEST_0_ITEMCATEGORY0': 'Digital',
            'L_BILLINGTYPE0': 'RecurringPayments',
            'L_BILLINGAGREEMENTDESCRIPTION0': 'AppHosted service',
        }
        resp, cont = self.api.do_request('SetExpressCheckout', vars)
        self.assertTrue(cont.has_key('ACK'))
        self.assertEqual(cont['ACK'].lower(), 'success')
        self.assertTrue(cont.has_key('TOKEN'))

if __name__=='__main__':
    unittest.main()

