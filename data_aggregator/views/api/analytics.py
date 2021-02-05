from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from data_aggregator.models import Assignment, Participation
from data_aggregator.serializers import ParticipationSerializer, \
    AssignmentSerializer

"""
Accounts API
"""


class AccountParticipationView(APIView):
    '''
    API endpoint returning participation analytics for a account

    /api/[version]/account/[sis-account-id]/participation/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_account_id):
        queryset = (
            Participation.objects.select_related()
            .annotate(sis_account_id=F('course__sis_account_id'))
            .annotate(sis_term_id=F('week__term__sis_term_id'))
            .filter(sis_account_id__startswith=sis_account_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        serializer = ParticipationSerializer(queryset, many=True)
        return Response(serializer.data)


class AccountAssignmentView(APIView):
    '''
    API endpoint returning assignment analytics for a account

    /api/[version]/account/[sis-account-id]/assignment/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_account_id):
        queryset = (
            Assignment.objects.select_related()
            .annotate(sis_account_id=F('course__sis_account_id'))
            .annotate(sis_term_id=F('week__term__sis_term_id'))
            .filter(sis_account_id__startswith=sis_account_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        serializer = AssignmentSerializer(queryset, many=True)
        return Response(serializer.data)


class TermParticipationView(APIView):
    '''
    API endpoint returning participation analytics for a term

    /api/[version]/term/[sis-term-id]/participation/

    Endpoint accepts the following query parameters:
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_term_id):
        queryset = (
            Participation.objects.select_related()
            .annotate(sis_term_id=F('week__term__sis_term_id'))
            .filter(sis_term_id=sis_term_id))
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        serializer = ParticipationSerializer(queryset, many=True)
        return Response(serializer.data)


class TermAssignmentView(APIView):
    '''
    API endpoint returning assignment analytics for a term

    /api/[version]/term/[sis-term-id]/assignment/

    Endpoint accepts the following query parameters:
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_term_id):
        queryset = (
            Assignment.objects.select_related()
            .annotate(sis_term_id=F('week__term__sis_term_id'))
            .filter(sis_term_id=sis_term_id))
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)
        serializer = AssignmentSerializer(queryset, many=True)
        return Response(serializer.data)


class StudentParticipationView(APIView):
    '''
    API endpoint returning participation analytics for a term

    /api/[version]/student/[student-id]/participation/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, student_id):
        queryset = (
            Participation.objects.select_related()
            .annotate(sis_term_id=F('week__term__sis_term_id'))
            .filter(student_id=student_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        serializer = ParticipationSerializer(queryset, many=True)
        return Response(serializer.data)


class StudentAssignmentView(APIView):
    '''
    API endpoint returning assignment analytics for a term

    /api/[version]/student/[student-id]/assignment/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, student_id):
        queryset = (
            Assignment.objects.select_related()
            .annotate(sis_term_id=F('week__term__sis_term_id'))
            .filter(student_id=student_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        serializer = AssignmentSerializer(queryset, many=True)
        return Response(serializer.data)
