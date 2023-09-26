# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import unittest
from data_aggregator.views.api.analytics import AccountParticipationView, \
    AccountAssignmentView, TermParticipationView, TermAssignmentView, \
    UserView, UserParticipationView, UserAssignmentView
from data_aggregator.tests.view_utils import BaseViewTestCase
from mock import MagicMock


class AnalyticsAPITestCase(BaseViewTestCase):

    fixtures = ['data_aggregator/fixtures/mock_data/da_assignment.json',
                'data_aggregator/fixtures/mock_data/da_course.json',
                'data_aggregator/fixtures/mock_data/da_job.json',
                'data_aggregator/fixtures/mock_data/da_jobtype.json',
                'data_aggregator/fixtures/mock_data/da_participation.json',
                'data_aggregator/fixtures/mock_data/da_term.json',
                'data_aggregator/fixtures/mock_data/da_user.json',
                'data_aggregator/fixtures/mock_data/da_week.json']

    def mock_paginate(self, queryset):
        return queryset

    def mock_get_paginated_response(self, queryset):
        return queryset


class TestAccountParticipationView(AnalyticsAPITestCase):

    def test_get(self):
        view_inst = AccountParticipationView()
        view_inst.paginate_queryset = \
            MagicMock(side_effect=self.mock_paginate)
        view_inst.get_paginated_response = \
            MagicMock(side_effect=self.mock_get_paginated_response)

        request = self.get_get_request(
            'api/v1/account/uwcourse:seattle:arts-&-sciences:phil:phil/'
            'participation/')
        response = view_inst.get(
            request,
            version=1,
            sis_account_id="uwcourse:seattle:arts-&-sciences:phil:phil")
        self.assertEqual(len(response), 200)
        request = self.get_get_request(
            'api/v1/account/some:bad:course/'
            'participation/')
        response = view_inst.get(
            request,
            version=1,
            sis_account_id="some:bad:course")
        self.assertEqual(len(response), 0)


class TestAccountAssignmentView(AnalyticsAPITestCase):

    def test_get(self):
        view_inst = AccountAssignmentView()
        view_inst.paginate_queryset = \
            MagicMock(side_effect=self.mock_paginate)
        view_inst.get_paginated_response = \
            MagicMock(side_effect=self.mock_get_paginated_response)

        request = self.get_get_request(
            'api/v1/account/uwcourse:seattle:arts-&-sciences:phil:phil/'
            'assignment/')
        response = view_inst.get(
            request,
            version=1,
            sis_account_id="uwcourse:seattle:arts-&-sciences:phil:phil")
        self.assertEqual(len(response), 100)
        request = self.get_get_request(
            'api/v1/account/some:bad:course/'
            'assignment/')
        response = view_inst.get(
            request,
            version=1,
            sis_account_id="some:bad:course")
        self.assertEqual(len(response), 0)


class TestTermParticipationView(AnalyticsAPITestCase):

    def test_get(self):
        view_inst = TermParticipationView()
        view_inst.paginate_queryset = \
            MagicMock(side_effect=self.mock_paginate)
        view_inst.get_paginated_response = \
            MagicMock(side_effect=self.mock_get_paginated_response)

        request = self.get_get_request(
            '/api/v1/term/2013-spring/participation/')
        response = view_inst.get(
            request,
            version=1,
            sis_term_id="2013-spring")
        self.assertEqual(len(response), 200)
        request = self.get_get_request(
            '/api/v1/term/2010-summer/'
            'participation/')
        response = view_inst.get(
            request,
            version=1,
            sis_term_id="2010-summer")
        self.assertEqual(len(response), 0)


