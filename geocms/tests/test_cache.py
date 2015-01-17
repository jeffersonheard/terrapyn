import sh
from django.conf import settings
import os

from .factories import *
import pytest
from terrapyn.geocms.cache import CacheManager


@pytest.fixture(scope="module")
def layer(request):
    ret = LayerFactory.create()
    @request.addfinalizer
    def teardown():
        sh.rm('-rf', settings.LAYER_CACHE_PATH)
    return ret

@pytest.mark.django_db
def test_fetch_tile(layer):
    mgr = CacheManager.get()
    filename = mgr.cache_entry_name(styles=[layer.default_style.slug],
        layers=[layer.slug])
    if os.path.exists(filename + '.mbtiles'):
        os.unlink(filename + '.mbtiles')

    cc = mgr.get_tile_cache(
        styles=[layer.default_style.slug],
        layers=[layer.slug],
    )
    rendered, tile = cc.fetch_tile(0, 0, 0)
    assert rendered
    rendered, tile = cc.fetch_tile(0, 0, 0)
    assert not rendered

    with open('test_fetch_tile.0.0.0.png', 'wb') as output:
        output.write(tile)

    rendered, tile = cc.fetch_tile(1, 0, 0)
    with open('test_fetch_tile.1.0.0.png', 'wb') as output:
        output.write(tile)

    rendered, tile = cc.fetch_tile(1, 1, 1)
    with open('test_fetch_tile.1.1.1.png', 'wb') as output:
        output.write(tile)

    rendered, tile = cc.fetch_tile(2, 0, 0)
    with open('test_fetch_tile.2.0.0.png', 'wb') as output:
        output.write(tile)

    rendered, tile = cc.fetch_tile(2, 1, 1)
    with open('test_fetch_tile.2.1.1.png', 'wb') as output:
        output.write(tile)

    rendered, tile = cc.fetch_tile(2, 2, 2)
    with open('test_fetch_tile.2.2.2.png', 'wb') as output:
        output.write(tile)

@pytest.mark.django_db
def test_remove_caches_for_style(layer):
    pass

@pytest.mark.django_db
def test_remove_caches_for_layer(layer):
    pass

@pytest.mark.django_db
def test_shave_cache(layer):
    pass

@pytest.mark.django_db
def test_seed_tiles(layer):
    pass


