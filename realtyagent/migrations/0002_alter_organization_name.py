# Generated by Django 4.2.1 on 2023-06-04 00:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('realtyagent', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Company name'),
        ),
    ]
