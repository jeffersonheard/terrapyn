import datetime
import pytest
from terrapyn.features import models
from django.contrib.auth import models as auth
from django.conf import settings
from django.db import connections

default_dbms = getattr(settings, 'TERRAPYN_DEFAULT_DATABASE', 'default')

# fixture for a "person" table.
@pytest.fixture(scope="test")
def persons(request):
    test_persons = models.StructuredDataset.objects.create_dataset(
        models.GeometryField(name='location', kind='Point'),
        models.SimpleField(name='first_name', kind='text', not_null=True),
        models.SimpleField(name='last_name', kind='text', not_null=True),
        models.SimpleField(name='email', kind='text', not_null=True),
        models.SimpleField(name='dob', kind='date'),
        models.SimpleField(name='properties', kind='json'),
        name='test_persons',
    )

    @request.add_finalizer
    def teardown():
        test_persons.delete()
    return test_persons

# fixture to test foreign key relations to the persons table
@pytest.fixture(scope="test")
def persons_profiles(persons):
    test_persons_profiles = models.StructuredDataset.objects.create_dataset(
        models.ForeignKey(rel_dataset=persons, name='person', reverse_name='profiles'),
        models.SimpleField(name='address1', kind='text'),
        models.SimpleField(name='address2', kind='text'),
        models.SimpleField(name='zip', kind='text'),
        models.SimpleField(name='phone', kind='text'),
        models.SimpleField(name='role', kind='text'),
        name='test_persons_profiles'
    )
    return test_persons_profiles

# fixture to allow tests of many-to-many relations
@pytest.fixture(scope="test")
def restaurants(request):
    test_restaurants = models.StructuredDataset.objects.create_dataset(
        models.SimpleField(name='name', kind='text'),
        models.GeometryField(name='location', kind='POINT', srid=4326),
        models.SimpleField(name='price_range', kind='int', default_value='1'),
        name='test_restaurants'
    )
    @request.add_finalizer
    def teardown():
        test_restaurants.delete()
    return test_restaurants

# fixture to allow tests of many-to-many through relations
@pytest.fixture(scope="test")
def ratings(test_persons, test_restaurants):
    test_ratings = models.StructuredDataset.objects.create_dataset(
        models.ForeignKey(rel_dataset=test_persons, name='person'),
        models.ForeignKey(rel_dataset=test_restaurants, name='restaurant'),
        models.SimpleField(name='rating', kind='float', default_value='2.5'),
        name='test_ratings'
    )
    return test_ratings

@pytest.fixture(scope="module")
def user(request):
    test_user = auth.User.objects.create_user('test_user')

    @request.add_finalizer
    def teardown():
        test_user.delete()
    return test_user

# tests

def _dataset_exists(dataset):
    with dataset.get_cursor() as c:
        sql = """
        SELECT EXISTS(
        SELECT *
        FROM information_schema.tables
        WHERE
          schema_name = '{schema_name}',
          table_name = '{table_name}'
        );
        """.format(
            table_name=dataset.name,
            schema_name=dataset.schema_name
        )
        c.execute(sql)
        row = c.fetchall()
    return row[0]

def _user_exists(user, dbms=default_dbms):
    with connections[dbms].get_cursor() as c:
        sql = """
        SELECT EXISTS(
        SELECT *
        FROM information_schema.tables
        WHERE
          schema_name = '{schema_name}'
        );
        """.format(
            schema_name=user.username
        )
        c.execute(sql)
        row = c.fetchall()
    return row[0]

@pytest.mark.django_db
def test_create_dataset_simple(persons):
    """Make sure that the persons dataset is setup correctly and the table was created."""
    assert persons.primary_key == 'id'
    assert persons.dbms == 'default'
    assert persons.is_layer
    assert persons.geometry_fields.all().exists()
    assert persons.simple_fields.all().exists()
    assert _dataset_exists(persons), 'dataset table not created'


@pytest.mark.django_db
def test_create_dataset_fk(persons_profiles):
    """Make sure that the profiles dataset is setup correctly and the relationship is established"""
    assert persons_profiles in persons_profiles['test_persons_id'].rel_dataset.reverse_keys

@pytest.mark.django_db
def test_create_dataset_m2m(persons, restaurants):
    """Create a new m2m relationships and make sure both datasets report them properly"""
    m2m = models.ManyToMany.create_m2m(dataset1=persons, dataset2=restaurants)

    assert m2m.to_dataset1_name == 'test_persons_set'
    assert m2m.to_dataset2_name == 'test_restaurants_set'
    assert m2m.reverse == True
    assert m2m in persons.relationships
    assert m2m in restaurants.relationships

    m2m.reverse = False
    m2m.save()
    assert m2m not in restaurants.relationships

    m2m.delete()
    assert not _dataset_exists(m2m), 'table not deleted'


