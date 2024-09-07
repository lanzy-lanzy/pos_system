from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class POSAdminSite(AdminSite):
    site_title = _('POS Admin')
    site_header = _('POS System Administration')
    index_title = _('Dashboard')

pos_admin_site = POSAdminSite(name='pos_admin')
