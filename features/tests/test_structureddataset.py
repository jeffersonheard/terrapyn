import pytest
from terrapyn.features import models

@pytest.fixture(scope="module")
def test_persons(request):
    test_persons = models.StructuredDataset.objects.create_dataset(
        models.GeometryField(name='location', kind='Point'),
        models.SimpleField(name='first_name', kind='text'),
        models.SimpleField(name='last_name', kind='text'),
        models.SimpleField(name='age', kind='int'),
        models.SimpleField(name='dob', kind='date'),
        models.SimpleField(name='properties', kind='json'),
        name='sds_test_persons',
    )

    @request.add_finalizer
    def teardown():
        test_persons.delete()
    return test_persons

@pytest.fixture(scope="module")
def test_persons_profiles(test_persons):
    test_persons_profiles = models.StructuredDataset.objects.create_dataset(
        models.ForeignKey(rel_dataset=test_persons),
        models.SimpleField(name='address1', kind='text'),
        models.SimpleField(name='address2', kind='text'),
        models.SimpleField(name='zip', kind='text'),
        models.SimpleField(name='phone', kind='text'),
        models.SimpleField(name='role', kind='text'),
        name='sds_test_persons_profiles'
    )
    return test_persons_profiles

@pytest.fixture(scope="module")
def test_restaurants(request):
    test_restaurants = models.StructuredDataset.objects.create_dataset()

@pytest.mark.django_db
def test_create_dataset_simple(test_persons):
    assert test_persons.primary_key == 'id'
    assert test_persons.dbms == 'default'
    assert test_persons.is_layer
    assert test_persons.geometry_fields.all().exists()
    assert test_persons.simple_fields.all().exists()

    with test_persons.get_cursor() as c:
        sql = """
        SELECT EXISTS(
        SELECT *
        FROM information_schema.tables
        WHERE
          table_name = '{table_name}'
        );
        """.format(table_name=test_persons.name)
        c.execute(sql)
        row = c.fetchall()
        assert row[0]


@pytest.mark.django_db
def test_create_dataset_fk(test_persons_profiles):
    assert test_persons_profiles in test_persons_profiles['test_persons_id'].rel_dataset.reverse_keys

@pytest.mark.django_db
def test_create_dataset_m2m(test_persons):
    raise NotImplemented

def test_create_user():
    raise NotImplemented

def test_delete_user():
    raise NotImplemented

def test_create_owned_dataset():
    raise NotImplemented

def test_add_simplefield():
    raise NotImplemented

def test_add_foreignkey():
    raise NotImplemented

def test_add_geographicfield():
    raise NotImplemented

def test_add_manytomany():
    raise NotImplemented

def test_drop_field():
    raise NotImplemented

def test_add_feature():
    raise NotImplemented

def test_delete_feature():
    raise NotImplemented

def test_feature_by_pk():
    raise NotImplemented

def test_features():
    raise NotImplemented

