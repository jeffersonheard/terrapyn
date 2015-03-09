from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
import json
from terrapyn.geocms.models import DataResource, Layer, Style, LayerCollection


class LayerPageView(TemplateView):
    template_name = 'terrapyn/geocms/layer.html'

    def get_context_data(self, **kwargs):
        ctx = super(LayerPageView, self).get_context_data(**kwargs)
        ctx['layer'] = get_object_or_404(Layer, slug=kwargs['slug'])
        ctx['res'] = ctx['layer'].data_resource
        ctx['metadata'] = ctx['res'].metadata.first()
        ctx['editable_obj'] = ctx['layer']

        return ctx


class LayerCollectionPageView(TemplateView):
    template_name = 'terrapyn/geocms/layer_collection.html'

    def get_context_data(self, **kwargs):
        ctx = super(LayerCollectionPageView, self).get_context_data(**kwargs)
        ctx['layer_collection'] = get_object_or_404(LayerCollection, slug=kwargs['slug'])
        ctx['editable_obj'] = ctx['layer_collection']

        extent = ctx['layer_collection'].layers.first().data_resource.metadata.first().bounding_box
        for l in ctx['layer_collection'].layers.all():
            extent = extent.union(l.data_resource.metadata.first().bounding_box)

        extent.transform(3857)
        ctx['layers_json'] = json.dumps({
            "extent": extent.wkt,
            "layers": [{
                "url": reverse('tms', kwargs={'layer': l.slug}),
                "title": l.title,
                "description": l.description
            } for l in ctx['layer_collection'].layers.all()]
        }, indent=4)

        return ctx


class DataResourcePageView(TemplateView):
    template_name = 'terrapyn/geocms/res.html'

    def get_context_data(self, **kwargs):
        ctx = super(DataResourcePageView, self).get_context_data(**kwargs)
        ctx['res'] = get_object_or_404(DataResource, slug=kwargs['slug'])
        ctx['metadata'] = ctx['res'].metadata.first()
        ctx['summary'] = ctx['res'].driver_instance.summary()
        ctx['editable_obj'] = ctx['res']
        return ctx


class StylePageView(TemplateView):
    template_name = 'terrapyn/geocms/style.html'

    def get_context_data(self, **kwargs):
        ctx = super(StylePageView, self).get_context_data(**kwargs)
        ctx['style'] = get_object_or_404(Style, slug=kwargs['slug'])
        ctx['layer'] = ctx['style'].default_for.first()
        ctx['editable_obj'] = ctx['style']
        return ctx
