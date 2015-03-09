from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin

from terrapyn.geocms.models import *
from . import signals


class LayerOrderingInline(admin.TabularInline):
    model = LayerOrdering

class LayerCollectionAdmin(admin.ModelAdmin):
    inlines = [LayerOrderingInline]

admin.site.register(DirectoryEntry, PageAdmin)
admin.site.register(DataResource)
admin.site.register(Layer)
admin.site.register(LayerCollection, LayerCollectionAdmin)
admin.site.register(Style)