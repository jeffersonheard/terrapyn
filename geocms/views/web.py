from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from terrapyn.geocms.models import DataResource, Layer, Style


class LayerPageView(TemplateView):
    template_name = 'terrapyn/geocms/layer.html'

    def get_context_data(self, **kwargs):
        ctx = super(LayerPageView, self).get_context_data(**kwargs)
        ctx['layer'] = get_object_or_404(Layer, slug=kwargs['slug'])
        ctx['res'] = ctx['layer'].data_resource
        ctx['metadata'] = ctx['res'].metadata.first()

        return ctx

class DataResourcePageView(TemplateView):
    template_name = 'terrapyn/geocms/res.html'

    def get_context_data(self, **kwargs):
        ctx = super(DataResourcePageView, self).get_context_data(**kwargs)
        ctx['res'] = get_object_or_404(DataResource, slug=kwargs['slug'])
        ctx['metadata'] = ctx['res'].metadata.first()
        ctx['summary'] = ctx['res'].driver_instance.summary()
        return ctx

class StylePageView(TemplateView):
    template_name = 'terrapyn/geocms/style.html'

    def get_context_data(self, **kwargs):
        ctx = super(StylePageView, self).get_context_data(**kwargs)
        ctx['style'] = get_object_or_404(Style, kwargs['slug'])
        ctx['layer'] = ctx['style'].default_for_layer.first()
        return ctx
