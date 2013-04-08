# Copyright 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


from django.http import HttpResponse
from report_server.sreport.models import QuarantinedReportData
from report_server.sreport.models import ReportData, SpliceServer, Filter
from report_server.sreport import views
from report_server.sreport.meter.views import report as meter_report
from report_server.sreport.spacewalk.views import report as space_report
from report_server.common import utils
from report_server.common import import_util
from splice.common.api import SpliceServerResource, MarketingProductUsageResource, \
    RulesResource, PoolResource, ProductResource
from report_server.report_import.api.productusage import ProductUsageResource
from splice.common.auth import X509CertificateAuthentication
from splice.common import certs
from tastypie.authorization import Authorization
from tastypie.authentication import BasicAuthentication
from tastypie_mongoengine.resources import MongoEngineResource
from tastypie.serializers import Serializer
from tastypie.resources import Resource
import logging
import sys


_LOG = logging.getLogger(__name__)

class RestSerializer(Serializer):
    """
    Class for overriding various aspects of the default Tastypie Serializer
    class.
    """

    def format_datetime(self, data):
        """
        By default, Tastypie's serializer serializes all datetime objects as
        naive (no timezone info).  I'm not sure why this is the case.

        There's a patch, but it has not been merged into master Tastypie:
        https://github.com/toastdriven/django-tastypie/commit/542d365d7d975a90c64c4c375257e5bc4b3b220a
        """
        return data.isoformat()

class SpliceServerResourceMod(SpliceServerResource):
    #
    # This feels a little ugly, unsure of better solution
    # ReportServer needs ability to set a db_alias setting on the SpliceServer model
    # We need Tastypie to use the ReportServer's version of SpliceServer so it respects db_alias if it's used
    # Tried to just override 'queryset', wasn't able to...then ran into next problem of the query for find_by_uuid()
    # needs to use same db_alias
    #
    class Meta:
        # Overriding queryset from base so that our db_alias and other settings are honored
        # from ReportServer
        resource_name = "spliceserver"
        queryset = SpliceServer.objects.all()
        authorization = Authorization()
        authentication = X509CertificateAuthentication(verification_ca=certs.get_splice_server_identity_ca_pem())
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get']

    def find_by_uuid(self, uuid):
        #
        # Need to be sure we are querrying same SpliceServer model instance as queryset above
        # Careful that SpliceServer here refers to report_server.sreport.models.SpliceServer and not
        # splice.common.models.SpliceServer
        #
        _LOG.info("report_server.sreport.api.SpliceServerResource::find_by_uuid(%s) SpliceServer=%s" % (uuid, SpliceServer))
        return SpliceServer.objects(uuid=uuid).first()


class ProductUsageResource(ProductUsageResource):

    def import_hook(self, product_usage):
        _LOG.info("called create_hook")
        items_not_imported, start_stop_time = import_util.import_data(product_usage,
                                                                      force_import=True
                                                                      )
        _LOG.info("items_not_imported length: " + str(len(items_not_imported)))
        for i in items_not_imported:
            thisDict = i.to_dict()
            thisItem = QuarantinedReportData(**thisDict)
            thisItem.save()

        return items_not_imported
    

class MarketingProductUsageResource(MarketingProductUsageResource):

    def create_hook(self, mkt_product_usage):
        # we don't want to save these to our DB, so we just return the object
        return mkt_product_usage

    def complete_hook(self, items):
        _LOG.info("called marketing import_hook with %s items" % (len(items)))
        not_imported = import_util.import_candlepin_data(items,
                                                        force_import=True)
        _LOG.info("items_not_imported length: " + str(len(not_imported)))
        for i in not_imported:
            thisDict = i.to_dict()
            thisItem.save()

        return not_imported

