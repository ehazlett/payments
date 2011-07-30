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

class PayPalError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class PreApprovalAPI(object):
    """
    PreApproval API operations

    """
    def __init__(self, api_username, api_password, api_signature, app_id='default'):
        if not api_username or not api_password or not api_signature:
            raise PayPalError("""You must specify an api_username, api_password, """
                """and api_signature""")
        self.__api_username = api_username
        self.__api_password = api_password
        self.__api_signature = api_signature
        self.__api_request_format = 'NV'
        self.__api_response_format = 'NV'
        self.__api_app_id = app_id
    
    def do_request(self, url=None, **params):
        """Makes a PayPal request with the specified params"""
        http = httplib2.Http()
        headers = {
            'X-PAYPAL-SECURITY-USERID': self.__api_username,
            'X-PAYPAL-SECURITY-PASSWORD': self.__api_password,
            'X-PAYPAL-SECURITY-SIGNATURE': self.__api_signature,
            'X-PAYPAL-REQUEST-DATA-FORMAT': self.__api_request_format,
            'X-PAYPAL-RESPONSE-DATA-FORMAT': self.__api_response_format,
            'X-PAYPAL-APPLICATION-ID': self.__api_app_id,
        }
        if params:
            method = 'POST'
            data = urllib.urlencode(params)
        else:
            method = 'GET'
            data = None
        if data:
            resp, content = http.request(url, method, data)
        else:
            resp, content = http.request(url, method)
        return resp, content

