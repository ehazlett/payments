#!/usr/bin/env python
#   Copyright 2011 Evan Hazlett
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import httplib2
import urllib
import logging
from datetime import datetime, timedelta

class PayPalError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AdaptivePaymentsAPI(object):
    """
    PayPal Adaptive Payments API operations

    """
    def __init__(self, api_username=None, api_password=None, api_signature=None, app_id='default', \
        cancel_url=None, return_url=None, ipn_url=None, debug=False):
        """
        AdaptivePayments API 

        :keyword api_user: PayPal API username
        :keyword api_password: PayPal API password
        :keyword api_signature: PayPal API signature
        :keyword app_id: PayPal API Application ID
        :keyword cancel_url: Url used for canceling payments
        :keyword return_url: Url used when PayPal redirects users back to site
        :keyword ipn_url: Url used for Instant Payment notification
        :keyword debug: Sets the url to the PayPal sandbox url (default False)

        """
        if not api_username or not api_password or not api_signature or not cancel_url \
            or not return_url or not ipn_url:
            raise PayPalError("""You must specify an api_username, api_password, """
                """api_signature, cancel_url, return_url, and ipn_url""")
        self.__api_username = api_username
        self.__api_password = api_password
        self.__api_signature = api_signature
        self.__api_request_format = 'NV'
        self.__api_response_format = 'NV'
        self.__api_app_id = app_id
        self.__api_cancel_url = cancel_url
        self.__api_return_url = return_url
        self.__api_ipn_url = ipn_url
        if debug:
            self.__api_base_url = 'https://svcs.sandbox.paypal.com/AdaptivePayments'
        else:
            self.__api_base_url = 'https://svcs.paypal.com/AdaptivePayments'
    
    def do_request(self, action=None, data={}):
        """
        Makes a PayPal AdaptivePayments API request with the specified params
        
        :keyword action: Type of action (i.e. Pay, Preapproval, etc.)
        :keyword data: Data to send as dict
        :rtype: response and content as tuple (response, content)
        
        """
        if not action:
            raise PayPalError('You must specify an action')
        url = '{0}/{1}'.format(self.__api_base_url, action)
        http = httplib2.Http()
        headers = {
            'X-PAYPAL-SECURITY-USERID': self.__api_username,
            'X-PAYPAL-SECURITY-PASSWORD': self.__api_password,
            'X-PAYPAL-SECURITY-SIGNATURE': self.__api_signature,
            'X-PAYPAL-REQUEST-DATA-FORMAT': self.__api_request_format,
            'X-PAYPAL-RESPONSE-DATA-FORMAT': self.__api_response_format,
            'X-PAYPAL-APPLICATION-ID': self.__api_app_id,
        }
        method = 'POST'
        data['cancelUrl'] = self.__api_cancel_url
        data['returnUrl'] = self.__api_return_url
        data['ipnNotificationUrl'] = self.__api_ipn_url
        params = urllib.urlencode(data)
        resp, content = http.request(url, method, params, headers=headers)
        data = {}
        if content.find('&') > -1:
            for x in content.split('&'):
                k,v = x.split('=')
                data[k] = v
        return (resp, data)
    
    def get_payment_details(self, pay_key=None):
        """
        Gets information about a payment
        
        :keyword pay_key: Pay key to lookup
        :rtype: response as dict

        """
        if not pay_key:
            raise PayPalError('You must specify a pay_key')
        data = {
            'requestEnvelope.errorLanguage': 'en_US',
            'payKey': pay_key,
        }
        resp, cont = self.do_request(action='PaymentDetails', data=data)
        if 'responseEnvelope.ack' not in cont:
            raise PayPalError('Error: Invalid PayPal response: {0}'.format(cont))
        if cont['responseEnvelope.ack'].lower() != 'success':
            errors = []
            for k,v in cont.iteritems():
                if k.find('error') > -1 and k.find('message') > -1:
                    v = urllib.unquote_plus(v)
                    errors.append(v.replace('+', ' '))
            raise PayPalError('Error requesting payment: {0}'.format('. '.join(errors)))
        return cont

    def get_preapproval_details(self, preapproval_key=None):
        """
        Gets information about a preapproval
        
        :keyword preapproval_key: Preapproval key to lookup
        :rtype: response as dict

        """
        if not preapproval_key:
            raise PayPalError('You must specify a preapproval_key')
        data = {
            'requestEnvelope.errorLanguage': 'en_US',
            'preapprovalKey': preapproval_key,
        }
        resp, cont = self.do_request(action='PreapprovalDetails', data=data)
        if 'responseEnvelope.ack' not in cont:
            raise PayPalError('Error: Invalid PayPal response: {0}'.format(cont))
        if cont['responseEnvelope.ack'].lower() != 'success':
            errors = []
            for k,v in cont.iteritems():
                if k.find('error') > -1 and k.find('message') > -1:
                    v = urllib.unquote_plus(v)
                    errors.append(v.replace('+', ' '))
            raise PayPalError('Error requesting payment: {0}'.format('. '.join(errors)))
        return cont

    def request_payment(self, currency='USD', sender_email=None, receivers={}, memo=''):
        """
        Requests a simple payment from the sender and returns the payment ID

        :keyword currency: Type of currency (default USD)
        :keyword sender_email: Email address of sender
        :keyword receivers: dict of receivers -- format must be the following:
            receiver_email_address: amount -- i.e.  receivers['receiver@domain.com'] = 200
        :keyword memo: Note for payment
        :rtype: response as dict

        """
        if not sender_email or len(receivers) == 0:
            raise PayPalError('You must specify a url, sender_email, and receivers')
        data = {
            'requestEnvelope.errorLanguage': 'en_US',
            'actionType': 'PAY',
            'senderEmail': sender_email,
            'currencyCode': currency,
            'feesPayer': 'EACHRECEIVER',
            'memo': memo,
            'cancelUrl': self.__api_cancel_url,
            'returnUrl': self.__api_return_url,
            'ipnNotificationUrl': self.__api_ipn_url,
        }
        # build receivers
        i = 0
        for k,v in receivers.iteritems():
            data['receiverList.receiver({0}).email'.format(i)] = k
            data['receiverList.receiver({0}).amount'.format(i)] = v
        resp, cont = self.do_request(action='Pay', data=data)
        if 'responseEnvelope.ack' not in cont:
            raise PayPalError('Error: Invalid PayPal response: {0}'.format(cont))
        if cont['responseEnvelope.ack'].lower() != 'success':
            errors = []
            for k,v in cont.iteritems():
                if k.find('error') > -1 and k.find('message') > -1:
                    v = urllib.unquote_plus(v)
                    errors.append(v.replace('+', ' '))
            raise PayPalError('Error requesting payment: {0}'.format('. '.join(errors)))
        return cont

    def setup_preapproval(self, currency='USD', sender_email=None, pin_type='NOT_REQUIRED', \
        starting_date=datetime.now().isoformat(), ending_date=None, max_amount_per_payment=None, \
        max_number_of_payments=None, max_total_amount_of_payments=None):
        """
        Sets up a pre-approved payment.  Returns response as dict

        :keyword currency: Type of currency (default USD)
        :keyword sender_email: Email address of sender
        :keyword pin_type: Type of pin (default no pin required)
        :keyword starting_date: Start date of payment (default is now)
        :keyword ending_date: End date of payment
        :keyword max_amount_per_payment: Max amount charged for each payment
        :keyword max_number_of_payments: Max number of individual payments
        :keyword max_total_amount_of_payments: Total amount that can be charged for the preapproval
        :rtype: response as dict

        """
        if not sender_email or not max_amount_per_payment or not max_number_of_payments or not \
            max_total_amount_of_payments or not ending_date:
                raise PayPalError("""You must specify sender_email, max_amount_per_payment, """
                    """max_number_of_payments, ending_date, and max_total_amount_of_payments""")
        data = {
            'requestEnvelope.errorLanguage': 'en_US',
            'actionType': 'Preapproval',
            'currencyCode': currency,
            'startingDate': starting_date,
            'endingDate': ending_date,
            'pinType': pin_type,
            'senderEmail': sender_email,
            'maxAmountPerPayment': max_amount_per_payment,
            'maxNumberOfPayments': max_number_of_payments,
            'maxTotalAmountOfAllPayments': max_total_amount_of_payments,
            'cancelUrl': self.__api_cancel_url,
            'returnUrl': self.__api_return_url,
        }
        resp, cont = self.do_request(action='Preapproval', data=data)
        if 'responseEnvelope.ack' not in cont:
            raise PayPalError('Error: Invalid PayPal response: {0}'.format(cont))
        if cont['responseEnvelope.ack'].lower() != 'success':
            errors = []
            for k,v in cont.iteritems():
                if k.find('error') > -1 and k.find('message') > -1:
                    v = urllib.unquote_plus(v)
                    errors.append(v.replace('+', ' '))
            raise PayPalError('Error requesting payment: {0}'.format('. '.join(errors)))
        return cont


