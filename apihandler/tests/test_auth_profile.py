from apihandler.models import ManagementOrganization, UserApartment

from .base import ApiTestCase


class LoginApiTests(ApiTestCase):
    login_url = "/api/v1/login"

    def test_login_creates_resident_and_session(self):
        response = self.post_json(
            self.login_url,
            {"max_id": "new-user", "name": "Алексей"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertFalse(data["is_jk"])
        self.assertIsNone(data["management_org"])

        user = self.create_user_queryset_get("new-user")
        self.assertEqual(user.name, "Алексей")
        self.assertFalse(user.is_jk)
        self.assertIsNone(user.management_org)

        me = self.client.get("/api/v1/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["id"], str(user.id))

    def create_user_queryset_get(self, max_id):
        from apihandler.models import User

        return User.objects.get(max_id=max_id)

    def test_login_existing_user_does_not_recreate_or_change_role(self):
        user = self.create_user(max_id="existing", name="Старое имя")

        response = self.post_json(
            self.login_url,
            {
                "max_id": user.max_id,
                "name": "Новое имя",
                "is_jk": True,
                "management_org": {"name": "Другая УК", "inn": "9999999999"},
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "Такой пользователь уже существует")
        user.refresh_from_db()
        self.assertEqual(user.name, "Старое имя")
        self.assertFalse(user.is_jk)
        self.assertEqual(ManagementOrganization.objects.count(), 0)

    def test_login_creates_uk_user_and_reuses_org_by_inn(self):
        org = self.create_org(name="Существующая УК", inn="7700000000")

        response = self.post_json(
            self.login_url,
            {
                "max_id": "uk-new",
                "name": "Сотрудник",
                "is_jk": True,
                "management_org": {"name": "Новое имя не должно примениться", "inn": org.inn},
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_jk"])
        self.assertEqual(response.json()["management_org"]["id"], str(org.id))
        self.assertEqual(ManagementOrganization.objects.count(), 1)

        user = self.create_user_queryset_get("uk-new")
        self.assertEqual(user.management_org_id, org.id)

    def test_login_validates_required_and_uk_fields(self):
        cases = [
            ({"name": "Иван"}, "Нужны поля max_id и name"),
            ({"max_id": "user"}, "Нужны поля max_id и name"),
            (
                {"max_id": "uk", "name": "УК", "is_jk": True},
                "Для сотрудника УК необходимо указать management_org",
            ),
            (
                {
                    "max_id": "uk",
                    "name": "УК",
                    "is_jk": True,
                    "management_org": {"name": "УК"},
                },
                "Для management_org нужны поля name и inn",
            ),
        ]
        for payload, expected_status in cases:
            with self.subTest(payload=payload):
                response = self.post_json(self.login_url, payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["status"], expected_status)

    def test_login_rejects_invalid_json_and_non_object_json(self):
        invalid = self.client.post(
            self.login_url,
            data="{invalid",
            content_type="application/json",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["status"], "Некорректный JSON")

        array = self.client.post(
            self.login_url,
            data="[]",
            content_type="application/json",
        )
        self.assertEqual(array.status_code, 400)
        self.assertEqual(array.json()["status"], "Тело запроса должно быть JSON-объектом")

    def test_login_only_accepts_post(self):
        self.assertEqual(self.client.get(self.login_url).status_code, 405)


class ProfileAndSearchApiTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.user = self.create_user()
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)

    def test_me_requires_authentication_with_json_401(self):
        response = self.client.get("/api/v1/me")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"status": "Не авторизован"})

    def test_me_returns_profile_and_only_users_apartments(self):
        self.link_apartment(self.user, self.apartment, is_primary=True)
        other_domik = self.create_domik(
            address="г Понск, улица Чужая, д 1",
            fias_id="foreign-fias",
            management_org=self.org,
        )
        other_apartment = self.create_apartment(other_domik, number="1")
        other_user = self.create_user(max_id="other", name="Пётр")
        self.link_apartment(other_user, other_apartment, is_primary=True)

        self.login_as(self.user)
        response = self.client.get("/api/v1/me")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], str(self.user.id))
        self.assertEqual(data["max_id"], self.user.max_id)
        self.assertEqual(data["apartments"], [
            {
                "id": str(self.apartment.id),
                "number": "42",
                "entrance": "1",
                "domik_id": str(self.domik.id),
                "domik_address": self.domik.address,
                "management_org": {"id": str(self.org.id), "name": self.org.name},
                "role": UserApartment.Role.RESIDENT,
                "role_display": "Житель",
                "is_primary": True,
            }
        ])

    def test_domik_search_requires_authentication(self):
        response = self.client.get("/api/v1/domiks?search=Пон")
        self.assertEqual(response.status_code, 401)

    def test_domik_search_is_case_insensitive_and_honors_limit(self):
        self.create_domik(
            address="Test Street 10",
            fias_id="fias-2",
            management_org=self.org,
        )
        self.create_domik(
            address="TEST Avenue 20",
            fias_id="fias-3",
            management_org=self.org,
        )
        self.login_as(self.user)

        response = self.client.get("/api/v1/domiks?search=test&limit=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["domiks"]), 1)
        self.assertIn("test", response.json()["domiks"][0]["address"].lower())

    def test_domik_search_short_query_returns_empty_list(self):
        self.login_as(self.user)
        response = self.client.get("/api/v1/domiks?search=п")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"domiks": []})
