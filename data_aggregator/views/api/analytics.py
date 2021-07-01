# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.db.models import F
from django.utils.decorators import method_decorator
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import JSONRenderer
from uw_saml.decorators import group_required
from data_aggregator.models import Assignment, Participation, User
from data_aggregator.serializers import ParticipationSerializer, \
    AssignmentSerializer, UserSerializer

"""
Analytics API
"""


class AnalyticsResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 2500


@method_decorator(group_required(settings.DATA_AGGREGATOR_ACCESS_GROUP),
                  name='dispatch')
class BaseAnalyticsAPIView(GenericAPIView):

    renderer_classes = [JSONRenderer]
    pagination_class = AnalyticsResultsSetPagination

    def get_assignment_queryset(self):
        queryset = (
            Assignment.objects.select_related()
            .annotate(sis_account_id=F('course__sis_account_id'))
            .annotate(sis_term_id=F('week__term__sis_term_id'))
        )
        return queryset

    def get_participation_queryset(self):
        queryset = (
            Participation.objects.select_related()
            .annotate(sis_account_id=F('course__sis_account_id'))
            .annotate(sis_term_id=F('week__term__sis_term_id'))
        )
        return queryset


class AccountParticipationView(BaseAnalyticsAPIView):
    '''
    API endpoint returning participation analytics for a account

    /api/[version]/account/[sis-account-id]/participation/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_account_id):
        queryset = (
            self.get_participation_queryset()
            .filter(sis_account_id__startswith=sis_account_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = ParticipationSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class AccountAssignmentView(BaseAnalyticsAPIView):
    '''
    API endpoint returning assignment analytics for a account

    /api/[version]/account/[sis-account-id]/assignment/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_account_id):
        queryset = (
            self.get_assignment_queryset()
            .filter(sis_account_id__startswith=sis_account_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = AssignmentSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class TermParticipationView(BaseAnalyticsAPIView):
    '''
    API endpoint returning participation analytics for a term

    /api/[version]/term/[sis-term-id]/participation/

    Endpoint accepts the following query parameters:
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_term_id):
        queryset = (
            self.get_participation_queryset()
            .filter(sis_term_id=sis_term_id))
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = ParticipationSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class TermAssignmentView(BaseAnalyticsAPIView):
    '''
    API endpoint returning assignment analytics for a term

    /api/[version]/term/[sis-term-id]/assignment/

    Endpoint accepts the following query parameters:
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_term_id):
        queryset = (
            self.get_assignment_queryset()
            .filter(sis_term_id=sis_term_id))
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = AssignmentSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class UserView(GenericAPIView):

    renderer_classes = [JSONRenderer]
    pagination_class = AnalyticsResultsSetPagination

    def get(self, request, version):
        queryset = User.objects.select_related()
        canvas_user_id = request.GET.get("canvas_user_id")
        if (canvas_user_id):
            queryset = queryset.filter(canvas_user_id=canvas_user_id)
        has_analytics = request.GET.get("has_analytics")
        if (has_analytics):
            assign_analytic_users = Assignment.objects.values("user")
            partic_analytic_users = Participation.objects.values("user")
            if has_analytics.lower() == "true":
                queryset = queryset.filter(
                    id__in=assign_analytic_users)
                queryset = queryset.filter(
                    id__in=partic_analytic_users)
            elif has_analytics.lower() == "false":
                queryset = queryset.exclude(
                    id__in=assign_analytic_users)
                queryset = queryset.exclude(
                    id__in=partic_analytic_users)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = UserSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class UserParticipationView(BaseAnalyticsAPIView):
    '''
    API endpoint returning participation analytics for a particular user

    /api/[version]/user/[sis-user-id]/participation/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_user_id):
        queryset = (
            self.get_participation_queryset()
            .filter(user__sis_user_id=sis_user_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = ParticipationSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class UserAssignmentView(BaseAnalyticsAPIView):
    '''
    API endpoint returning assignment analytics for a particular user

    /api/[version]/user/[sis-user-id]/assignment/

    Endpoint accepts the following query parameters:
    * sis_term_id: limit results to a term
    * week: limit results to a week in term
    '''
    def get(self, request, version, sis_user_id):
        queryset = (
            self.get_assignment_queryset()
            .filter(user__sis_user_id=sis_user_id))
        sis_term_id = request.GET.get("sis_term_id")
        if sis_term_id:
            queryset = queryset.filter(sis_term_id=sis_term_id)
        week = request.GET.get("week")
        if week:
            queryset = queryset.filter(week__week=week)

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = AssignmentSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)
