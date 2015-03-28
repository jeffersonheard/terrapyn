$ ->
  wkt = new ol.format.WKT()
  extent = wkt.readGeometry DATA.extent, dataProjection: "EPSG:4326", featureProjection: "EPSG:3857"
  feature = new ol.Feature extent

  view = new ol.View
    center: [0,0]
    zoom: 2

  map = new ol.Map
    target: 'map'
    layers: [new ol.layer.Tile source: new ol.source.OSM()]
    view: view

  map.addControl new ol.control.FullScreen()

  featureOverlay = new ol.FeatureOverlay
    features: [feature]
    map: map

  view.fitGeometry(extent, map.getSize())