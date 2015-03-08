# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geocms', '0003_auto_20150308_1000'),
    ]

    operations = [
        migrations.RenameField(
            model_name='layerordering',
            old_name='lyaer_collection',
            new_name='layer_collection',
        ),
    ]
