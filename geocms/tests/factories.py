import factory
from django.core.files.base import ContentFile
from django.contrib.auth.models import User, Group

from terrapyn.geocms import models


class GroupFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'group{0}'.format(n))

    class Meta:
        model = Group
        django_get_or_create = ('name',)


class RootUserFactory(factory.DjangoModelFactory):
    username = 'root'
    password = 'root'
    email = 'root@terrapyn.io'
    first_name = 'Jefferson'
    last_name = 'Heard'
    is_superuser = True

    class Meta:
        model = User


class GeneralUserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'person{0}@terrapyn.io'.format(n))
    password = 'person'
    email = factory.LazyAttribute(lambda a: '{0}@terrapyn.io'.format(a.username.lower()))
    first_name = factory.Sequence(lambda n: 'Person{0}'.format(n))
    last_name = 'Smith'


class DataResourceFactory(factory.DjangoModelFactory):
    title = 'Census Places'
    slug = 'census-places'
    original_file = ContentFile(open('/home/docker/terrapyn_project/terrapyn/geocms/tests/data/census-places.sqlite').read(), 'census-places.sqlite')
    description = 'This is a map of Census designated places'
    driver = 'terrapyn.geocms.drivers.spatialite'
    driver_config = {}

    class Meta:
        model = models.DataResource


class StyleFactory(factory.DjangoModelFactory):
    title = 'Default Style'
    slug = 'default-style'
    stylesheet = """
    .default {
        line-width: 1;
        line-color: #000;
        polygon-fill: #05f;
        marker-width: 3;
        marker-height: 3;
        marker-line-color: #000;
        marker-fill: #f50;
    }
    """
    class Meta:
        model = models.Style


class LayerFactory(factory.DjangoModelFactory):
    title = 'Census Places Layer'
    slug = 'census-places-layer'
    data_resource = factory.SubFactory(DataResourceFactory)
    default_style = factory.SubFactory(StyleFactory)

    @factory.post_generation
    def postgeneration(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        else:
            self.styles.add(self.default_style)

        if extracted:
            # A list of groups were passed in, use them
            for style in extracted:
                self.styles.add(style)

    class Meta:
        model = models.Layer


class CatalogPageFactory(factory.DjangoModelFactory):
    title = 'Root'
    owner = factory.SubFactory(RootUserFactory)
    public = True

    class Meta:
        model = models.CatalogPage

