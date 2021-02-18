from data_aggregator.models import Course, User, Assignment, \
    Participation
from rest_framework import serializers


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['sis_course_id', 'canvas_course_id', 'short_name',
                  'long_name', 'canvas_account_id', 'sis_account_id',
                  'status']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['sis_user_id', 'canvas_user_id', 'login_id',
                  'first_name', 'last_name', 'full_name',
                  'sortable_name', 'short_name', 'email', 'status']


class AssignmentSerializer(serializers.ModelSerializer):
    sis_user_id = \
        serializers.CharField(source="user.sis_user_id", read_only=True)
    sis_course_id = \
        serializers.CharField(source="course.sis_course_id", read_only=True)
    week = serializers.IntegerField(source="week.week", read_only=True)
    sis_term_id = serializers.CharField(read_only=True)

    class Meta:
        model = Assignment
        fields = ['sis_user_id', 'assignment_id', 'title',
                  'unlock_at', 'points_possible', 'non_digital_submission',
                  'due_at', 'status', 'muted', 'min_score', 'max_score',
                  'first_quartile', 'median', 'third_quartile', 'excused',
                  'score', 'posted_at', 'submitted_at', 'sis_course_id',
                  'sis_term_id', 'week']


class ParticipationSerializer(serializers.ModelSerializer):
    sis_user_id = \
        serializers.CharField(source="user.sis_user_id", read_only=True)
    sis_course_id = \
        serializers.CharField(source="course.sis_course_id", read_only=True)
    week = serializers.IntegerField(source="week.week", read_only=True)
    sis_term_id = serializers.CharField(read_only=True)

    class Meta:
        model = Participation
        fields = ['sis_user_id', 'page_views', 'page_views_level',
                  'participations', 'participations_level', 'time_tardy',
                  'time_on_time', 'time_late', 'time_missing', 'time_floating',
                  'sis_course_id', 'sis_term_id', 'week']
