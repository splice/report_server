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

#__future__ import must be first
from __future__ import division
from report_server.sreport.models import ReportData
from report_server.common.utils import datespan
from report_server.common.utils import subscription_calc, get_datespan
from report_server.common.utils import get_date_epoch, get_date_object
from report_server.common.max import MaxUsage
import logging
import json


_LOG = logging.getLogger(__name__)


class Product_Def:

    @staticmethod
    def get_count(product,
                  rhic,
                  start,
                  end,
                  contract_number,
                  environment,
                  config):
        count_list = []
        product_config = config[product.name]
        
        results = generic_count(product,
                                rhic,
                                start,
                                end,
                                contract_number,
                                environment,
                                product_config)

        if(results['high_count']):
            count = results['high_count']
            compliant = results['compliant_high']
            filter_args_dict = results['filter_args_high']
            result_dict = build_result(product,
                                       rhic,
                                       start,
                                       end,
                                       contract_number,
                                       count,
                                       environment,
                                       product_config,
                                       compliant)
            result_dict['facts'] = results['facts_high']
            result_dict['filter_args_dict'] = json.dumps(filter_args_dict)
            count_list.append(result_dict)
        
        if(results['low_count']):
            count = results['low_count']
            compliant = results['compliant_low']
            filter_args_dict = results['filter_args_low']
            result_dict = build_result(product,
                                       rhic,
                                       start,
                                       end,
                                       contract_number,
                                       count,
                                       environment,
                                       product_config,
                                       compliant)
            result_dict['facts'] = results['facts_low']
            result_dict['filter_args_dict'] = json.dumps(filter_args_dict)
            
            count_list.append(result_dict)
        
        return count_list
    

def build_result(product,
                 rhic,
                 start,
                 end,
                 contract_number,
                 count,
                 environment,
                 product_config,
                 compliant):
    result_dict = {}
    hours_for_sub = get_datespan(start, end, product_config)
    nau = subscription_calc(count, start, end, product_config)
    
    result_dict['count'] = count
    result_dict['compliant'] = compliant
    result_dict['nau'] = "{0:.0f}".format(nau)
    result_dict['rhic'] = str(rhic.name)
    result_dict['product_name'] = product.name
    result_dict['engineering_id'] = str(product.engineering_ids)
    result_dict['contract_use'] = product.quantity
    result_dict['sla'] = product.sla
    result_dict['support'] = product.support_level
    result_dict['contract_id'] = contract_number
    result_dict['start'] = get_date_epoch(start)
    result_dict['end'] = get_date_epoch(end)
    result_dict['sub_hours'] = hours_for_sub
    result_dict['product_config'] = json.dumps(product_config)
    
    return result_dict
    

def generic_count(product,
                  rhic,
                  start,
                  end,
                  contract_number,
                  environment,
                  config):
    product_config = config
        
    # Generic parameters to filter on
    filter_args_dict = {'consumer_uuid': str(rhic.uuid), 
                        'product': product.engineering_ids,
                        'sla': product.sla,
                        'support': product.support_level,
                        'contract_id': contract_number}
    if environment != "All":
        filter_args_dict['environment'] = environment
    
    #add custom business rules
    filter_args_high = dict(filter_args_dict)
    filter_args_low = dict(filter_args_dict)
    facts_high = ""
    facts_low = ""
    
    for key, values in product_config.items():
        if key == 'calculation':
            continue
        if(values):
            filter_args_low[key + '__gt'] = values['low_gt'] 
            filter_args_low[key + '__lt'] = values['low_lt']
            facts_low += values['low_desc']
           
            filter_args_high[key + '__gt'] = values['high_gt']
            if values['high_lt'] == -1:
                _LOG.debug('-1, parameter will not be added to query')
            else:
                filter_args_high[key + '__lt'] = values['high_lt']
            facts_high += values['high_desc']
     
    compliant_high = False
    compliant_low = False
    if product_config['calculation'] == 'hourly':
       
        high = ReportData.objects.filter(date__gt=start,
                                         date__lt=end,
                                         **filter_args_high).count()
        low = ReportData.objects.filter(date__gt=start,
                                        date__lt=end,
                                        **filter_args_low).count()
        if high:
            compliant_high = MaxUsage.get_MCU_Compliant(start,
                                                         end,
                                                         filter_args_high,
                                                         product.name)
            
        if low:
            compliant_low = MaxUsage.get_MCU_Compliant(start,
                                                        end,
                                                        filter_args_low,
                                                        product.name)

    
    results = {'high_count': high,
               'facts_high': facts_high,
               'filter_args_high': filter_args_high,
               'compliant_high': compliant_high,
               'low_count': low,
               'facts_low': facts_low,
               'filter_args_low': filter_args_low,
               'compliant_low': compliant_low }
                                
    return results
