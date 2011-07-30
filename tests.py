#!/usr/bin/env python

import unittest
try:
    import local_settings
except ImportError:
    pass

class TestPreApprovalAPI(unittest.TestCase):
    def setUp(self):
        self.api_username = 'ejhazl_1236995983_biz_api1.gmail.com'
        self.api_password = '1236995989'
        self.api_signature = 'AQU0e5vuZCvSg-XJploSa.sGUDlpAZoUpIYWaAwasX6MCPYCmVFEFz8m'

    def test_preapproval_setup(self):
        


if __name__=='__main__':
    unittest.main()

