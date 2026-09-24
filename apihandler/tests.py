from django.test import TestCase
import json
from apihandler.models import (User, Domik, Apartment, UserApartment, Appeal, AppealHistory)

class ApiTestCase(TestCase):
    def setUp(self):
        self.login_url = "/api/v1/user/login"
        self.apartments_url = "/api/v1/user/apartments"
        self.appeals_url = "/api/v1/user/appeals"

        self.user = User.objects.create_user(max_id="test-user", name="test")
        self.domik = Domik.objects.create(address = "г Понск, улица Поновая, д 52")
        self.apartment = Apartment.objects.create(domik = self.domik, number="42", entrance="1")

    def login_user(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                "max_id": self.user.max_id,
                "name": self.user.name,
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

    def test_login_existing_user(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                "max_id": self.user.max_id,
                "name": self.user.name,
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["status"],
            "Такой пользователь уже существует",
        )

        self.assertEqual(
            data["id"],
            str(self.user.id),
        )

    def test_login_new_user(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                "max_id": "new-test-user",
                "name": "new-test",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            User.objects.filter(
                max_id="new-test-user"
            ).exists()
        )

    def test_add_apartment(self):
        self.login_user()

        response = self.client.post(
            self.apartments_url,
            data=json.dumps({
                "domik_id": str(self.domik.id),
                "number": "42",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(
            data["id"],
            str(self.apartment.id),
        )

        self.assertEqual(
            data["number"],
            "42",
        )

        self.assertEqual(
            data["role"],
            UserApartment.Role.RESIDENT,
        )

        self.assertTrue(
            UserApartment.objects.filter(
                user=self.user,
                apartment=self.apartment,
            ).exists()
        )

    def test_add_apartment_twice(self):
        self.login_user()

        payload = {
            "domik_id": str(self.domik.id),
            "number": "42",
        }

        response = self.client.post(
            self.apartments_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            self.apartments_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)

        self.assertEqual(
            UserApartment.objects.filter(
                user=self.user,
                apartment=self.apartment,
            ).count(),
            1,
        )

    def test_create_appeal(self):
        self.login_user()

        UserApartment.objects.create(
            user=self.user,
            apartment=self.apartment,
            role=UserApartment.Role.RESIDENT,
        )

        response = self.client.post(
            self.appeals_url,
            data=json.dumps({
                "apartment_id": str(self.apartment.id),
                "title": "Не работает лифт",
                "description": "Лифт не работает со вчера",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        appeal = Appeal.objects.get(
            id=data["id"]
        )

        self.assertEqual(
            appeal.author,
            self.user,
        )

        self.assertEqual(
            appeal.apartment,
            self.apartment,
        )

        self.assertEqual(
            appeal.domik,
            self.domik,
        )

        self.assertEqual(
            appeal.title,
            "Не работает лифт",
        )

        self.assertEqual(
            appeal.description,
            "Лифт не работает со вчера",
        )

        self.assertEqual(
            appeal.status,
            Appeal.Status.NEW,
        )

        history = AppealHistory.objects.get(
            appeal=appeal
        )

        self.assertEqual(
            history.status,
            Appeal.Status.NEW,
        )

        self.assertEqual(
            history.changed_by,
            self.user,
        )

    def test_create_foreign_appeal(self):
        self.login_user()

        another_user = User.objects.create_user(
            max_id="another-user",
            name="another-test",
        )

        UserApartment.objects.create(
            user=another_user,
            apartment=self.apartment,
            role=UserApartment.Role.RESIDENT,
        )

        response = self.client.post(
            self.appeals_url,
            data=json.dumps({
                "apartment_id": str(self.apartment.id),
                "title": "Чужая заявка",
                "description": "Описание",
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            Appeal.objects.count(),
            0,
        )



