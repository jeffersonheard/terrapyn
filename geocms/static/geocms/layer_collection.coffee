$ ->
  wkt = new ol.format.WKT()
  extent = wkt.readGeometry LAYERS.extent
  view = new ol.View
    center: [0,0]
    zoom: 2

  makeLayer = (x) -> new ol.layer.Tile
    source: new ol.source.XYZ url: "#{x.url}{z}/{x}/{y}/"

  layers = (makeLayer(x) for x in LAYERS.layers)

  map = new ol.Map
    target: 'map'
    layers: [new ol.layer.Tile source: new ol.source.OSM()]
    view: view

  map.addLayer(l) for l in layers
  map.addControl new ol.control.FullScreen()

  view.fitGeometry(extent, map.getSize())