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


from __future__ import division
from datetime import datetime, timedelta
from splice.common import config
import logging
import json
import math
import os


_LOG = logging.getLogger(__name__)


def datespan_by_hour(startDate, endDate):
    return datespan(startDate, endDate)


def datespan_by_day(startDate, endDate):
    return datespan(startDate, endDate, delta=timedelta(days=1))


def get_datespan(startDate, endDate, product_config):
    if product_config['calculation'] == 'hourly':
        return datespan_by_hour(startDate, endDate)
    if product_config['calculation'] == 'daily':
        return datespan_by_day(startDate, endDate)
        
        
def datespan(startDate, endDate, delta=timedelta(hours=1)):
    currentDate = startDate
    count = 0
    last_month_days = 0
    hours_for_sub = {}
    total_hours = 0
    while currentDate < endDate:
        hours_for_sub[currentDate.month] = {}
        hours_for_sub[currentDate.month]['start'] = startDate
        if (currentDate + delta).month > currentDate.month:
            sub = count 
            hours_for_sub[currentDate.month]['hours_for_sub'] = sub
            hours_for_sub[currentDate.month]['end'] = currentDate
            count = 0
            startDate = currentDate + delta
        
        if currentDate.month == endDate.month:
            last_month_days += 1
            sub = last_month_days 
            hours_for_sub[currentDate.month]['hours_for_sub'] = sub
            hours_for_sub[currentDate.month]['end'] = currentDate
        
        if (currentDate + delta).month == 1 and currentDate.month == 12:
            _LOG.debug('plus delta= ' + str((currentDate + delta).month) + ', currentDate = ' + str(currentDate.month))
            sub = count 
            hours_for_sub[currentDate.month]['hours_for_sub'] = sub
            hours_for_sub[currentDate.month]['end'] = currentDate
            count = 0
            startDate = currentDate + delta
            
        count += 1
        currentDate += delta
    
    _LOG.debug(str(hours_for_sub))  
    for key, value in hours_for_sub.items():
        #if 'hours_for_sub' in value:
            #_LOG.debug(str(key) +  str(value['start']) + str(value['end']) +  str(value['hours_for_sub']))
        total_hours += value['hours_for_sub']
    _LOG.debug('total hours: ' + str(total_hours))
    return total_hours


def subscription_calc(count, start, end, product_config):
    if product_config['calculation'] == 'hourly':
        hours_for_sub = datespan_by_hour(start, end) 
    if product_config['calculation'] == 'daily':
        hours_for_sub = datespan_by_day(start, end) 
    
    nau = count / hours_for_sub
    nau = math.ceil(nau)
    return nau


def get_date_epoch(date):
    '''
    return python epoch time * 1000 for javascript 
    '''
    
    epoch = (int(date.strftime("%s")))
    return epoch


def get_date_object(epoch_int):
    '''
    return datetime object from epoch string
    '''
    date = datetime.utcfromtimestamp(int(epoch_int))
    return date


#################################################
# Helper Classes / Methods
#################################################

class MongoEncoder(json.JSONEncoder):
    """ JSON Encoder for Mongo Objects """
    
    def default(self, obj, **kwargs):
        #ObjectId works w/ fedora17 but fails w/ RHEL6
        #from pymongo.objectid import ObjectId
        import mongoengine
        import types
        if isinstance(obj, (mongoengine.Document, mongoengine.EmbeddedDocument)):
            out = dict(obj._data)
            for k,v in out.items():
                #if isinstance(v, ObjectId):
                _LOG.debug("k = %s, v = %s" % (k,v))
                out[k] = str(v)
            return out
        elif isinstance(obj, mongoengine.queryset.QuerySet):
            return list(obj)
        elif isinstance(obj, types.ModuleType):
            return None
        elif isinstance(obj, (list, dict)):
            return obj
        elif isinstance(obj, datetime):
            return str(obj)
        else:
            msg = ('object type not found, can not encode to JSON')
            _LOG.error(msg)
            raise Exception(msg)
    

def to_json(obj):
    return json.dumps(obj, cls=MongoEncoder, indent=2)


def read_rhn_conf():
    config_file = '/etc/rhn/rhn.conf'
    config_section = 'spacewalk'
    rhn_dict = {}
    keys = ['db_backend', 'db_user', 'db_password', 'db_name', 'db_host', 'db_port']
    if os.path.isfile(config_file):
        if not config.CONFIG.has_section(config_section):
            config.CONFIG.add_section(config_section)
        _LOG.info('found ' + config_file)
        file = open(config_file, 'r')
        for line in file:
            for key in keys:
                if key in line:
                    _LOG.debug(line)
                    value = line.split('=')[1].strip()
                    rhn_dict[key] = value
    for key, value in rhn_dict.items():
        #_LOG.info(str(key) + ':' + str(value))
        config.CONFIG.set(config_section, key, value)
                    
            