#
# Below is a 'hack' so we can test the API prior to running from RPM
# 
class MarketingProductUsageResourceDev(MarketingProductUsageResource):
    class Meta:
        from tastypie.authentication import Authentication
        from splice.common.deserializer import JsonGzipSerializer
        from splice.common.models import MarketingProductUsage
        queryset = MarketingProductUsage.objects.all()
        resource_name = "marketingproductusage"
        authorization = Authorization()
        authentication = Authentication()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get']
        serializer = JsonGzipSerializer()


class PoolResourceMod(PoolResource):
    class Meta(PoolResource.Meta):
        resource_name = "pool"


class ProductResourceMod(ProductResource):
    class Meta(ProductResource.Meta):
        resource_name = "product"


class RulesResourceMod(RulesResource):
    class Meta(RulesResource.Meta):
        resource_name = "rules"


class QuarantinedDataResource(Resource):

    class Meta:
        queryset = QuarantinedReportData.objects.all()
        authorization = Authorization()
        allowed_methods = ['get']

    def get_list(self, request, **kwargs):
        _LOG.info("QuarantinedDataResource::get_list() ")

        results = QuarantinedReportData.objects.all()
        response_data = {}
        response_data['list'] = results

        try:
            response = HttpResponse(utils.to_json(response_data))
        except:
            _LOG.error(sys.exc_info()[0])
            _LOG.error(sys.exc_info()[1])
            raise

        return response


class ComplianceDataResource(Resource):

    class Meta:
        queryset = ReportData.objects.all()
        authorization = Authorization()
        allowed_methods = ['get']

    def get_list(self, request, **kwargs):

        _LOG.info("ComplianceDataResource::get_list() ")

        response = views.system_fact_compliance(request)

        return response



class ReportMeterResource(MongoEngineResource):

    class Meta:
        queryset = ReportData.objects.all()
        allow_methods = ['post']

        # Make sure we always get back the representation of the resource back
        # on a POST.
        # always_return_data = True
        authorization = Authorization()
        authentication = BasicAuthentication()
        

    def post_list(self, request, **kwargs):
        user = request.user
        _LOG.info("%s called ReportResource::post_list()  " % (str(user)))

        response = meter_report(request)
        return response
    
class ReportSpaceResource(MongoEngineResource):

    class Meta:
        queryset = ReportData.objects.all()
        allow_methods = ['post']

        # Make sure we always get back the representation of the resource back
        # on a POST.
        # always_return_data = True
        authorization = Authorization()
        authentication = BasicAuthentication()
        

    def post_list(self, request, **kwargs):
        user = request.user
        _LOG.info("%s called ReportResource::post_list()  " % (str(user)))

        response = space_report(request)
        return response


class FilterResource(MongoEngineResource):

    class Meta:
        queryset = Filter.objects.all()
        authorization = Authorization()
        allowed_methods = ['get', 'post', 'delete']
        filtering = {
            'id': ['exact'],
        }
        


    def get(self, request, **kwargs):

        _LOG.info("FilterResource::get() ")
        user_filters = Filter.objects.filter(owner=str(request.user), **kwargs)

        response_data = {}
        response_data['filters'] = user_filters

        return utils.create_response(response_data)

    def post(self, request, **kwargs):
        _LOG.info("FilterResource::get() ")
        start, end = utils.get_dates_from_request(request)
        data = utils.data_from_post(request)
        
        start = "%s/%s/%s" % (start.month, start.day, start.year)
        end = "%s/%s/%s" % (end.month, end.day, end.year)
        filter_name = data["filter_name"]
        if 'org' in data:
            environment = data["org"]
        else:
            environment = "All"
    
        status = data["status"]
    
        filter = Filter(
            filter_name = filter_name,
            owner = user,
            status = status,
            environment = environment, 
            start_date = start,
            end_date = end
            )
        filter.save()
        
        
    def delete(self, request, id):
        _LOG.info("FilterResource::delete() ")
        user_filters = Filter.objects.filter(id=id)
        deleted = user_filters.delete()
        
        response_data = {}
        return utils.create_response(response_data) 
