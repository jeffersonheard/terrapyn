import sh
from django.conf import settings

from .factories import *
import pytest
from terrapyn.geocms import rendering


@pytest.fixture(scope="module")
def layer(request):
    ret = LayerFactory.create()
    @request.addfinalizer
    def teardown():
        sh.rm('-rf', settings.LAYER_CACHE_PATH)
    return ret

@pytest.mark.django_db
def test_render(layer):
    renderer = rendering.Renderer()
    filename, tile = renderer.render(
        'png',
        1024,
        512,
        [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
        'EPSG:3857',
        styles=[layer.default_style.slug],
        layers=[layer.slug],
    )

    assert filename is not None
    with open('tile.png', 'wb') as t:
        t.write(tile)
    assert len(tile) > 4096 # make sure there's stuff in the tile

