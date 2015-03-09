from rest_framework import generics
from mezzanine.pages.models import Page

from terrapyn.geocms import models
from terrapyn.geocms.api import serializers


class DataResourceList(generics.ListCreateAPIView):
    queryset = models.DataResource.objects.all()
    serializer_class = serializers.DataResourceSerializer


class DataResourceDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.DataResource.objects.all()
    serializer_class = serializers.DataResourceSerializer
    lookup_field = 'slug'
    
class StyleList(generics.ListCreateAPIView):
    queryset = models.Style.objects.all()
    serializer_class = serializers.StyleSerializer


class StyleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Style.objects.all()
    serializer_class = serializers.StyleSerializer
    lookup_field = 'slug'
    

class LayerList(generics.ListCreateAPIView):
    queryset = models.Layer.objects.all()
    serializer_class = serializers.LayerSerializer


class LayerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Layer.objects.all()
    serializer_class = serializers.LayerSerializer
    lookup_field = 'slug'


# class DirectoryEntryList(generics.ListCreateAPIView):
#     queryset = models.DirectoryEntry.objects.all()
#     serializer_class = serializers.DirectoryEntrySerializer
#
#
# class DirectoryEntryDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = models.DirectoryEntry.objects.all()
#     serializer_class = serializers.DirectoryEntrySerializer
#     lookup_field = 'slug'


class LayerCollectionList(generics.ListCreateAPIView):
    queryset = models.DirectoryEntry.objects.all()
    serializer_class = serializers.LayerCollectionSerializer


class LayerCollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.DirectoryEntry.objects.all()
    serializer_class = serializers.LayerCollectionSerializer
    lookup_field = 'slug'


class TerrapynPageList(generics.ListAPIView):
    queryset = Page.objects.all()
    serializer_class = serializers.PageSerializer


class TerrapynPageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Page.objects.all()
    serializer_class = serializers.PageSerializer
    lookup_field = 'slug'
