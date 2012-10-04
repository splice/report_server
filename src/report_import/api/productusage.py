# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


from django.template.response import TemplateResponse

from tastypie.authorization import Authorization
from tastypie import http
from tastypie.resources import Resource, ModelResource
from tastypie_mongoengine.resources import MongoEngineResource
from tastypie.utils import dict_strip_unicode_keys

from bson.json_util import loads

from sreport.models import ProductUsage, SpliceServer

class ProductUsageResource(MongoEngineResource):

    class Meta:
        queryset = ProductUsage.objects.all()
        authorization = Authorization()


    def post_list(self, request, **kwargs):
        import epdb; epdb.st()  
        deserialized = self.deserialize(
            request, request.raw_post_data, 
            format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(
            request, deserialized)
        bundle = self.build_bundle(data=deserialized, request=request)

        product_usage = loads(request.raw_post_data)
        if isinstance(product_usage, dict):
            product_usage = [product_usage]

        pu_models = [ProductUsage._from_son(p) for p in product_usage]
        self.import_hook(pu_models)

        return http.HttpAccepted()

    def get_list(self, request, **kwargs):
        product_usage = ProductUsage.objects.all()
        results = self.import_hook(product_usage)
        response = TemplateResponse(request, 'import.html', {'list': results})
        return response

    def import_hook(self, product_usage):
        raise NotImplementedError

