# Copyright  2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


from subprocess import call, PIPE
from datetime import datetime, timedelta
from logging import getLogger

from django.conf import settings
from django.test import TestCase
from django.test import client, simple, testcases

from mongoengine.connection import connect
from mongoengine import connection, register_connection

from report_server.sreport.models import ProductUsage
from report_server.common.biz_rules import Rules
from report_server.common import config
from report_server.common import constants
from report_server.common.products import Product_Def
from report_server.common.report import hours_per_consumer
from report_server.sreport.models import ReportData
from report_server.sreport.models import SpliceServer
from report_server.sreport.tests.setup import TestData, Product

from rhic_serve.rhic_rest.models import RHIC, Account

from splice.common import config
from splice.common.test_utils import RawTestApiClient

from tastypie.test import ResourceTestCase
from tastypie import authentication

LOG = getLogger(__name__)
#this_config = config.get_import_info()
ss = SpliceServer

import base64
import os

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_data")

'''
Currently the unit tests required that the rhic_serve database has been populated w/ the sample-load.py script
This can be found @rhic_serve/playpen/sample-load.py
Example: python sample-load.py Splice-RHIC-Sample-Data.csv Splice-Product-Definitions.csv

Although the product usage data from the is not used from the splice-server's generate_usage_data.py script, the generated RHIC's are used.
It is also a current requirement to load RHIC's.
This script can be found @splice-server/playpen/generate_usage_data.py
Example: PYTHONPATH=~/workspace/rhic_serve/ DJANGO_SETTINGS_MODULE='dev.settings' ./generate_usage_data.py -n 1

Example of running these unit tests from $checkout/src
#python manage.py test sreport --settings=dev.settings -v 3

'''

RHEL = TestData.RHEL
HA = TestData.HA
EUS = TestData.EUS
LB = TestData.LB
JBoss = TestData.JBoss
EDU = TestData.EDU
UNLIMITED = TestData.UNLIMITED
GEAR = TestData.GEAR

products_dict = TestData.PRODUCTS_DICT


rules = Rules()
report_biz_rules = rules.get_rules()


#MONGO_TEST_DATABASE_NAME = 'test_%s' % settings.MONGO_DATABASE_NAME
rhic_serve = settings.MONGO_DATABASE_NAME_RHICSERVE
checkin_service = settings.MONGO_DATABASE_NAME_CHECKIN
report = settings.MONGO_DATABASE_NAME
#default = settings.MONGO_DATABASE_NAME_RHICSERVE
DATABASES = [rhic_serve, checkin_service, report]


class MongoTestRunner(simple.DjangoTestSuiteRunner):

    def setup_databases(self, *args, **kwargs):
        pass

    def teardown_databases(self, *args, **kwargs):
        pass


