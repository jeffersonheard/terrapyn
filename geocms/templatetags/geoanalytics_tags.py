from django.contrib.auth import REDIRECT_FIELD_NAME
from django.db.models import Model
from markdown import markdown
from mezzanine import template
from mezzanine.pages.models import Page
from django.template import Node
from django.core.exceptions import ImproperlyConfigured
from lxml import etree
from mezzanine.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from mezzanine.core.fields import RichTextField
from mezzanine.core.forms import get_edit_form

from terrapyn.geocms.utils import best_name


def is_editable(obj, request):
    """
    Returns ``True`` if the object is editable for the request. First
    check for a custom ``editable`` handler on the object, otherwise
    use the logged in user and check change permissions for the
    object's model.
    """
    if hasattr(obj, 'can_change'):
        return obj.can_change(request)
    else:
        slug = request.get_full_path()[1:-1]
        p = Page.objects.get(slug=slug)
        return p.can_change(request)


register = template.Library()

@register.filter(is_safe=True)
def contact(user):
    if not user:
        return "<strong>None</strong>"
    bn = best_name(user)
    email = user.email
    return '<a href="{email}">{bn}</a>'.format(**locals())

@register.filter(is_safe=True)
def md(value):
    return  markdown(value)