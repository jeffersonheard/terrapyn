# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('pages', '__first__'),
        ('geocms', '0002_auto_20150216_1805'),
    ]

    operations = [
        migrations.CreateModel(
            name='LayerCollection',
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
                ('associated_pages', models.ManyToManyField(related_name='layer_collections', null=True, to='pages.Page', blank=True)),
            ],
            options={
                'permissions': (('view_layercollection', 'View layer collection'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LayerOrdering',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('layer', models.ForeignKey(to='geocms.Layer')),
                ('lyaer_collection', models.ForeignKey(to='geocms.LayerCollection')),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='layercollection',
            name='layers',
            field=models.ManyToManyField(to='geocms.Layer', through='geocms.LayerOrdering'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layercollection',
            name='site',
            field=models.ForeignKey(editable=False, to='sites.Site'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='directoryentry',
            name='layers',
        ),
        migrations.RemoveField(
            model_name='directoryentry',
            name='resources',
        ),
        migrations.RemoveField(
            model_name='directoryentry',
            name='styles',
        ),
        migrations.AddField(
            model_name='dataresource',
            name='associated_pages',
            field=models.ManyToManyField(related_name='data_resources', null=True, to='pages.Page', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='associated_pages',
            field=models.ManyToManyField(related_name='layers', null=True, to='pages.Page', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='style',
            name='associated_pages',
            field=models.ManyToManyField(related_name='styles', null=True, to='pages.Page', blank=True),
            preserve_default=True,
        ),
    ]
