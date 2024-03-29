# Generated by Django 3.2.4 on 2021-08-13 04:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_aggregator', '0014_adviser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adviser',
            name='is_active',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='adviser',
            name='is_dept_adviser',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='adviser',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='data_aggregator.user'),
        ),
    ]
