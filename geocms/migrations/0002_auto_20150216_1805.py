# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import timedelta.fields


class Migration(migrations.Migration):

    dependencies = [
        ('geocms', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dataresource',
            options={'permissions': (('view_dataresource', 'View data resource'),)},
        ),
        migrations.AlterModelOptions(
            name='layer',
            options={'permissions': (('view_layer', 'View layer'),)},
        ),
        migrations.AlterModelOptions(
            name='resourcemetadata',
            options={'permissions': (('view_metadata', 'View data resource metadata'),)},
        ),
        migrations.AlterModelOptions(
            name='style',
            options={'permissions': (('view_style', 'View stylesheet'),)},
        ),
        migrations.AlterField(
            model_name='dataresource',
            name='refresh_every',
            field=timedelta.fields.TimedeltaField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
