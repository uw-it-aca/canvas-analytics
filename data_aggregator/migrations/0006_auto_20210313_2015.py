# Generated by Django 3.1.7 on 2021-03-13 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregator', '0005_auto_20210219_1804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='max_score',
            field=models.DecimalField(decimal_places=3, max_digits=13, null=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='min_score',
            field=models.DecimalField(decimal_places=3, max_digits=13, null=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='points_possible',
            field=models.DecimalField(decimal_places=3, max_digits=13, null=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='score',
            field=models.DecimalField(decimal_places=3, max_digits=13, null=True),
        ),
    ]