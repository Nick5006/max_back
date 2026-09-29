from decimal import Decimal

from django.db import IntegrityError, transaction

from apihandler.models import CapitalRepair, User, UserApartment, Vote

from .base import ApiTestCase


class UserManagerTests(ApiTestCase):
    def test_create_user_requires_max_id_and_name(self):
        with self.assertRaisesMessage(ValueError, "Нужен max_id"):
            User.objects.create_user(max_id="", name="Иван")
        with self.assertRaisesMessage(ValueError, "Нужно name"):
            User.objects.create_user(max_id="user", name="")

    def test_create_jkuser_sets_role_flags(self):
        org = self.create_org()
        user = User.objects.create_jkuser(
            max_id="uk",
            name="Сотрудник",
            management_org=org,
        )
        self.assertTrue(user.is_jk)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_sets_required_flags(self):
        user = User.objects.create_superuser(
            max_id="admin",
            name="Админ",
            password="password",
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_jk)
        self.assertTrue(user.check_password("password"))


class ModelInvariantTests(ApiTestCase):
    def test_only_one_primary_apartment_is_kept_for_user(self):
        user = self.create_user()
        domik = self.create_domik()
        first = self.create_apartment(domik, number="1")
        second = self.create_apartment(domik, number="2")
        first_link = self.link_apartment(user, first, is_primary=True)
        second_link = self.link_apartment(user, second, is_primary=True)

        first_link.refresh_from_db()
        second_link.refresh_from_db()
        self.assertFalse(first_link.is_primary)
        self.assertTrue(second_link.is_primary)

    def test_capital_repair_balance_is_collected_minus_spent(self):
        domik = self.create_domik()
        cr = CapitalRepair.objects.create(
            domik=domik,
            collected_total=Decimal("1000.50"),
            spent_total=Decimal("250.25"),
        )
        self.assertEqual(cr.balance, Decimal("750.25"))

    def test_vote_is_unique_per_poll_and_user(self):
        org = self.create_org()
        uk = self.create_user(
            max_id="uk",
            name="Сотрудник",
            is_jk=True,
            management_org=org,
        )
        user = self.create_user(max_id="resident")
        domik = self.create_domik(management_org=org)
        poll = self.create_poll(author=uk, domik=domik)
        first_choice, second_choice = list(poll.choices.all())
        Vote.objects.create(poll=poll, choice=first_choice, user=user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(poll=poll, choice=second_choice, user=user)
