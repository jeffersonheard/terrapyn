# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields
from django.conf import settings
import timedelta.fields
import django_hstore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('sites', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL('create extension if not exists postgis;'),
        migrations.RunSQL('create extension if not exists hstore;'),

        migrations.CreateModel(
            name='CatalogPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('public', models.BooleanField(default=True)),
                ('edit_groups', models.ManyToManyField(related_name='group_editable_resources_catalogpage', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(related_name='editable_resources_catalogpage', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('owner', models.ForeignKey(related_name='owned_resources_catalogpage', to=settings.AUTH_USER_MODEL, null=True)),
                ('view_groups', models.ManyToManyField(related_name='group_viewable_resources_catalogpage', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(related_name='viewable_resources_catalogpage', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='DataResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('keywords_string', models.CharField(max_length=500, editable=False, blank=True)),
                ('title', models.CharField(max_length=500, verbose_name='Title')),
                ('slug', models.CharField(help_text='Leave blank to have the URL auto-generated from the title.', max_length=2000, null=True, verbose_name='URL', blank=True)),
                ('_meta_title', models.CharField(help_text='Optional title to be used in the HTML title tag. If left blank, the main title field will be used.', max_length=500, null=True, verbose_name='Title', blank=True)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('gen_description', models.BooleanField(default=True, help_text='If checked, the description will be automatically generated from content. Uncheck if you want to manually set a custom description.', verbose_name='Generate description')),
                ('created', models.DateTimeField(null=True, editable=False)),
                ('updated', models.DateTimeField(null=True, editable=False)),
                ('status', models.IntegerField(default=2, help_text='With Draft chosen, will only be shown for admin users on the site.', verbose_name='Status', choices=[(1, 'Draft'), (2, 'Published')])),
                ('publish_date', models.DateTimeField(help_text="With Published chosen, won't be shown until this time", null=True, verbose_name='Published from', blank=True)),
                ('expiry_date', models.DateTimeField(help_text="With Published chosen, won't be shown after this time", null=True, verbose_name='Expires on', blank=True)),
                ('short_url', models.URLField(null=True, blank=True)),
                ('in_sitemap', models.BooleanField(default=True, verbose_name='Show in sitemap')),
                ('original_file', models.FileField(null=True, upload_to=b'geographica_resources', blank=True)),
                ('resource_file', models.FileField(null=True, upload_to=b'geographica_resources', blank=True)),
                ('resource_url', models.URLField(null=True, blank=True)),
                ('metadata_url', models.URLField(null=True, blank=True)),
                ('metadata_xml', models.TextField(null=True, blank=True)),
                ('driver_config', django_hstore.fields.DictionaryField(null=True, blank=True)),
                ('metadata_properties', django_hstore.fields.DictionaryField(null=True, blank=True)),
                ('last_change', models.DateTimeField(auto_now=True, null=True)),
                ('last_refresh', models.DateTimeField(null=True, blank=True)),
                ('next_refresh', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('refresh_every', timedelta.fields.TimedeltaField(null=True, blank=True)),
                ('md5sum', models.CharField(max_length=64, null=True, blank=True)),
                ('bounding_box', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('import_log', models.TextField(null=True, blank=True)),
                ('driver', models.CharField(default=b'terrapyn.geocms.drivers.spatialite', max_length=255, choices=[(b'terrapyn.geocms.drivers.spatialite', b'Spatialite (universal vector)'), (b'terrapyn.geocms.drivers.shapefile', b'Shapefile'), (b'terrapyn.geocms.drivers.geotiff', b'GeoTIFF'), (b'terrapyn.geocms.drivers.postgis', b'PostGIS'), (b'terrapyn.geocms.drivers.kmz', b'Google Earth KMZ'), (b'terrapyn.geocms.drivers.ogr', b'OGR DataSource')])),
                ('big', models.BooleanField(default=False, help_text=b'Set this to be true if the dataset is more than 100MB')),
                ('site', models.ForeignKey(editable=False, to='sites.Site')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('keywords_string', models.CharField(max_length=500, editable=False, blank=True)),
                ('title', models.CharField(max_length=500, verbose_name='Title')),
                ('slug', models.CharField(help_text='Leave blank to have the URL auto-generated from the title.', max_length=2000, null=True, verbose_name='URL', blank=True)),
                ('_meta_title', models.CharField(help_text='Optional title to be used in the HTML title tag. If left blank, the main title field will be used.', max_length=500, null=True, verbose_name='Title', blank=True)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('gen_description', models.BooleanField(default=True, help_text='If checked, the description will be automatically generated from content. Uncheck if you want to manually set a custom description.', verbose_name='Generate description')),
                ('created', models.DateTimeField(null=True, editable=False)),
                ('updated', models.DateTimeField(null=True, editable=False)),
                ('status', models.IntegerField(default=2, help_text='With Draft chosen, will only be shown for admin users on the site.', verbose_name='Status', choices=[(1, 'Draft'), (2, 'Published')])),
                ('publish_date', models.DateTimeField(help_text="With Published chosen, won't be shown until this time", null=True, verbose_name='Published from', blank=True)),
                ('expiry_date', models.DateTimeField(help_text="With Published chosen, won't be shown after this time", null=True, verbose_name='Expires on', blank=True)),
                ('short_url', models.URLField(null=True, blank=True)),
                ('in_sitemap', models.BooleanField(default=True, verbose_name='Show in sitemap')),
                ('default_class', models.CharField(default=b'default', max_length=255)),
                ('data_resource', models.ForeignKey(to='geocms.DataResource')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('table', models.TextField()),
                ('last_change', models.DateTimeField(auto_now=True, null=True)),
                ('native_bounding_box', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('bounding_box', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('three_d', models.BooleanField(default=False)),
                ('native_srs', models.TextField(null=True, blank=True)),
                ('resource', models.ForeignKey(related_name='metadata', to='geocms.DataResource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Style',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('keywords_string', models.CharField(max_length=500, editable=False, blank=True)),
                ('title', models.CharField(max_length=500, verbose_name='Title')),
                ('slug', models.CharField(help_text='Leave blank to have the URL auto-generated from the title.', max_length=2000, null=True, verbose_name='URL', blank=True)),
                ('_meta_title', models.CharField(help_text='Optional title to be used in the HTML title tag. If left blank, the main title field will be used.', max_length=500, null=True, verbose_name='Title', blank=True)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('gen_description', models.BooleanField(default=True, help_text='If checked, the description will be automatically generated from content. Uncheck if you want to manually set a custom description.', verbose_name='Generate description')),
                ('created', models.DateTimeField(null=True, editable=False)),
                ('updated', models.DateTimeField(null=True, editable=False)),
                ('status', models.IntegerField(default=2, help_text='With Draft chosen, will only be shown for admin users on the site.', verbose_name='Status', choices=[(1, 'Draft'), (2, 'Published')])),
                ('publish_date', models.DateTimeField(help_text="With Published chosen, won't be shown until this time", null=True, verbose_name='Published from', blank=True)),
                ('expiry_date', models.DateTimeField(help_text="With Published chosen, won't be shown after this time", null=True, verbose_name='Expires on', blank=True)),
                ('short_url', models.URLField(null=True, blank=True)),
                ('in_sitemap', models.BooleanField(default=True, verbose_name='Show in sitemap')),
                ('legend', models.ImageField(height_field=b'legend_height', width_field=b'legend_width', null=True, upload_to=b'terrapyn.styles.legends', blank=True)),
                ('legend_width', models.IntegerField(null=True, blank=True)),
                ('legend_height', models.IntegerField(null=True, blank=True)),
                ('stylesheet', models.TextField()),
                ('site', models.ForeignKey(editable=False, to='sites.Site')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='layer',
            name='default_style',
            field=models.ForeignKey(related_name='default_for_layer', to='geocms.Style'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='site',
            field=models.ForeignKey(editable=False, to='sites.Site'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='styles',
            field=models.ManyToManyField(to='geocms.Style', null=True, blank=True),
            preserve_default=True,
        ),
    ]
