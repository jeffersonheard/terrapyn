$ ->

  attributions = []

  if LAYER.attribution?
    attributions.append = new ol.Attribution html: "Tiles &copy; #{layer.attribution}"

  wkt = new ol.format.WKT()
  extent = wkt.readGeometry LAYER.extent, dataProjection: "EPSG:4326", featureProjection: "EPSG:3857"
  view = new ol.View
    center: [0,0]
    zoom: 2

  map = new ol.Map
    target: 'map'
    layers: [
      new ol.layer.Tile source: new ol.source.OSM()
      new ol.layer.Tile
        source: new ol.source.XYZ
          attributions: attributions
          url: "#{LAYER.url}{z}/{x}/{y}/" + if LAYER.style then "?styles=#{style}" else ""
    ]
    view: view

  map.addControl new ol.control.FullScreen()

  view.fitGeometry(extent, map.getSize())