from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin

from terrapyn.geocms.models import *


admin.site.register(DirectoryEntry, PageAdmin)
admin.site.register(DataResource)
admin.site.register(Layer)
admin.site.register(Style)