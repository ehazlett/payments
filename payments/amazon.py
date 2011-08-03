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
import uuid
from datetime import datetime, timedelta
import time
import hashlib
from hashlib import sha256
import base64
import hmac
import xml.parsers.expat

class AmazonError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FPSResponseParser(object):
    def __init__(self, data):
        self.__data = data
        self.__parsed_data = {}
        self.__cur_node = None
        self.__parser = xml.parsers.expat.ParserCreate()
        self.__parser.StartElementHandler = self.start_element
        self.__parser.CharacterDataHandler = self.char_data
        self.__parser.EndElementHandler = self.end_element
        self._parse()

    def _parse(self):
        self.__parser.Parse(self.__data, 1)

    def start_element(self, name, attrs):
        self.__cur_node = name

    def char_data(self, data):
        self.__parsed_data[str(self.__cur_node)] = data

    def end_element(self, name):
        pass

    def get_data(self):
        return self.__parsed_data

class FlexiblePaymentsService(object):
    """
    PayPal Adaptive Payments API operations

    """
    def __init__(self, api_username=None, api_password=None, return_url='', \
        api_version='2010-08-28', debug=False):
        """

        :keyword api_user: PayPal API username
        :keyword api_password: PayPal API password
        :keyword return_url: Return url 
        :keyword debug: Sets the url to the PayPal sandbox url (default False)

        """
        if not api_username or not api_password :
            raise AmazonError("""You must specify an api_username and api_password, """)
        self.__api_username = api_username
        self.__api_password = api_password
        self.__api_version = api_version
        self.__api_return_url = return_url
        if debug:
            self.__api_base_url = 'https://fps.sandbox.amazonaws.com'
            self.__api_cbservice_url = 'https://authorize.payments-sandbox.amazon.com/cobranded-ui/actions/start'
        else:
            self.__api_base_url = 'https://fps.amazonaws.com'
            self.__api_cbservice_url = 'https://authorize.payments.amazon.com/cobranded-ui/actions/start'


    def _get_endpoint_host(self, url=None): return url.replace('https://', '').split('/')[0]

    def _parse_response(self, data):
        """
        Parses a response from the FPS API

        """
        p = FPSResponseParser(data)
        return p.get_data()

    def _sign(self, endpoint_host=None, base_url='/', params={}):
        """
        Signs a url for FPS

        """
        parts = ''
        for k in sorted(params.keys()):
            parts += '&%s=%s' % (str(k), urllib.quote(str(params[k]), '~'))
        canonical = '\n'.join(['GET', str(endpoint_host).lower(), base_url, parts[1:]])
        hmac256 = hmac.new(self.__api_password, digestmod=sha256)
        hmac256.update(canonical)
        sig = base64.encodestring(hmac256.digest()).strip()
        return sig

    def get_api_endpoint(self): return self.__api_base_url

    def do_request(self, action=None, data={}):
        """
        Makes a PayPal AdaptivePayments API request with the specified params
        
        :keyword action: Type of action (i.e. Pay, Preapproval, etc.)
        :keyword data: Data to send as dict
        :rtype: response and content as tuple (response, content)
        
        """
        if not action:
            raise PayPalError('You must specify an action')
        url = '{0}/?'.format(self.__api_base_url)
        http = httplib2.Http()
        headers = {
        }
        method = 'GET'
        data['Action'] = str(action)
        data['AWSAccessKeyId'] = str(self.__api_username)
        data['Version'] = str(self.__api_version)
        data['Timestamp'] = str(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        data['SignatureMethod'] = 'HmacSHA256'
        data['SignatureVersion'] = '2'
        sig = self._sign(self._get_endpoint_host(self.__api_base_url), '/', data)
        data['Signature'] = sig
        params = ''
        for k in sorted(data.keys()):
            params += '&%s=%s' % (str(k), urllib.quote(str(data[k]), '~'))
        #print('URL: {0}'.format(url+params))
        resp, content = http.request(url+params, method, headers=headers)
        return (resp, content)
    

    def get_authorization_url(self, token_type=None, transaction_amount=None, \
        amount_type=None, caller_reference=None, global_amount_limit='10000', payment_reason='',\
        data={}):
        """
        Returns the URL that the user needs to visit to setup a payment authorization
        
        :keyword token_type: Type of pipeline (i.e. SingleUse, MultiUse, etc.)
        :keyword transaction_amount: Amount to charge for transaction
        :keyword amount_type: Type of amount (i.e. Exact, Maximum, Minimum)
        :keyword caller_reference: Data used to identify transaction
        :keyword global_amount_limit: Maximum amount that can be charged during the 
            entire authorization period
        :keyword payment_reason: Note or description to user 
        :keyword data: Optional extra data
        :rtype: url as string

        """
        data['pipelineName'] = token_type
        data['transactionAmount'] = str(transaction_amount)
        data['amountType'] = amount_type
        data['globalAmountLimit'] = str(global_amount_limit)
        data['paymentReason'] = payment_reason
        if not caller_reference:
            caller_reference = str(uuid.uuid4())
        data['callerReference'] = caller_reference
        data['callerKey'] = self.__api_username
        data['signatureMethod'] = 'HmacSHA256'
        data['signatureVersion'] = '2'
        if isinstance(data, dict) and len(data) > 0:
            for k,v in data.iteritems():
                data[k] = str(v)
        ep_host = self._get_endpoint_host(self.__api_cbservice_url)
        data['signature'] = self._sign(ep_host, '/cobranded-ui/actions/start', data)
        params = urllib.urlencode(sorted(data.items()))
        return self.__api_cbservice_url + '?' + params
    

    def get_transaction_status(self, transaction_id=None):
        """
        Returns the status of the FPS transaction

        :keyword transaction_id: Transaction ID to check
        :rtype: status as dict

        """
        if not transaction_id:
            raise AmazonError('You must specify a transaction_id')
        data = {}
        data['TransactionId'] = transaction_id
        resp, cont = self.do_request('GetTransactionStatus', data)
        return self._parse_response(cont)

    def pay(self, sender_token_id=None, transaction_amount=None, currency='USD', \
        caller_reference=None, sender_description='', params={}):
        """
        Issues an FPS payment

        :keyword sender_token_id: Sender token used in transaction 
            (obtained from Co-Branded service request)
        :keyword transaction_amount: Amount to charge
        :keyword caller_reference: Value to identify request
        :keyword sender_description: Description or note for transaction
        :keyword params: Optional parameters to send as dict

        """
        if not sender_token_id or not transaction_amount:
            raise AmazonError('You must specify a sender_token_id and transaction_amount')
        data = {}
        data['SenderTokenId'] = sender_token_id
        data['TransactionAmount.CurrencyCode'] = currency
        data['TransactionAmount.Value'] = transaction_amount
        if not caller_reference:
            caller_reference = str(uuid.uuid4())
        data['CallerReference'] = caller_reference
        if isinstance(params, dict) and len(params) > 0:
            for k,v in params.iteritems():
                data[k] = v
        resp, cont = self.do_request('Pay', data)
        return self._parse_response(cont)
