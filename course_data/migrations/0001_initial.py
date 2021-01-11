# Generated by Django 2.2.17 on 2021-01-11 18:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.IntegerField()),
                ('year', models.IntegerField()),
                ('quarter', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week', models.IntegerField()),
                ('pid', models.IntegerField(null=True)),
                ('start', models.DateTimeField(null=True)),
                ('end', models.DateTimeField(null=True)),
                ('message', models.TextField()),
                ('created', models.DateField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course_data.Course')),
            ],
        ),
        migrations.CreateModel(
            name='JobType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('assignment', 'AssignmentJob'), ('participation', 'ParticipationJob')], max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Participation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week', models.IntegerField()),
                ('page_views', models.IntegerField(null=True)),
                ('page_views_level', models.IntegerField(null=True)),
                ('participations', models.IntegerField(null=True)),
                ('participations_level', models.IntegerField(null=True)),
                ('time_tardy', models.IntegerField(null=True)),
                ('time_on_time', models.IntegerField(null=True)),
                ('time_late', models.IntegerField(null=True)),
                ('time_missing', models.IntegerField(null=True)),
                ('time_floating', models.IntegerField(null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course_data.Course')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course_data.Job')),
            ],
        ),
        migrations.AddField(
            model_name='job',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course_data.JobType'),
        ),
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week', models.IntegerField()),
                ('assignment_id', models.IntegerField(null=True)),
                ('student_id', models.IntegerField(null=True)),
                ('score', models.IntegerField(null=True)),
                ('due_at', models.DateField(null=True)),
                ('points_possible', models.IntegerField(null=True)),
                ('status', models.TextField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course_data.Course')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course_data.Job')),
            ],
        ),
        migrations.AddIndex(
            model_name='participation',
            index=models.Index(fields=['week'], name='course_data_week_88c168_idx'),
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['week'], name='course_data_week_f22c2e_idx'),
        ),
    ]
