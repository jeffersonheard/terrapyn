import requests
import json


def _pipe_to_file(error_text, filename):
    with open(filename, 'w') as x:
        x.write(error_text)

    return "See http://127.0.0.1:8000/media/{0}".format(filename.split('/')[-1])

def _u(s, x=None):
    return 'http://127.0.0.1:8000/terrapyn/api/{0}/{1}'.format(
        s,
        (str(x)+'/') if x else ''
    )

def test_layer_api():
    result = requests.post(
        _u('data-resource'),
        files={ 'original_file': open('/home/docker/terrapyn_project/terrapyn/geocms/tests/data/census-places.sqlite') },
        data=dict(
            driver="terrapyn.geocms.drivers.spatialite",
            title='Census Places',
        ),
        headers={'Accept': 'application/json, text/plain'}
    )
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/resource-error.html')
    data_resource = result.json()
    assert data_resource is not None
    assert data_resource['slug'].startswith('census-places')

    result = requests.post(
        _u('style'),
        headers={'Accept': 'application/json, text/plain'},
        data = {
        "stylesheet": """
        .default {
            line-width: 1;
            line-color: #000;
            polygon-fill: #05f;
            marker-width: 3;
            marker-height: 3;
            marker-line-color: #000;
            marker-fill-color: #f50;
        }
        """,
        "title":"default-style",
        }
    )
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/style-error.html')
    stylesheet = result.json()
    assert stylesheet is not None
    assert stylesheet['slug'].startswith('default-style')
    
    result = requests.post(
        _u('layer'),
        headers={'Accept': 'application/json, text/plain'},
        data={
            "data_resource": data_resource['slug'],
            "default_style": stylesheet['slug'],
            "styles": [stylesheet['slug']],
            "title": "Census Places Layer"
        }
    )
    
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/layer-error.html')
    layer = result.json()
    assert layer is not None
    assert layer['slug'].startswith('census-places-layer')
    
    result = requests.delete(_u('layer', layer['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/layer-delete-error.html')
    result = requests.delete(_u('style', stylesheet['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/style-delete-error.html')
    result = requests.delete(_u('data-resource', data_resource['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/resource-delete-error.html')


def test_style_api():
    result = requests.post(
        _u('style'),
        headers={'Accept': 'application/json, text/plain'},
        data = {
        "stylesheet": """
        .default {
            line-width: 1;
            line-color: #000;
            polygon-fill: #05f;
            marker-width: 3;
            marker-height: 3;
            marker-line-color: #000;
            marker-fill-color: #f50;
        }
        """,
        "title":"default-style",
        }
    )
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/style-error.html')
    obj = result.json()
    assert obj is not None
    assert obj['slug'].startswith('default-style')

    result = requests.delete(_u('style', obj['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/post-error.html')

    



def test_resource_api():
    # create a resource
    result = requests.post(
        _u('data-resource'),
        files={ 'original_file': open('/home/docker/terrapyn_project/terrapyn/geocms/tests/data/census-places.sqlite') },
        data=dict(
            driver="terrapyn.geocms.drivers.spatialite",
            title='Census Places',
        ),
        headers={'Accept': 'application/json, text/plain'}
    )
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/resource-error.html')
    obj = result.json()
    assert obj is not None
    assert obj['slug'].startswith('census-places')

    # change the resourcein
    new_obj = dict(**obj)
    del new_obj['slug']
    del new_obj['original_file']
    del new_obj['last_change']
    del new_obj['last_refresh']
    del new_obj['next_refresh']
    del new_obj['bounding_box']
    del new_obj['import_log']
    new_obj['metadata_url'] = "http://metadata.com/x.xml"

    result = requests.put(
        _u('data-resource', obj['slug']),
        data=json.dumps(new_obj),
        headers={'Content-Type': 'application/json'}
    )
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/post-error.html')
    updated_obj = result.json()
    assert updated_obj is not None
    assert updated_obj['metadata_url'] is not None

    # delete the resource
    result = requests.delete(_u('data-resource', obj['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/post-error.html')





