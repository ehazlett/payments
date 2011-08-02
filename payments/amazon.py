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
import hashlib
from hashlib import sha256
import base64
import hmac

class AmazonError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

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


    def _sign(self, endpoint_host=None, base_url='/', params={}):
        """
        Signs a url for FPS

        """
        #param_str = 'GET\n'
        #param_str = endpoint_host.lower() + '\n'
        #param_str = '{0}\n'.format(base_url)

        #print(param_str)
        #def quote(thing): return urllib.quote(str(thing), '')
        #param_str += '&'.join( quote(i[0]) + '=' + quote(i[1]) for i in sorted(params.items()))
        #hmac256 = hmac.new(self.__api_password, digestmod=sha256)
        #hmac256.update(param_str)
        #sig = base64.encodestring(hmac256.digest()).strip()
        ##sig = base64.b64encode(hmac.new(self.__api_password, param_str, hashlib.sha256).digest())
        #print(sig)
        #return sig
        parts = ''
        for k in sorted(params.keys()):
            parts += '&%s=%s' % (str(k), urllib.quote(str(params[k]), '~'))
        canonical = '\n'.join(['GET', str(endpoint_host).lower(), base_url, parts[1:]])
        hmac256 = hmac.new(self.__api_password, digestmod=sha256)
        hmac256.update(canonical)
        sig = base64.encodestring(hmac256.digest()).strip()
        return sig

    def get_api_endpoint(self): return self.__api_base_url
    def get_endpoint_host(self, url=None): return url.replace('https://', '').split('/')[0]

    def get_authorization_url(self, token_type=None, transaction_amount=None, \
        amount_type=None, caller_reference=None, global_amount_limit='10000', payment_reason='',\
        data={}):
        """
        Returns the URL that the user needs to visit to setup a payment authorization
        
        :keyword data: Pipeline specific parameters
        :rtype: string

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
        ep_host = self.get_endpoint_host(self.__api_cbservice_url)
        data['signature'] = self._sign(ep_host, '/cobranded-ui/actions/start', data)
        params = urllib.urlencode(sorted(data.items()))
        return self.__api_cbservice_url + '?' + params
    
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
        data['Action'] = action
        data['AWSAccessKeyId'] = self.__api_username
        data['Version'] = self.__api_version
        data['Timestamp'] = datetime.now().isoformat()
        sig = self._sign(self.get_endpoint_host(self.__api_base_url), '/', data)
        data['Signature'] = sig
        data['SignatureMethod'] = 'HmacSHA256'
        data['SignatureVersion'] = 2
        params = urllib.urlencode(sorted(data.keys()))
        print(url + params)
        resp, content = http.request(url+params, method, headers=headers)
        print(resp, content)
        data = {}
        if content.find('&') > -1:
            for x in content.split('&'):
                k,v = x.split('=')
                data[k] = v
        return (resp, data)
    
