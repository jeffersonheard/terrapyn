from django.conf.urls import patterns, url

from terrapyn.geocms import views, api

urlpatterns = patterns('',
    url(r'^wms/', views.WMS.as_view(), name='wms'),
    url(r'^tms/(?P<layer>.*)/(?P<z>[0-9]+)/(?P<x>[0-9]+)/(?P<y>[0-9]+)/', views.tms, name='tms'),
    url(r'^wfs/', views.WFS.as_view(), name='wfs'),
    url(r'^download/(?P<slug>.*)$', views.download_file, name='download-original'),

    # Data API

    url(r'^q/new/', views.create_dataset),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/schema/', views.schema),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/full_schema/', views.full_schema),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/query/(?P<x1>[0-9\-.]+),(?P<y1>[0-9\-.]+),(?P<x2>[0-9\-.]+),(?P<y2>[0-9\-.]+)(?P<srid>;[0-9]+)?/',
        views.query),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/query/', views.query),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/add_column/', views.add_column),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid>[0-9]+)/', views.CRUDView.as_view()),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid_start>[0-9]+):(?P<ogc_fid_end>[0-9]+)/', views.CRUDView.as_view()),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid_start>[0-9]+),(?P<limit>[0-9]+)/', views.CRUDView.as_view()),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/fork/', views.derive_dataset),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/fork_geometry/', views.create_dataset_with_parent_geometry),
    url(r'^q/(?P<slug>[a-z0-9\-/]+)/', views.CRUDView.as_view()),

    # Terrapyn Model REST API

    url(r'api/data-resource/$', api.DataResourceList.as_view(), name='data-resource-list'),
    url(r'api/data-resource/(?P<slug>[a-z0-9\-/]+)/$', api.DataResourceDetail.as_view(), name='data-resource-detail'),
    url(r'api/style/$', api.StyleList.as_view(), name='style-list'),
    url(r'api/style/(?P<slug>[a-z0-9\-/]+)/$', api.StyleDetail.as_view(), name='style-detail'),
    url(r'api/layer/$', api.LayerList.as_view(), name='layer-list'),
    url(r'api/layer/(?P<slug>[a-z0-9\-/]+)/$', api.LayerDetail.as_view(), name='layer-detail'),
)
