# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test import TestCase


class TestNumbers(TestCase):

    def setUp(self):
        self.client.login(username='tk', password='2')

    def test_numbers_view(self):
        url = reverse("numbers_view")

        c = self.client.get(url)
        self.assertEqual(c.status_code, 200)


class TestTargets(TestCase):
    def test_targets_view(self):
        url = reverse("targets_view")

        c = self.client.get(url)
        self.assertEqual(c.status_code, 200)


class TestCashflow(TestCase):
    def test_cashflow_view(self):
        url = reverse("cashflow_view")

        c = self.client.get(url)
        self.assertEqual(c.status_code, 200)


class TestGroups(TestCase):

    def test_group_new(self):
        url = reverse("group_new")

        c = self.client.get(url)
        self.assertEqual(c.status_code, 200)

    def test_group_customer(self):
        url = reverse("customer_list")

        c = self.client.get(url)
        self.assertEqual(c.status_code, 200)

class TestCustomers(TestCase):

    def test_customers(self):
        url = reverse("customers")

        c = self.client.get(url)
        self.assertEqual(c.status_code, 200)
