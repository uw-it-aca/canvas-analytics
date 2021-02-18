# Generated by Django 3.1 on 2021-01-20 21:32

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
                ('canvas_course_id', models.IntegerField()),
                ('sis_course_id', models.TextField(null=True)),
                ('short_name', models.TextField(null=True)),
                ('long_name', models.TextField(null=True)),
                ('canvas_account_id', models.IntegerField(null=True)),
                ('sis_account_id', models.TextField(null=True)),
                ('status', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_date_start', models.DateTimeField()),
                ('target_date_end', models.DateTimeField()),
                ('context', models.JSONField()),
                ('pid', models.IntegerField(null=True)),
                ('start', models.DateTimeField(null=True)),
                ('end', models.DateTimeField(null=True)),
                ('message', models.TextField()),
                ('created', models.DateField(auto_now_add=True)),
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
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('canvas_term_id', models.IntegerField()),
                ('sis_term_id', models.TextField(null=True)),
                ('year', models.IntegerField(null=True)),
                ('quarter', models.TextField(null=True)),
                ('label', models.TextField(null=True)),
                ('last_day_add', models.DateField(null=True)),
                ('last_day_drop', models.DateField(null=True)),
                ('first_day_quarter', models.DateField(null=True)),
                ('census_day', models.DateField(null=True)),
                ('last_day_instruction', models.DateField(null=True)),
                ('grading_period_open', models.DateTimeField(null=True)),
                ('aterm_grading_period_open', models.DateTimeField(null=True)),
                ('grade_submission_deadline', models.DateTimeField(null=True)),
                ('last_final_exam_date', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week', models.IntegerField()),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.term')),
            ],
        ),
        migrations.CreateModel(
            name='Participation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.IntegerField(null=True)),
                ('page_views', models.IntegerField(null=True)),
                ('page_views_level', models.IntegerField(null=True)),
                ('participations', models.IntegerField(null=True)),
                ('participations_level', models.IntegerField(null=True)),
                ('time_tardy', models.IntegerField(null=True)),
                ('time_on_time', models.IntegerField(null=True)),
                ('time_late', models.IntegerField(null=True)),
                ('time_missing', models.IntegerField(null=True)),
                ('time_floating', models.IntegerField(null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.course')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.job')),
                ('week', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.week')),
            ],
        ),
        migrations.AddField(
            model_name='job',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.jobtype'),
        ),
        migrations.AddField(
            model_name='course',
            name='term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.term'),
        ),
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assignment_id', models.IntegerField(null=True)),
                ('student_id', models.IntegerField(null=True)),
                ('score', models.IntegerField(null=True)),
                ('due_at', models.DateField(null=True)),
                ('points_possible', models.IntegerField(null=True)),
                ('status', models.TextField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.course')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.job')),
                ('week', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_aggregator.week')),
            ],
        ),
    ]
