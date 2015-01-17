from PIL import Image
from cStringIO import StringIO
import requests

import pytest


HOST = "http://127.0.0.1:8000/"

def _delete_layer(layer, stylesheet, data_resource):
    result = requests.delete(_u('layer', layer['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/layer-delete-error.html')
    result = requests.delete(_u('style', stylesheet['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/style-delete-error.html')
    result = requests.delete(_u('data-resource', data_resource['slug']))
    assert result.ok, _pipe_to_file(result.text, '/home/docker/terrapyn_project/terrapyn_project/static/media/resource-delete-error.html')

def _create_layer():
    result = requests.post(
        _u('data-resource'),
        files={ 'original_file': open('/home/docker/terrapyn_project/terrapyn/geocms/tests/data/census-places.sqlite') },
        data=dict(
            driver="terrapyn.geocms.drivers.spatialite",
            title='Census Places',
        ),
        headers={'Accept': 'application/json, text/plain'}
    )
    assert result.ok, _pipe_to_file(result.text, 'resource-error.html')
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
            marker-fill: #f50;
        }
        """,
        "title":"Default Style",
        }
    )
    assert result.ok, _pipe_to_file(result.text, 'style-error.html')
    stylesheet = result.json()
    assert stylesheet is not None
    assert stylesheet['slug'].startswith('default-style')
    assert stylesheet['stylesheet'] == """
        .default {
            line-width: 1;
            line-color: #000;
            polygon-fill: #05f;
            marker-width: 3;
            marker-height: 3;
            marker-line-color: #000;
            marker-fill: #f50;
        }
        """, stylesheet['stylesheet']

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
    assert result.ok, _pipe_to_file(result.text, 'layer-error.html')
    layer = result.json()
    assert layer is not None
    assert layer['slug'].startswith('census-places-layer')

    return layer, stylesheet, data_resource

@pytest.fixture(scope='module')
def layer_info(request):
    layer, stylesheet, data_resource = _create_layer()
    def fin():
        _delete_layer(layer, stylesheet, data_resource)

    request.addfinalizer(fin)
    return layer, stylesheet, data_resource


def _pipe_to_file(error_text, filename):
    with open("/home/docker/terrapyn_project/terrapyn_project/static/media/" + filename, 'w') as x:
        x.write(error_text)

    return "See http://127.0.0.1:8000/media/{0}".format(filename.split('/')[-1])

def _u(s, x=None):
    return 'http://127.0.0.1:8000/terrapyn/api/{0}/{1}'.format(
        s,
        (str(x)+'/') if x else ''
    )

def test_anonymous_tms(layer_info):
    layer, stylesheet, data_resource = layer_info

    t000 = requests.get('{HOST}terrapyn/tms/{slug}/0/0/0/'.format(HOST=HOST, slug=layer['slug']))
    assert t000.status_code == requests.codes.ok, _pipe_to_file(t000.text, 't000.html')
    t000 = t000.content

    t100 = requests.get('{HOST}terrapyn/tms/{slug}/1/0/0/'.format(HOST=HOST, slug=layer['slug']))
    assert t100.status_code == requests.codes.ok, _pipe_to_file(t100.text, 't100.html')
    t100 = t100.content

    t111 = requests.get('{HOST}terrapyn/tms/{slug}/1/1/1/'.format(HOST=HOST, slug=layer['slug']))
    assert t111.status_code == requests.codes.ok, _pipe_to_file(t111.text, 't111.html')
    t111 = t111.content

    t200 = requests.get('{HOST}terrapyn/tms/{slug}/2/0/0/'.format(HOST=HOST, slug=layer['slug']))
    assert t200.status_code == requests.codes.ok, _pipe_to_file(t200.text, 't200.html')
    t200 = t200.content

    t211 = requests.get('{HOST}terrapyn/tms/{slug}/2/1/1/'.format(HOST=HOST, slug=layer['slug']))
    assert t211.status_code == requests.codes.ok, _pipe_to_file(t211.text, 't211.html')
    t211 = t211.content

    t222 = requests.get('{HOST}terrapyn/tms/{slug}/2/2/2/'.format(HOST=HOST, slug=layer['slug']))
    assert t222.status_code == requests.codes.ok, _pipe_to_file(t222.text, 't222.html')
    t222 = t222.content

    try:
        Image.open(StringIO(t000))
    except:
        print t000
        assert False, _pipe_to_file(t000, 't000.png')

    try:
        Image.open(StringIO(t111))
    except:
        print t111
        assert False, _pipe_to_file(t111, 't111.png')

    try:
        Image.open(StringIO(t200))
    except:
        print t200
        assert False, _pipe_to_file(t200, 't200.png')

    try:
        Image.open(StringIO(t211))
    except:
        print t211
        assert False, _pipe_to_file(t211, 't211.png')

    try:
        Image.open(StringIO(t222))
    except:
        print t222
        assert False, _pipe_to_file(t222, 't222.png')


def test_wms_getcapabilities(layer_info):
    rsp = requests.get('{host}terrapyn/wms/'.format(host=HOST), params={
        'request': 'GetCapabilities',
        'version': '1.1.0',
        'service': 'WMS'
    })

    assert rsp.status_code == requests.codes.ok, _pipe_to_file(rsp.text, 'wms_getcapabilites.html')

def test_wms_getmap(layer_info):
    rsp = requests.get('{host}terrapyn/wms/ '.format(host=HOST), params={
        'request': 'GetMap',
        'version': '1.1.0',
        'service': 'WMS',
        'bbox' : '-180,-90,180,90',
        'srs' : 'EPSG:4326',
        'layers' : layer_info[0]['slug'],
        'styles' : layer_info[1]['slug'],
        'width': 512,
        'height': 512
    }, stream=True)

    assert rsp.status_code == requests.codes.ok, _pipe_to_file(rsp.text, 'wms_getmap.html')

    try:
        Image.open(StringIO(rsp.content)) # should raise an exception if it fails
    except:
        assert False, _pipe_to_file(rsp.content, 't000.png')

def test_wms_getfeatureinfo(layer_info):
    pass