class TestTermAssignmentView(AnalyticsAPITestCase):

    def test_get(self):
        view_inst = TermAssignmentView()
        view_inst.paginate_queryset = \
            MagicMock(side_effect=self.mock_paginate)
        view_inst.get_paginated_response = \
            MagicMock(side_effect=self.mock_get_paginated_response)

        request = self.get_get_request(
            '/api/v1/term/2013-spring/assignment/')
        response = view_inst.get(
            request,
            version=1,
            sis_term_id="2013-spring")
        self.assertEqual(len(response), 100)
        request = self.get_get_request(
            '/api/v1/term/2010-summer/'
            'assignment/')
        response = view_inst.get(
            request,
            version=1,
            sis_term_id="2010-summer")
        self.assertEqual(len(response), 0)


class TestUserView(AnalyticsAPITestCase):

    def test_get(self):
        view_inst = UserView()
        view_inst.paginate_queryset = \
            MagicMock(side_effect=self.mock_paginate)
        view_inst.get_paginated_response = \
            MagicMock(side_effect=self.mock_get_paginated_response)

        request = self.get_get_request('/api/v1/user/')
        response = view_inst.get(
            request,
            version=1)
        self.assertEqual(len(response), 21)
        request = self.get_get_request('/api/v1/user/')
        request.GET = {"has_analytics": "false"}
        response = view_inst.get(
            request,
            version=1)
        self.assertEqual(len(response), 1)
        request = self.get_get_request('/api/v1/user/')
        request.GET = {"has_analytics": "true"}
        response = view_inst.get(
            request,
            version=1)
        self.assertEqual(len(response), 20)


class TestUserParticipationView(AnalyticsAPITestCase):

    def test_get(self):
        view_inst = UserParticipationView()
        view_inst.paginate_queryset = \
            MagicMock(side_effect=self.mock_paginate)
        view_inst.get_paginated_response = \
            MagicMock(side_effect=self.mock_get_paginated_response)
        request = self.get_get_request(
            '/api/v1/user/896C60D888F54DDFBB54E91D12401BF2/participation/')

        # all terms
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 10)
        # term filter
        request.GET = {"sis_term_id": "2013-spring"}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 10)
        request.GET = {"sis_term_id": "2021-summer"}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        # week filter
        request.GET = {"week": 1}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        request.GET = {"week": 2}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        weeks_with_partic = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        for week in weeks_with_partic:
            request.GET = {"week": week}
            response = view_inst.get(
                request,
                version=1,
                sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
            self.assertEqual(len(response), 1)
        # term and week filter
        request.GET = {"sis_term_id": "2013-spring", "week": 2}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        weeks_with_partic = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        for week in weeks_with_partic:
            request.GET = {"sis_term_id": "2013-spring", "week": week}
            response = view_inst.get(
                request,
                version=1,
                sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
            self.assertEqual(len(response), 1)
        # bad endpoint
        request = self.get_get_request(
            '/api/v1/user/0000000000000-BAD-00000000000000/participation/')
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="0000000000000-BAD-00000000000000")
        self.assertEqual(len(response), 0)


class TestUserAssignmentView(AnalyticsAPITestCase):

    def test_get(self):
        view_inst = UserAssignmentView()
        view_inst.paginate_queryset = \
            MagicMock(side_effect=self.mock_paginate)
        view_inst.get_paginated_response = \
            MagicMock(side_effect=self.mock_get_paginated_response)

        request = self.get_get_request(
            '/api/v1/user/896C60D888F54DDFBB54E91D12401BF2/assignment/')
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 5)
        # term filter
        request.GET = {"sis_term_id": "2013-spring"}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 5)
        request.GET = {"sis_term_id": "2021-summer"}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        # week filter
        request.GET = {"week": 1}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        request.GET = {"week": 2}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        request.GET = {"week": 3}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 1)
        # term and week filter
        request.GET = {"sis_term_id": "2013-spring", "week": 1}
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="896C60D888F54DDFBB54E91D12401BF2")
        self.assertEqual(len(response), 0)
        # bad endpoint
        request = self.get_get_request(
            '/api/v1/user/0000000000000-BAD-00000000000000/assignment/')
        response = view_inst.get(
            request,
            version=1,
            sis_user_id="0000000000000-BAD-00000000000000")
        self.assertEqual(len(response), 0)


if __name__ == "__main__":
    unittest.main()
