import os

from terrapyn.geocms.tests.factories import *
import pytest


@pytest.fixture(scope="module", params=(
        {},
# time consuming        {'original_file': ContentFile(open('/home/docker/terrapyn_project/ga_resources/tests/data/cities.zip').read(), 'cities.zip')}
))
def ds(request):
    ret = DataResourceFactory.create(**request.param)
    @request.addfinalizer
    def teardown():
        if ret.resource_file != None and os.path.exists(ret.resource_file.name):
            os.unlink(ret.driver_instance.get_filename('sqlite'))
            ret.resource_file.delete()
            ret.original_file.delete()
        return ret

    return ret


@pytest.mark.django_db
def test_ready_data_resource(ds):
    drv = ds.driver_instance
    assert ds.metadata.all().count() > 0
    m = ds.metadata.all().first()
    assert m.native_bounding_box != None
    assert m.bounding_box != None
    assert m.three_d == False
    assert m.native_srs != None
    assert m.table != None
    assert m.last_change != None


@pytest.mark.django_db
def test_get_rendering_parameters(ds):
    drv = ds.driver_instance
    drv.get_rendering_parameters()


@pytest.mark.django_db
def test_get_data_fields(ds):
    drv = ds.driver_instance
    if ds.driver == 'spatialite':
        assert len(drv.get_data_fields()) > 0


@pytest.mark.django_db
def test_get_filename(ds):
    drv = ds.driver_instance
    assert ds.resource_file.name.endswith('sqlite')
    assert os.path.exists(drv.get_filename('sqlite'))


@pytest.mark.django_db
def test_get_data_for_point(ds):
    drv = ds.driver_instance
    drv.ready_data_resource()


@pytest.mark.django_db
def test_as_dataframe(ds):
    drv = ds.driver_instance
    drv.as_dataframe()


@pytest.mark.django_db
def test_summary(ds):
    drv = ds.driver_instance
    drv.summary()


