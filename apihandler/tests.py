import uuid

from django.test import TestCase
import json
from apihandler.models import (User, Domik, Apartment, UserApartment, Appeal, AppealHistory, ManagementOrganization,
                               JKDomik)

class UserApiTestCase(TestCase):
    def setUp(self):
        self.login_url = "/api/v1/login"
        self.me_url = "/api/v1/me"
        self.apartments_url = "/api/v1/user/apartments"
        self.appeals_url = "/api/v1/user/appeals"

        self.management_org = ManagementOrganization.objects.create(
            name="ООО ПОН",
            inn="1234567890",
        )

        self.domik = Domik.objects.create(
            address="г Понск, улица Поновая, д 52",
            fias_id="test-fias-1",
            management_org=self.management_org,
        )

        self.second_domik = Domik.objects.create(
            address="г Понск, улица Вторая, д 10",
            fias_id="test-fias-2",
            management_org=self.management_org,
        )

        self.apartment = Apartment.objects.create(
            domik=self.domik,
            number="42",
            entrance="1",
        )

        self.second_apartment = Apartment.objects.create(
            domik=self.second_domik,
            number="15",
            entrance="2",
        )

        self.user = User.objects.create_user(
            max_id="test-user",
            name="pon-1",
        )

        self.other_user = User.objects.create_user(
            max_id="other-user",
            name="pon-2",
        )

    def auth(self, user=None):
        self.client.force_login(user or self.user)

    def post_json(self, url, data):
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
        )

    def add_apartment(
            self,
            user=None,
            apartment=None,
            is_primary=False,
    ):
        return UserApartment.objects.create(
            user=user or self.user,
            apartment=apartment or self.apartment,
            role=UserApartment.Role.RESIDENT,
            is_primary=is_primary,
        )

    def create_appeal(
            self,
            author=None,
            apartment=None,
            title="Не работает лифт",
            description="Лифт не работает",
            status=Appeal.Status.NEW,
    ):
        author = author or self.user
        apartment = apartment or self.apartment

        appeal = Appeal.objects.create(
            author=author,
            apartment=apartment,
            domik=apartment.domik,
            title=title,
            description=description,
            status=status,
        )

        AppealHistory.objects.create(
            appeal=appeal,
            status=status,
            changed_by=author,
            text="Обращение создано",
        )

        return appeal

    def test_login_existing_user(self):
        response = self.post_json(
            self.login_url,
            {
                "max_id": self.user.max_id,
                "name": self.user.name,
            },
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

        self.assertFalse(data["is_jk"])

    def test_login_existing_user_creates_session(self):
        response = self.post_json(
            self.login_url,
            {
                "max_id": self.user.max_id,
                "name": self.user.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Проверяем, что login действительно создал Django session
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["id"],
            str(self.user.id),
        )

    def test_login_creates_new_ordinary_user(self):
        response = self.post_json(
            self.login_url,
            {
                "max_id": "new-user",
                "name": "Алексей",
            },
        )

        self.assertEqual(response.status_code, 200)

        user = User.objects.get(
            max_id="new-user",
        )

        self.assertEqual(
            user.name,
            "Алексей",
        )

        self.assertFalse(user.is_jk)

        self.assertIsNone(
            user.management_org,
        )

        data = response.json()

        self.assertEqual(
            data["status"],
            "ok",
        )

        self.assertFalse(
            data["is_jk"],
        )

        self.assertIsNone(
            data["management_org"],
        )

    def test_login_without_max_id_returns_400(self):
        response = self.post_json(
            self.login_url,
            {
                "name": "Иван",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_login_without_name_returns_400(self):
        response = self.post_json(
            self.login_url,
            {
                "max_id": "user",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_login_invalid_json_returns_400(self):
        response = self.client.post(
            self.login_url,
            data="{invalid json}",
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["status"],
            "Некорректный JSON",
        )

    def test_login_get_not_allowed(self):
        response = self.client.get(
            self.login_url
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_me_requires_authentication(self):
        response = self.client.get(
            self.me_url
        )

        # Сейчас используется стандартный @login_required,
        # поэтому Django делает redirect
        self.assertEqual(
            response.status_code,
            302,
        )

    def test_me_returns_user(self):
        self.auth()

        response = self.client.get(
            self.me_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["id"],
            str(self.user.id),
        )

        self.assertEqual(
            data["max_id"],
            self.user.max_id,
        )

        self.assertEqual(
            data["name"],
            self.user.name,
        )

        self.assertFalse(
            data["is_jk"],
        )

        self.assertEqual(
            data["apartments"],
            [],
        )

    def test_me_returns_user_apartments(self):
        self.add_apartment(
            is_primary=True,
        )

        self.auth()

        response = self.client.get(
            self.me_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        apartments = response.json()["apartments"]

        self.assertEqual(
            len(apartments),
            1,
        )

        apartment = apartments[0]

        self.assertEqual(
            apartment["id"],
            str(self.apartment.id),
        )

        self.assertEqual(
            apartment["number"],
            "42",
        )

        self.assertEqual(
            apartment["entrance"],
            "1",
        )

        self.assertEqual(
            apartment["domik_id"],
            str(self.domik.id),
        )

        self.assertEqual(
            apartment["domik_address"],
            self.domik.address,
        )

        self.assertEqual(
            apartment["role"],
            UserApartment.Role.RESIDENT,
        )

        self.assertEqual(
            apartment["role_display"],
            "Житель",
        )

        self.assertTrue(
            apartment["is_primary"],
        )

    def test_me_returns_management_org(self):
        self.add_apartment()

        self.auth()

        response = self.client.get(
            self.me_url
        )

        org = (
            response.json()
            ["apartments"][0]
            ["management_org"]
        )

        self.assertEqual(
            org["id"],
            str(self.management_org.id),
        )

        self.assertEqual(
            org["name"],
            self.management_org.name,
        )

    def test_apartments_require_authentication(self):
        response = self.client.get(
            self.apartments_url
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_get_apartments_returns_empty_list(self):
        self.auth()

        response = self.client.get(
            self.apartments_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["apartments"],
            [],
        )

    def test_get_user_apartments(self):
        self.add_apartment(
            is_primary=True,
        )

        self.auth()

        response = self.client.get(
            self.apartments_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        apartments = response.json()["apartments"]

        self.assertEqual(
            len(apartments),
            1,
        )

        apartment = apartments[0]

        self.assertEqual(
            apartment["id"],
            str(self.apartment.id),
        )

        self.assertEqual(
            apartment["number"],
            self.apartment.number,
        )

        self.assertEqual(
            apartment["domik_id"],
            str(self.domik.id),
        )

        self.assertTrue(
            apartment["is_primary"],
        )

    def test_get_apartments_does_not_return_other_users_apartments(self):
        self.add_apartment(
            user=self.other_user,
            apartment=self.apartment,
        )

        self.auth()

        response = self.client.get(
            self.apartments_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["apartments"],
            [],
        )

    def test_add_first_apartment(self):
        self.auth()

        response = self.post_json(
            self.apartments_url,
            {
                "domik_id": str(self.domik.id),
                "number": self.apartment.number,
            },
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        relation = UserApartment.objects.get(
            user=self.user,
            apartment=self.apartment,
        )

        self.assertEqual(
            relation.role,
            UserApartment.Role.RESIDENT,
        )

        self.assertTrue(
            relation.is_primary,
        )

        self.assertTrue(
            response.json()["is_primary"],
        )

    def test_second_apartment_is_not_primary(self):
        self.add_apartment(
            apartment=self.apartment,
            is_primary=True,
        )

        self.auth()

        response = self.post_json(
            self.apartments_url,
            {
                "domik_id": str(self.second_domik.id),
                "number": self.second_apartment.number,
            },
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        relation = UserApartment.objects.get(
            user=self.user,
            apartment=self.second_apartment,
        )

        self.assertFalse(
            relation.is_primary,
        )

        self.assertFalse(
            response.json()["is_primary"],
        )

    def test_add_apartment_twice_returns_409(self):
        self.add_apartment()

        self.auth()

        response = self.post_json(
            self.apartments_url,
            {
                "domik_id": str(self.domik.id),
                "number": self.apartment.number,
            },
        )

        self.assertEqual(
            response.status_code,
            409,
        )

        self.assertEqual(
            UserApartment.objects.filter(
                user=self.user,
                apartment=self.apartment,
            ).count(),
            1,
        )

    def test_add_nonexistent_apartment_returns_404(self):
        self.auth()

        response = self.post_json(
            self.apartments_url,
            {
                "domik_id": str(self.domik.id),
                "number": "999",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json()["status"],
            "Квартира не найдена",
        )

    def test_add_apartment_without_required_fields_returns_400(self):
        self.auth()

        response = self.post_json(
            self.apartments_url,
            {
                "domik_id": str(self.domik.id),
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_add_apartment_invalid_json_returns_400(self):
        self.auth()

        response = self.client.post(
            self.apartments_url,
            data="{invalid}",
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_apartments_put_not_allowed(self):
        self.auth()

        response = self.client.put(
            self.apartments_url,
            data="{}",
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_appeals_require_authentication(self):
        response = self.client.get(
            self.appeals_url
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_get_appeals_empty(self):
        self.auth()

        response = self.client.get(
            self.appeals_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["appeals"],
            [],
        )

    def test_get_only_current_users_appeals(self):
        own_appeal = self.create_appeal()

        self.create_appeal(
            author=self.other_user,
            title="Чужая заявка",
        )

        self.auth()

        response = self.client.get(
            self.appeals_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        appeals = response.json()["appeals"]

        self.assertEqual(
            len(appeals),
            1,
        )

        self.assertEqual(
            appeals[0]["id"],
            str(own_appeal.id),
        )

    def test_get_appeals_newest_first(self):
        first = self.create_appeal(
            title="Первая заявка",
        )

        second = self.create_appeal(
            title="Вторая заявка",
        )

        self.auth()

        response = self.client.get(
            self.appeals_url
        )

        appeals = response.json()["appeals"]

        self.assertEqual(
            appeals[0]["id"],
            str(second.id),
        )

        self.assertEqual(
            appeals[1]["id"],
            str(first.id),
        )

    def test_get_appeal_list_fields(self):
        appeal = self.create_appeal()

        self.auth()

        response = self.client.get(
            self.appeals_url
        )

        data = response.json()["appeals"][0]

        self.assertEqual(
            data["id"],
            str(appeal.id),
        )

        self.assertEqual(
            data["title"],
            appeal.title,
        )

        self.assertEqual(
            data["description"],
            appeal.description,
        )

        self.assertEqual(
            data["status"],
            Appeal.Status.NEW,
        )

        self.assertEqual(
            data["apartment_id"],
            str(self.apartment.id),
        )

        self.assertEqual(
            data["apartment_number"],
            "42",
        )

        self.assertEqual(
            data["domik_id"],
            str(self.domik.id),
        )

        self.assertEqual(
            data["domik_address"],
            self.domik.address,
        )

        self.assertEqual(
            data["management_org"]["id"],
            str(self.management_org.id),
        )

    def test_create_appeal(self):
        self.add_apartment()

        self.auth()

        response = self.post_json(
            self.appeals_url,
            {
                "apartment_id": str(self.apartment.id),
                "title": "Не работает лифт",
                "description": "Лифт не работает со вчера",
            },
        )

        self.assertEqual(
            response.status_code,
            201,
        )

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
            appeal.status,
            Appeal.Status.NEW,
        )

        self.assertEqual(
            data["management_org"]["id"],
            str(self.management_org.id),
        )

    def test_create_appeal_creates_history(self):
        self.add_apartment()

        self.auth()

        response = self.post_json(
            self.appeals_url,
            {
                "apartment_id": str(self.apartment.id),
                "title": "Не работает свет",
                "description": "Нет света в подъезде",
            },
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        appeal = Appeal.objects.get(
            id=response.json()["id"]
        )

        histories = AppealHistory.objects.filter(
            appeal=appeal
        )

        self.assertEqual(
            histories.count(),
            1,
        )

        history = histories.first()

        self.assertEqual(
            history.status,
            Appeal.Status.NEW,
        )

        self.assertEqual(
            history.changed_by,
            self.user,
        )

    def test_cannot_create_appeal_for_foreign_apartment(self):
        self.add_apartment(
            user=self.other_user,
            apartment=self.apartment,
        )

        self.auth()

        response = self.post_json(
            self.appeals_url,
            {
                "apartment_id": str(self.apartment.id),
                "title": "Чужая квартира",
                "description": "Описание",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            Appeal.objects.count(),
            0,
        )

    def test_create_appeal_invalid_json_returns_400(self):
        self.auth()

        response = self.client.post(
            self.appeals_url,
            data="{invalid}",
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_appeals_put_not_allowed(self):
        self.auth()

        response = self.client.put(
            self.appeals_url,
            data="{}",
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_appeal_detail_requires_authentication(self):
        appeal = self.create_appeal()

        response = self.client.get(
            f"/api/v1/user/appeals/{appeal.id}"
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_get_own_appeal_detail(self):
        appeal = self.create_appeal()

        self.auth()

        response = self.client.get(
            f"/api/v1/user/appeals/{appeal.id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["id"],
            str(appeal.id),
        )

        self.assertEqual(
            data["title"],
            appeal.title,
        )

        self.assertEqual(
            data["description"],
            appeal.description,
        )

        self.assertEqual(
            data["status"],
            Appeal.Status.NEW,
        )

        self.assertEqual(
            data["status_display"],
            "Новая",
        )

        self.assertEqual(
            data["domik"]["id"],
            str(self.domik.id),
        )

        self.assertEqual(
            data["domik"]["address"],
            self.domik.address,
        )

        self.assertEqual(
            data["apartment"]["id"],
            str(self.apartment.id),
        )

        self.assertEqual(
            data["apartment"]["number"],
            "42",
        )

    def test_appeal_detail_contains_management_org(self):
        appeal = self.create_appeal()

        self.auth()

        response = self.client.get(
            f"/api/v1/user/appeals/{appeal.id}"
        )

        org = response.json()["domik"]["management_org"]

        self.assertEqual(
            org["id"],
            str(self.management_org.id),
        )

        self.assertEqual(
            org["name"],
            self.management_org.name,
        )

    def test_appeal_detail_contains_history(self):
        appeal = self.create_appeal()

        appeal.status = Appeal.Status.IN_PROGRESS
        appeal.save()

        AppealHistory.objects.create(
            appeal=appeal,
            status=Appeal.Status.IN_PROGRESS,
            changed_by=self.user,
            text="Заявка принята в работу",
        )

        self.auth()

        response = self.client.get(
            f"/api/v1/user/appeals/{appeal.id}"
        )

        history = response.json()["history"]

        self.assertEqual(
            len(history),
            2,
        )

        self.assertEqual(
            history[0]["status"],
            Appeal.Status.NEW,
        )

        self.assertEqual(
            history[1]["status"],
            Appeal.Status.IN_PROGRESS,
        )

        self.assertEqual(
            history[1]["status_display"],
            "В работе",
        )

        self.assertEqual(
            history[1]["text"],
            "Заявка принята в работу",
        )

        self.assertEqual(
            history[1]["changed_by"],
            self.user.name,
        )

    def test_cannot_get_other_users_appeal(self):
        appeal = self.create_appeal(
            author=self.other_user,
        )

        self.auth()

        response = self.client.get(
            f"/api/v1/user/appeals/{appeal.id}"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json()["status"],
            "Обращение не найдено",
        )

    def test_nonexistent_appeal_returns_404(self):
        self.auth()

        response = self.client.get(
            f"/api/v1/user/appeals/{uuid.uuid4()}"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_user_cannot_get_uk_domiks(self):
        self.auth()

        response = self.client.get(
            "/api/v1/uk/domiks"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.json()["status"],
            "Только для сотрудников УК",
        )

    def test_user_cannot_create_uk_domik(self):
        self.auth()

        response = self.post_json(
            "/api/v1/uk/domiks",
            {
                "address": "Тестовый дом",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_cannot_get_uk_domik_detail(self):
        self.auth()

        response = self.client.get(
            f"/api/v1/uk/domiks/{self.domik.id}"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_cannot_get_uk_appeals(self):
        self.auth()

        response = self.client.get(
            "/api/v1/uk/appeals"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_cannot_change_appeal_status(self):
        appeal = self.create_appeal()

        self.auth()

        response = self.post_json(
            f"/api/v1/uk/appeals/{appeal.id}/status",
            {
                "status": Appeal.Status.DONE,
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        appeal.refresh_from_db()

        self.assertEqual(
            appeal.status,
            Appeal.Status.NEW,
        )

class UKApiTestCase(TestCase):
    def setUp(self):
        self.org = ManagementOrganization.objects.create(name = "ООО ПОН", inn = "123456789")
        self.jk_user = User.objects.create_jkuser(max_id = "jk-user", name = "Il Rez", management_org = self.org)
        self.resident = User.objects.create_user(max_id = "resident-user", name = "Pon Rez")
        self.domik = Domik.objects.create(address = "г Понск, улица Поновая, д 52", fias_id = "fias-id", management_org = self.org)
        JKDomik.objects.create(user = self.jk_user, domik = self.domik)
        self.apartment = Apartment.objects.create(domik = self.domik, number = "42", entrance = "1")
        UserApartment.objects.create(user = self.resident, apartment = self.apartment, role = UserApartment.Role.RESIDENT)
        self.appeal = Appeal.objects.create(author = self.resident, domik = self.domik, apartment = self.apartment, title = "ПОН", description = "Не работает НИЧЕГО", status = Appeal.Status.NEW)
        AppealHistory.objects.create(appeal = self.appeal, status = Appeal.Status.NEW, changed_by = self.resident)
        self.uk_domiks_url = "/api/v1/uk/domiks"
        self.uk_appeals_url = "/api/v1/uk/appeals"

    def test_resident_cannot_get_uk_domiks(self):
        self.client.force_login(self.resident)

        response = self.client.get(
            self.uk_domiks_url
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["status"],
            "Только для сотрудников УК",
        )

    def test_unauthorized_user_cannot_get_uk_domiks(self):
        response = self.client.get(
            self.uk_domiks_url
        )

        self.assertEqual(response.status_code, 401)

    def test_get_uk_domiks(self):
        self.client.force_login(self.jk_user)

        response = self.client.get(
            self.uk_domiks_url
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data["domiks"]), 1)

        domik = data["domiks"][0]

        self.assertEqual(
            domik["id"],
            str(self.domik.id),
        )

        self.assertEqual(
            domik["address"],
            self.domik.address,
        )

        self.assertEqual(
            domik["fias_id"],
            self.domik.fias_id,
        )

        self.assertEqual(
            domik["apartments_count"],
            1,
        )

        self.assertEqual(
            domik["appeals_count"],
            1,
        )

        self.assertEqual(
            domik["new_appeals_count"],
            1,
        )

        self.assertEqual(
            domik["management_org"]["id"],
            str(self.org.id),
        )

        self.assertEqual(
            domik["management_org"]["name"],
            self.org.name,
        )

    def test_uk_user_does_not_see_unassigned_house(self):
        another_domik = Domik.objects.create(
            address="г Понск, ул Другая, д 10",
            fias_id="foreign-fias",
            management_org=self.org,
        )

        self.client.force_login(self.jk_user)

        response = self.client.get(
            self.uk_domiks_url
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            domik["id"]
            for domik in response.json()["domiks"]
        ]

        self.assertIn(
            str(self.domik.id),
            ids,
        )

        self.assertNotIn(
            str(another_domik.id),
            ids,
        )

    def test_create_uk_domik(self):
        self.client.force_login(self.jk_user)

        response = self.client.post(
            self.uk_domiks_url,
            data=json.dumps({
                "address": "г Понск, ул Новая, д 100",
                "fias_id": "new-fias-id",
                "apartments": {
                    "from": 1,
                    "to": 5,
                    "entrance": "1",
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        domik = Domik.objects.get(
            id=data["domik_id"]
        )

        self.assertEqual(
            domik.management_org,
            self.org,
        )

        self.assertTrue(
            JKDomik.objects.filter(
                user=self.jk_user,
                domik=domik,
            ).exists()
        )

        self.assertEqual(
            domik.apartments.count(),
            5,
        )

        self.assertEqual(
            data["apartments_created"],
            5,
        )

    def test_create_domik_uses_users_management_org(self):
        self.client.force_login(self.jk_user)

        response = self.client.post(
            self.uk_domiks_url,
            data=json.dumps({
                "address": "г Понск, ул УК, д 1",
                "fias_id": "org-test-fias",
                "apartments": {
                    "from": 1,
                    "to": 2,
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        domik = Domik.objects.get(
            id=response.json()["domik_id"]
        )

        self.assertEqual(
            domik.management_org,
            self.jk_user.management_org,
        )

    def test_jk_user_without_management_org_cannot_create_domik(self):
        employee = User.objects.create_jkuser(
            max_id="jk-without-org",
            name="pon2",
        )

        self.client.force_login(employee)

        response = self.client.post(
            self.uk_domiks_url,
            data=json.dumps({
                "address": "г Понск, д 555",
                "fias_id": "some-fias",
                "apartments": {
                    "from": 1,
                    "to": 10,
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            response.json()["status"],
            "Нет привязки к УК",
        )

    def test_create_domik_duplicate_fias_returns_409(self):
        self.client.force_login(self.jk_user)

        response = self.client.post(
            self.uk_domiks_url,
            data=json.dumps({
                "address": "Совершенно другой адрес",
                "fias_id": self.domik.fias_id,
                "apartments": {
                    "from": 1,
                    "to": 2,
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            409,
        )

    def test_create_domik_duplicate_address_returns_409(self):
        self.client.force_login(self.jk_user)

        response = self.client.post(
            self.uk_domiks_url,
            data=json.dumps({
                "address": self.domik.address,
                "fias_id": "another-fias",
                "apartments": {
                    "from": 1,
                    "to": 2,
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            409,
        )

    def test_get_uk_domik_detail(self):
        self.client.force_login(self.jk_user)

        response = self.client.get(
            f"/api/v1/uk/domiks/{self.domik.id}"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["id"],
            str(self.domik.id),
        )

        self.assertEqual(
            data["address"],
            self.domik.address,
        )

        self.assertEqual(
            len(data["apartments"]),
            1,
        )

        self.assertEqual(
            data["apartments"][0]["number"],
            "42",
        )

        self.assertEqual(
            data["apartments"][0]["residents_count"],
            1,
        )

    def test_cannot_get_unassigned_domik_detail(self):
        another_domik = Domik.objects.create(
            address="Чужой дом",
            fias_id="foreign-detail-fias",
            management_org=self.org,
        )

        self.client.force_login(self.jk_user)

        response = self.client.get(
            f"/api/v1/uk/domiks/{another_domik.id}"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_get_uk_appeals(self):
        self.client.force_login(self.jk_user)

        response = self.client.get(
            self.uk_appeals_url
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            len(data["appeals"]),
            1,
        )

        appeal = data["appeals"][0]

        self.assertEqual(
            appeal["id"],
            str(self.appeal.id),
        )

        self.assertEqual(
            appeal["title"],
            "ПОН",
        )

        self.assertEqual(
            appeal["status"],
            Appeal.Status.NEW,
        )

        self.assertEqual(
            appeal["apartment_number"],
            "42",
        )

        self.assertEqual(
            appeal["author"]["name"],
            self.resident.name,
        )

    def test_uk_does_not_see_appeal_from_unassigned_house(self):
        another_domik = Domik.objects.create(
            address="Чужой дом",
            fias_id="foreign-house",
            management_org=self.org,
        )

        another_apartment = Apartment.objects.create(
            domik=another_domik,
            number="10",
        )

        Appeal.objects.create(
            author=self.resident,
            domik=another_domik,
            apartment=another_apartment,
            title="Чужое обращение",
            description="Описание",
        )

        self.client.force_login(self.jk_user)

        response = self.client.get(
            self.uk_appeals_url
        )

        data = response.json()

        ids = [
            appeal["id"]
            for appeal in data["appeals"]
        ]

        self.assertIn(
            str(self.appeal.id),
            ids,
        )

        self.assertEqual(
            len(ids),
            1,
        )

    def test_update_appeal_status(self):
        self.client.force_login(self.jk_user)

        response = self.client.post(
            f"/api/v1/uk/appeals/{self.appeal.id}/status",
            data=json.dumps({
                "status": Appeal.Status.IN_PROGRESS,
                "text": "Передано мастеру",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        self.appeal.refresh_from_db()

        self.assertEqual(
            self.appeal.status,
            Appeal.Status.IN_PROGRESS,
        )

        history = self.appeal.appeal_history.order_by(
            "-changed_at"
        ).first()

        self.assertEqual(
            history.status,
            Appeal.Status.IN_PROGRESS,
        )

        self.assertEqual(
            history.changed_by,
            self.jk_user,
        )

        self.assertEqual(
            history.text,
            "Передано мастеру",
        )

    def test_update_appeal_invalid_status(self):
        self.client.force_login(self.jk_user)

        response = self.client.post(
            f"/api/v1/uk/appeals/{self.appeal.id}/status",
            data=json.dumps({
                "status": "pon",
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.appeal.refresh_from_db()

        self.assertEqual(
            self.appeal.status,
            Appeal.Status.NEW,
        )

    def test_cannot_update_appeal_from_unassigned_house(self):
        another_domik = Domik.objects.create(
            address="Дом без доступа",
            fias_id="no-access-fias",
            management_org=self.org,
        )

        another_apartment = Apartment.objects.create(
            domik=another_domik,
            number="5",
        )

        appeal = Appeal.objects.create(
            author=self.resident,
            domik=another_domik,
            apartment=another_apartment,
            title="Чужая заявка",
            description="Описание",
        )

        self.client.force_login(self.jk_user)

        response = self.client.post(
            f"/api/v1/uk/appeals/{appeal.id}/status",
            data=json.dumps({
                "status": Appeal.Status.DONE,
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        appeal.refresh_from_db()

        self.assertEqual(
            appeal.status,
            Appeal.Status.NEW,
        )



