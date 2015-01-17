import os
import re
import json
from django.conf import settings
import sh
import mapnik
import time
import logging

from terrapyn.geocms.cache import CacheManager
from terrapyn.geocms import models


_log = logging.getLogger('terrapyn.driver_messages')

LAYER_CACHE_PATH = getattr(settings, 'LAYER_CACHE_PATH')

if not os.path.exists(LAYER_CACHE_PATH):
    sh.mkdir('-p', LAYER_CACHE_PATH)


class Renderer(object):
    def compile_layer(self, rl, layer_id, srs, css_classes, **parameters):
        """Take a RenderedLayer and turn it into a Mapnik input file clause"""

        return {
            "id" : parameters['id'] if 'id' in parameters else re.sub('/', '_', layer_id),
            "name" : parameters['name'] if 'name' in parameters else re.sub('/', '_', layer_id),
            "class" : ' '.join(rl.default_class if 'default' else cls for cls in css_classes).strip(),
            "srs" : srs if isinstance(srs, basestring) else srs.ExportToProj4(),
            "Datasource" : parameters
        }

    def compile_mml(self, srs, styles, *layers):
        """Take multiple layers and stylesheets and turn it into a Mapnik input file"""
        stylesheets = models.Style.objects.filter(slug__in=[s.split('.')[0] for s in styles])
        css_classes = set([s.split('.')[1] if '.' in s else 'default' for s in styles])

        _log.debug('compile_mml {0}'.format(layers))

        mml = {
            'srs': srs,
            'Stylesheet': [{"id": re.sub('/', '_', stylesheet.slug), "data" : stylesheet.stylesheet } for stylesheet in stylesheets],
            'Layer': [self.compile_layer(rl, layer_id, lsrs, css_classes, **parms) for rl, (layer_id, lsrs, parms) in layers]
        }
        return mml

    def compile_mapfile(self, name, srs, stylesheets, *layers):
        """Compile from Carto to Mapnik"""

        _log.debug('compiling mapfile')
        with open(name + ".mml", 'w') as mapfile:
            mapfile.write(json.dumps(self.compile_mml(srs, stylesheets, *layers), indent=4))
        carto = sh.Command(settings.CARTO_HOME + "/bin/carto")
        carto(name + '.mml', _out=name + '.xml')
        _log.debug('compiled mapfile')

    def prepare_wms(self, layers, srs, styles, bgcolor=None, transparent=True, **kwargs):
        """Take a WMS query and turn it into the appropriate MML file, if need be.  Or look up the cached MML file"""
        _log.debug('prepare wms {0} {1}'.format(layers, styles))

        if not os.path.exists(LAYER_CACHE_PATH):
            os.makedirs(LAYER_CACHE_PATH)  # just in case it's not there yet.

        cached_filename = CacheManager.cache_entry_name(
            layers, srs, styles,
            bgcolor=bgcolor,
            transparent=transparent,
            query=kwargs['query'] if 'query' in kwargs else None
        )
        _log.debug('cache entry {0}'.format(cached_filename))

        layer_specs = []
        for layer in layers:
            if "#" in layer:
                layer, kwargs['sublayer'] = layer.split("#")
            _log.debug('pulling layer {0}'.format(layer))
            rendered_layer = models.Layer.objects.get(slug=layer)
            driver = rendered_layer.data_resource.driver_instance
            layer_spec = driver.get_rendering_parameters(**kwargs)
            layer_specs.append((rendered_layer, layer_spec))

        if not os.path.exists(cached_filename + ".xml"):  # not an else as previous clause may remove file.
            try:
                with open(cached_filename + ".lock", 'w') as w:
                     self.compile_mapfile(cached_filename, srs, styles, *layer_specs)
                os.unlink(cached_filename + ".lock")
            except sh.ErrorReturnCode_1, e:
                os.unlink(cached_filename + ".lock")
                raise RuntimeError(str(e.stderr))

        return cached_filename

    def render(self, fmt, width, height, bbox, srs, styles, layers, **kwargs):
        """Render a WMS request or a tile.  TODO - create an SQLite cache for this as well, based on hashed filename."""

        _log.debug('render called for {0}'.format(layers))
        if srs.lower().startswith('epsg'):
            if srs.endswith("900913") or srs.endswith("3857"):
                srs = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null"
            else:
                srs = "+init=" + srs.lower()

        name = self.prepare_wms(layers, srs, styles, **kwargs)
        filename = "{name}.{bbox}.{width}x{height}.{fmt}".format(
            name=name,
            bbox='_'.join(str(b) for b in bbox),
            width=width,
            height=height,
            fmt=fmt
        )

        _log.debug('waiting on lock')
        while os.path.exists(name + ".lock"):
            time.sleep(0.05)

        _log.debug('rendering {0}x{1} tile'.format(width, height))
        m = mapnik.Map(width, height)
        mapnik.load_map(m, (name + '.xml').encode('ascii'))
        m.zoom_to_box(mapnik.Box2d(*bbox))
        mapnik.render_to_file(m, filename, fmt)

        with open(filename) as tiledata:
            tile = buffer(tiledata.read())
        os.unlink(filename)

        return filename, tile
