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


import os

from splice.common import config
from report_server.settings import *

ROOT_URLCONF = 'dev.urls'

curr_dir = os.path.dirname(__file__)
source_dir = os.path.join(curr_dir, '..')
os.chdir(source_dir)

config_file = os.path.join(curr_dir, 'splice.conf')
config.init(config_file, reinit=True)

DUMP_DIR = os.path.join(curr_dir, 'db_dump')

TEMPLATE_DIRS = (
    os.path.join(source_dir, 'templates'),
)

TEMPLATE_DEBUG = True