class PatchClient(client.Client):

    def patch(self, path, data={}, content_type=client.MULTIPART_CONTENT,
             **extra):
        "Construct a PATCH request."

        post_data = self._encode_data(data, content_type)
        
        username = 'shadowman@redhat.com:shadowman@redhat.com'
        #credentials = base64.b64encode(username)
        #client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials

        parsed = client.urlparse(path)
        r = {
            'CONTENT_LENGTH': len(post_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   parsed[4],
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input':     client.FakePayload(post_data),
        }
        r.update(extra)
        return self.request(**r)

"""
class MongoTestCase(BaseMongoTestCase):

    def setUp(self):
        super(MongoTestCase, self).setUp()
        self.setup_database()
        #self.client.defaults['SSL_CLIENT_CERT'] = \
           # open(config.CONFIG.get('security', 'rhic_ca_cert')).read()

    def setup_database(self, *args, **kwargs):
        # Disconnect from the default mongo db, and use a test db instead.
        pass
        self.disconnect_dbs()
        connection.connect(MONGO_TEST_DATABASE_NAME, 
            alias=settings.MONGO_DATABASE_NAME, tz_aware=True)

        for collection in ['account', 'user', 'rhic', 'fs.chunks',
            'fs.files']:
            print 'importing %s collection' % collection
            call(['mongoimport', '--db', MONGO_TEST_DATABASE_NAME,
                '-c', collection, '--file', 
                '%s.json' % os.path.join(settings.DUMP_DIR, collection)])
"""


class BaseMongoTestCase(ResourceTestCase):
    
    client_class = PatchClient

    def _fixture_setup(self, *args, **kwargs):
        pass

    def _fixture_teardown(self, *args, **kwargs):
        pass
    
    def tearDown(self):
        self.teardown_database()
        super(BaseMongoTestCase, self).tearDown()

    def setUp(self):
        super(BaseMongoTestCase, self).setUp()
        self.setup_database()
        self.drop_product_usage()
        self.drop_report_data()
        self.drop_products()
        self.drop_pools()
        #required to add authorization to the headers for tastypie.. :(
        username = 'shadowman@redhat.com:shadowman@redhat.com'
        credentials = base64.b64encode(username)
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials
        
    def drop_products(self):
        #Note:  name conflict of 'Product' with 'report_server.sreport.tests.setup.Product'
        from report_server.sreport.models import Product
        Product.drop_collection()
        
    def drop_pools(self):
        from report_server.sreport.models import Pool
        Pool.drop_collection()

    def drop_rules(self):
        #Note: name conflict with 'report_server.common.biz_rules.Rules'
        from report_server.sreport.models import Rules
        Rules.drop_collection()

    def drop_product_usage(self):
        ProductUsage.drop_collection()
    
    def drop_report_data(self):
        ReportData.drop_collection()

    def setup_database(self):
        # Disconnect from the default mongo db, and use a test db instead.
        self.disconnect_dbs()
        connection.connect(rhic_serve, 
            alias='default', tz_aware=True)
        register_connection(rhic_serve, rhic_serve)
        register_connection(checkin_service, checkin_service)
        register_connection(report, report)
        register_connection('default', rhic_serve)

        for collection in ['rhic', 'account', 'user', 'fs.chunks']:
            #print 'importing %s collection' % collection
            call(['mongoimport', '--db', rhic_serve,
                  '-c', collection, '--file', 
                  '%s.json' % os.path.join(settings.DUMP_DIR, collection)],
                 stdout=PIPE, stderr=PIPE)
        
        for collection in ['splice_server', 'product']:
            #print 'importing %s collection' % collection
            call(['mongoimport', '--db', checkin_service,
                  '-c', collection, '--file', 
                  '%s.json' % os.path.join(settings.DUMP_DIR, collection)],
                 stdout=PIPE, stderr=PIPE)
    
    def teardown_database(self, *args, **kwargs):
        self.disconnect_dbs()
        # Drop the test database
        #for db in DATABASES:
        #    pymongo_connection = connection.get_connection(db)
        #    pymongo_connection.drop_database(db)
    
    def disconnect_dbs(self):
        for alias in connection._connections.keys():
            connection.disconnect(alias)


class MongoApiTestCase(BaseMongoTestCase):

    username = 'shadowman@redhat.com'
    password = 'shadowman@redhat.com'

    def setUp(self):
        super(MongoApiTestCase, self).setUp()
        self.valid_identity_cert_pem =  os.path.join(TEST_DATA_DIR, "valid_cert", "valid.cert")
        self.valid_identity_cert_pem = open(self.valid_identity_cert_pem, "r").read()

    def login(self):
        if os.path.isfile("/etc/rhn/rhn.conf"):
            raise Exception("You are currently running unit tests designed for the METERING " + 
                            "version of report-server.  Please remove the /etc/rhn/rhn.conf file")
        login = self.client.login(username=self.username, password=self.password)
        #if login fails, check if there is a /etc/rhn/rhn.conf and if the spacewalk auth backend is used
        self.assertTrue(login)
        self.client.request


    def post(self, url, data, code=202):
        self.login()
        content_type = 'application/json'
        response = self.client.post(url, data, content_type)
        self.assertEquals(response.status_code, code)
        self.client.logout()
        return response

    def get(self, url):
        self.login()
        content_type = 'application/json'
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.client.logout()
        return response

    def delete(self, url):
        self.login()
        content_type = 'application/json'
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 204)
        self.client.logout()
        return response

    def patch(self, url, data, code=202):
        self.login()
        content_type = 'application/json'
        response = self.client.patch(url, data, content_type)
        self.assertEquals(response.status_code, code)
        self.client.logout()
        return response


