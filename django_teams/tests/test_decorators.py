from time import sleep
import sys
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test.client import RequestFactory

from django_teams.decorators import teamify

class DecoratorTests(TestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.factory = RequestFactory()

    def test_can_import_without_errors(self):
        # If we can get this far, we passed this test
        pass

    def test_view(self):
        def view(request):
            pass
        teamify(view)
