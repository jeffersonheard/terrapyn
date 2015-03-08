# this should be used as the page processor for anything with pagepermissionsmixin
# page_processor_for(MyPage)(ga_resources.views.page_permissions_page_processor)
from mezzanine.pages.page_processors import processor_for

from terrapyn.geocms.models import DirectoryEntry


@processor_for(DirectoryEntry)
def catalog_page_processor(request, page):
    return {}