@pytest.mark.django_db
def test_m2m_through(test_ratings):
    """Test that through relationships work okay"""
    assert 'test_persons_id' in test_ratings
    assert 'test_restaurants_id' in test_ratings

    m2m = models.ManyToMany.create_through(
        test_ratings,
        test_ratings['test_persons_id'],
        test_ratings['test_restaurants_id'],
    )
    assert m2m in persons.relationships
    assert m2m in restaurants.relationships

    m2m.delete()
    assert _dataset_exists(test_ratings)


def test_create_and_delete_user(user):
    models.StructuredDataset.create_user(user)
    assert _user_exists(user)

    models.StructuredDataset.delete_user(user)
    assert not _user_exists(user)

def test_create_owned_dataset(user):
    owned_dataset = models.StructuredDataset.objects.create_dataset(
        models.SimpleField(name='thingie', kind='int'),
        owner=user,
        name='owned_dataset'
    )
    assert _dataset_exists(owned_dataset)
    models.StructuredDataset.delete_user(user)
    assert not _dataset_exists(owned_dataset)


def test_add_simplefield(persons):
    age = models.SimpleField(dataset=persons, kind='int', name='age', default_value='24')
    persons.add(age)
    age.create_index()
    persons.drop(age)
        
def test_add_foreignkey(persons):
    profile2 = models.StructuredDataset.objects.create_dataset(
        models.SimpleField(name='address1', kind='text'),
        models.SimpleField(name='address2', kind='text'),
        models.SimpleField(name='zip', kind='text'),
        models.SimpleField(name='phone', kind='text'),
        models.SimpleField(name='role', kind='text'),
        name='test_persons_profile2'
    )
    persons_id = models.ForeignKey(rel_dataset=persons),
    profile2.add(persons_id)
    assert profile2 in persons.reverse_keys
    profile2.delete()

def test_add_geographicfield(persons):
    last_location = models.GeometryField(kind='Point', name='last_location', srid=4326, index=True, dimension=2)
    persons.add(last_location)
    persons.drop(last_location)

def test_add_manytomany(persons, restaurants):
    visited = models.ManyToMany.objects.create_m2m(
        persons,
        restaurants,
        to_dataset2_name='visited',
        reverse=False
    )

def test_add_feature(persons, person_profiles, restaurants):
    # add person
    p1 = persons.add_feature({
        'location': {'type': "Point", "coordinates": [-35, 79]},        
        'first_name': "Jefferson",
        'last_name': "Heard",
        'email': "jeff@terrahub.io",
        'dob': datetime.date(month=4, day=5, year=1979),
        'properties': {
            "company": "TerraHub",
            "role": "CEO",
            "founded": 2013
        }
    })
    
    
    # check to make sure person is in feature list
    assert 'id' in p1 and p1['id'] is not None
    
    # pull the feature collection for persons
    fc = persons.features()
    assert 'type' in fc and fc['type'] == 'FeatureCollection', "features is not a valid feature collection"
    assert 'features' in fc and p1['id'] in {f['id'] for f in fc['features']} 
    
    # add restaurant
    r1 = restaurants.add_feature({
        'name': 'City Beverage',
        'location':  {'type': "Point", "coordinates": [-35, 79]},
        'price_range': 2 
    })    
    
    # add m2m relationship
    models.ManyToMany.objects.add()
    # upsert p1 iwth r1 added as one of its restaurants
    # check feature result to make sure that it's listed
    # upsert p1 missing its location field
    # check to make sure location hasn't changed
    # upsert p1 making its location field null
    # check to make sure location is now null
    # check restaurant features and make suer persons are listed
    # add profile data for person
    # check to make sure that profiles

def test_delete_feature():
    raise NotImplemented

