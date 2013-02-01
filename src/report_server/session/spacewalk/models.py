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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.sessions.models import SessionManager

    
class WebCustomer(models.Model): 
    
    id = models.DecimalField(primary_key=True, unique=True, decimal_places=0, max_digits=10)
    name = models.CharField(unique=True, max_length=128)
    staging_content_enabled = models.CharField(max_length=1)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    class Meta:
        db_table = u'web_customer'

class WebContact(models.Model):
    
    id = models.DecimalField(primary_key=True, decimal_places=0, max_digits=10)
    org = models.ForeignKey(WebCustomer)
    login = models.CharField(max_length=64)
    login_uc = models.CharField(unique=True, max_length=64)
    password = models.CharField(max_length=38)
    old_password = models.CharField(max_length=38, blank=True)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    oracle_contact_id = models.DecimalField(unique=True, null=True, max_digits=10, decimal_places=0, blank=True)
    ignore_flag = models.CharField(max_length=1)
    class Meta:
        db_table = u'web_contact'


class Session(models.Model):
    """
    Django provides full support for anonymous sessions. The session
    framework lets you store and retrieve arbitrary data on a
    per-site-visitor basis. It stores data on the server side and
    abstracts the sending and receiving of cookies. Cookies contain a
    session ID -- not the data itself.

    The Django sessions framework is entirely cookie-based. It does
    not fall back to putting session IDs in URLs. This is an intentional
    design decision. Not only does that behavior make URLs ugly, it makes
    your site vulnerable to session-ID theft via the "Referer" header.

    For complete documentation on using Sessions in your code, consult
    the sessions documentation that is shipped with Django (also available
    on the Django Web site).
    """
    session_key = models.CharField(_('session key'), max_length=40,
                                   primary_key=True)
    session_data = models.TextField(_('session data'))
    expire_date = models.DateTimeField(_('expire date'), db_index=True)
    web_user = models.ForeignKey(WebContact, null=True, blank=True)
    objects = SessionManager()

    class Meta:
        db_table = 'django_session'
        verbose_name = _('session')
        verbose_name_plural = _('sessions')

    def get_decoded(self):
        return SessionStore().decode(self.session_data)
    



    
class Pxtsessions(models.Model):
    id = models.DecimalField(max_digits=10, decimal_places=10, primary_key=True)
    web_user = models.ForeignKey(WebContact, null=True, blank=True)
    expires = models.DecimalField(max_digits=10, decimal_places=10)
    value = models.CharField(max_length=4000)
    class Meta:
        db_table = u'pxtsessions'
        

# At bottom to avoid circular import
# this may need to be enabled and fixed.. not sure yet
#from report_server.session.spacewalk.db import SessionStore
from django.contrib.sessions.backends.db import SessionStore
