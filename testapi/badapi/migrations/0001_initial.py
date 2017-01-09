# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='A',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=135)),
            ],
        ),
        migrations.CreateModel(
            name='AA',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=135)),
                ('a', models.ForeignKey(related_name='aa', to='badapi.A')),
            ],
        ),
        migrations.CreateModel(
            name='B',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=135)),
            ],
        ),
        migrations.CreateModel(
            name='BB',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=135)),
                ('b', models.ManyToManyField(related_name='bb', to='badapi.B')),
            ],
        ),
        migrations.CreateModel(
            name='C',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=135)),
            ],
        ),
    ]