def test_feature_by_pk(persons, persons_profiles, restaurants, ratings):
    p1 = persons.add_feature({
        'location': {'type': "Point", "coordinates": [-35, 79]},        
        'first_name': "Jefferson",
        'last_name': "Heard",
        'email': "jeff@terrahub.io",
        'dob': datetime.date(month=4, day=5, year=1979),
        'properties': {
            "company": "TerraHub",
            "role": "CEO",
            "founded": 2013
        }
    })
    
    r1 = restaurants.add_feature({
        'name': 'City Beverage',
        'location':  {'type': "Point", "coordinates": [-35, 79]},
        'price_range': 2 
    })  
    
    # check to make sure person is in feature list
    assert 'id' in p1 and p1['id'] is not None
    fid = p1['id']
    
    # pull the feature collection for persons
    # make sure the feature we added is the same, but now has an id field
    # feature should now be this: 
    #
    # { "type": "Feature",
    #   "geometry": {'type': "Point", "coordinates": [-35, 79]},
    #   "properties": {
    #       "first_name": "Jefferson",
    #       "last_name": "Heard",
    #       "email": "jeff@terrahub.io",
    #       "dob": datetime.date(month=4, day=5, year=1979),
    #       "properties": {
    #           "company": "TerraHub",
    #           "role": "CEO",
    #           "founded": 2013
    #       }
    #       "profile": null
    #  }
    f = persons.feature(id)
    assert 'type' in f and f['type'] == 'Feature', "features is not a valid feature collection"
    assert 'properties' in f
    assert 'location' in f['properties'] 
    assert 'type' in f['location'] and f['location']['type'] == 'Point'
    assert 'coordinates' in f['location'] and f['location']['coordinates'][0] == -35 and f['location']['coordinates'][1] == -79
    assert 'first_name' in f['properties'] and f['properties']['first_name'] == 'Jefferson'
    assert 'last_name' in f['properties'] and f['properties']['last_name'] == 'Heard'
    assert 'properties' in f['properties'] and isinstance(f['properties'], dict)
    assert 'company' in f['properties']['properties']

    # now add a profile
    p1_profile = persons_profiles.add_feature({
        "person": p1,
        "address1": "3926 Swarthmore Rd",
        "zip": "27707",
        "role": "CEO, TerraHub LLC",
    })

    # pull the feature again, this time getting the profile
    #
    # Feature should be this:
    #
    # { "type": "Feature",
    #   "geometry": {'type': "Point", "coordinates": [-35, 79]},
    #   "properties": {
    #       "first_name": "Jefferson",
    #       "last_name": "Heard",
    #       "email": "jeff@terrahub.io",
    #       "dob": datetime.date(month=4, day=5, year=1979),
    #       "properties": {
    #           "company": "TerraHub",
    #           "role": "CEO",
    #           "founded": 2013
    #       },
    #       "profile": {
    #           "address1": "3926 Swarthmore Rd",
    #           "zip": "27707",
    #           "role": "CEO, TerraHub LLC"
    #       }
    #  }
    f = persons.feature(fid)
    
    # make sure that the profile exists, is not a list of profiles (since unique was set)
    assert 'profiles' in f['properties']
    assert isinstance(f['properties']['profiles'], dict)
    assert f['properties']['profiles']['id'] == p1_profile['id']
    
    # add a record on a many-to-many through relation
    m2m_thru = models.ManyToMany.objects.create_through(
        ratings, 
        key1=ratings['person'], 
        key2=ratings['restaurant'], 
        to_dataset1_name='restaurants', 
        reverse=False 
    )
    ratings.add_feature({
        'person': p1,
        'restaurant': r1,
        'rating': 5
    })

    # Grab feature again
    #
    # Feature should be this:
    #
    # { "type": "Feature",
    #   "geometry": {'type': "Point", "coordinates": [-35, 79]},
    #   "properties": {
    #       "first_name": "Jefferson",
    #       "last_name": "Heard",
    #       "email": "jeff@terrahub.io",
    #       "dob": datetime.date(month=4, day=5, year=1979),
    #       "properties": {
    #           "company": "TerraHub",
    #           "role": "CEO",
    #           "founded": 2013
    #       },
    #       "profile": {
    #           "address1": "3926 Swarthmore Rd",
    #           "zip": "27707",
    #           "role": "CEO, TerraHub LLC"
    #       }
    #       "ratings": [
    #           { "restaurant": {
    #               "type": "Feature",
    #               "geometry": {'type': "Point", "coordinates": [-35, 79]},
    #               "properties": {
    #                   'name': 'City Beverage',
    #                   'location':
    #                   'price_range': 2
    #               }
    #             },
    #             "rating": 5
    #           }
    #       ]
    #  }
    f = persons.feature(fid)

    
    m2m_thru.delete()
    
    
    
def test_features():
    p1 = persons.add_feature({
        'location': {'type': "Point", "coordinates": [-35, 79]},        
        'first_name': "Jefferson",
        'last_name': "Heard",
        'email': "jeff@terrahub.io",
        'dob': datetime.date(month=4, day=5, year=1979),
        'properties': {
            "company": "TerraHub",
            "role": "CEO",
            "founded": 2013
        }
    })
    
    # check to make sure person is in feature list
    assert 'id' in p1 and p1['id'] is not None
    
    # pull the feature collection for persons
    fc = persons.features()
    assert 'type' in fc and fc['type'] == 'FeatureCollection', "features is not a valid feature collection"
    assert 'features' in fc and p1['id'] in {f['id'] for f in fc['features']} 
    
