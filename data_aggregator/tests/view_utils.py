# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.test.client import RequestFactory


def get_user(netid):
    try:
        user = User.objects.get(username=netid)
        return user
    except Exception:
        user = User.objects.create_user(
            netid, password=get_user_pass(netid))
        return user


def get_user_pass(netid):
    return 'pass'


class BaseViewTestCase(TestCase):

    def setUp(self):
        self.client = Client(HTTP_USER_AGENT='Mozilla/5.0')
        self._set_user('javerage')
        self._set_group('u_test_group')

    def _set_user(self, netid):
        get_user(netid)
        self.client.login(username=netid,
                          password=get_user_pass(netid))

    def _set_group(self, group):
        session = self.client.session
        session['samlUserdata'] = {'isMemberOf': [group]}
        session.save()

    def get_request(self, url, netid, group):
        self._set_user(netid)
        self._set_group(group)
        request = RequestFactory().get(url)
        request.user = get_user(netid)
        request.session = self.client.session
        return request

    def get_post_request(self, url, data=None):
        if data is None:
            data = {}
        factory = RequestFactory()
        factory.session = self.client.session
        request = factory.post(url, data,
                               content_type="application/json",
                               follow=True)
        return request

    def get_get_request(self, url, data=None):
        if data is None:
            data = {}
        factory = RequestFactory()
        factory.session = self.client.session
        request = factory.get(url, data,
                              content_type="application/json",
                              follow=True)
        return request
