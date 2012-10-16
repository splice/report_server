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


from django.conf.urls import patterns, include, url
from tastypie.api import Api

from report_import.api import productusage

v1_api = Api(api_name='v1')

# Resources
productusage_resource = productusage.ProductUsageResource()

v1_api.register(productusage_resource)

urlpatterns = patterns('',

    # API Resources
    url(r'^api/', include(v1_api.urls)),

)