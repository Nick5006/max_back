from apihandler.models import ApartmentKey, Appeal, AppealHistory, UserApartment

from .base import ApiTestCase


class UserApartmentApiTests(ApiTestCase):
    list_url = "/api/v1/user/apartments"

    def setUp(self):
        self.org = self.create_org()
        self.user = self.create_user()
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)
        self.second_apartment = self.create_apartment(self.domik, number="43", entrance="1")

    def make_bind_key(self, apartment=None, *, code="1234567890"):
        return ApartmentKey.objects.create(
            apartment=apartment or self.apartment,
            code=code,
            purpose=ApartmentKey.Purpose.BIND,
            created_by=None,
        )

    def test_apartments_require_authentication(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 401)
        self.assertEqual(
            self.post_json(
                self.list_url,
                {"domik_id": str(self.domik.id), "number": "42", "code": "123"},
            ).status_code,
            401,
        )

    def test_list_returns_only_current_users_apartments(self):
        self.link_apartment(self.user, self.apartment, is_primary=True)
        other = self.create_user(max_id="other", name="Пётр")
        self.link_apartment(other, self.second_apartment, is_primary=True)
        self.login_as(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        apartments = response.json()["apartments"]
        self.assertEqual(len(apartments), 1)
        self.assertEqual(apartments[0]["id"], str(self.apartment.id))
        self.assertTrue(apartments[0]["is_primary"])

    def test_attach_first_apartment_with_valid_one_time_key(self):
        key = self.make_bind_key()
        self.login_as(self.user)

        response = self.post_json(
            self.list_url,
            {
                "domik_id": str(self.domik.id),
                "number": self.apartment.number,
                "code": key.code,
            },
        )

        self.assertEqual(response.status_code, 201)
        relation = UserApartment.objects.get(user=self.user, apartment=self.apartment)
        self.assertEqual(relation.role, UserApartment.Role.RESIDENT)
        self.assertTrue(relation.is_primary)
        self.assertFalse(ApartmentKey.objects.filter(pk=key.pk).exists())

    def test_attach_second_apartment_is_not_primary(self):
        self.link_apartment(self.user, self.apartment, is_primary=True)
        key = self.make_bind_key(self.second_apartment)
        self.login_as(self.user)

        response = self.post_json(
            self.list_url,
            {
                "domik_id": str(self.domik.id),
                "number": self.second_apartment.number,
                "code": key.code,
            },
        )

        self.assertEqual(response.status_code, 201)
        relation = UserApartment.objects.get(user=self.user, apartment=self.second_apartment)
        self.assertFalse(relation.is_primary)
        self.assertTrue(
            UserApartment.objects.get(user=self.user, apartment=self.apartment).is_primary
        )

    def test_attach_rejects_missing_wrong_or_absent_key(self):
        self.login_as(self.user)

        missing = self.post_json(
            self.list_url,
            {"domik_id": str(self.domik.id), "number": self.apartment.number},
        )
        self.assertEqual(missing.status_code, 400)

        no_key = self.post_json(
            self.list_url,
            {
                "domik_id": str(self.domik.id),
                "number": self.apartment.number,
                "code": "1111111111",
            },
        )
        self.assertEqual(no_key.status_code, 403)
        # Текст ошибки не является частью API-контракта: реализация может
        # одинаково отвечать на отсутствующий и неверный код, чтобы не
        # раскрывать наличие ключа для квартиры.
        self.assertFalse(UserApartment.objects.filter(user=self.user).exists())

        key = self.make_bind_key(code="1234567890")
        wrong = self.post_json(
            self.list_url,
            {
                "domik_id": str(self.domik.id),
                "number": self.apartment.number,
                "code": "0000000000",
            },
        )
        self.assertEqual(wrong.status_code, 403)
        self.assertTrue(ApartmentKey.objects.filter(pk=key.pk).exists())
        self.assertFalse(UserApartment.objects.filter(user=self.user).exists())

    def test_attach_nonexistent_apartment_is_rejected_without_side_effects(self):
        self.login_as(self.user)
        response = self.post_json(
            self.list_url,
            {
                "domik_id": str(self.domik.id),
                "number": "999",
                "code": "1234567890",
            },
        )

        # Некоторые версии API сначала проверяют код (403), другие сначала
        # ищут квартиру (404). Для этого теста важен внешний инвариант:
        # несуществующую квартиру нельзя привязать и БД не меняется.
        self.assertIn(response.status_code, (403, 404))
        self.assertFalse(UserApartment.objects.filter(user=self.user).exists())

    def test_attach_duplicate_with_new_key_returns_409_and_does_not_consume_key(self):
        self.link_apartment(self.user, self.apartment, is_primary=True)
        key = self.make_bind_key()
        self.login_as(self.user)

        response = self.post_json(
            self.list_url,
            {
                "domik_id": str(self.domik.id),
                "number": self.apartment.number,
                "code": key.code,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["status"], "Квартира уже добавлена")
        self.assertTrue(ApartmentKey.objects.filter(pk=key.pk).exists())

    def test_delete_apartment_reassigns_primary(self):
        self.link_apartment(self.user, self.apartment, is_primary=True)
        second = self.link_apartment(self.user, self.second_apartment, is_primary=False)
        self.login_as(self.user)

        response = self.client.delete(
            f"/api/v1/user/apartments/{self.apartment.id}/delete"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            UserApartment.objects.filter(user=self.user, apartment=self.apartment).exists()
        )
        second.refresh_from_db()
        self.assertTrue(second.is_primary)

    def test_delete_apartment_cannot_delete_foreign_relation(self):
        other = self.create_user(max_id="other", name="Пётр")
        self.link_apartment(other, self.apartment, is_primary=True)
        self.login_as(self.user)

        response = self.client.delete(
            f"/api/v1/user/apartments/{self.apartment.id}/delete"
        )
        self.assertEqual(response.status_code, 404)

    def test_apartment_collection_rejects_unsupported_method(self):
        self.login_as(self.user)
        self.assertEqual(self.client.put(self.list_url).status_code, 405)


class AppealApiTests(ApiTestCase):
    list_url = "/api/v1/user/appeals"

    def setUp(self):
        self.org = self.create_org()
        self.user = self.create_user()
        self.other_user = self.create_user(max_id="other", name="Пётр")
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)
        self.other_apartment = self.create_apartment(self.domik, number="43")
        self.link_apartment(self.user, self.apartment, is_primary=True)
        self.link_apartment(self.other_user, self.other_apartment, is_primary=True)

    def test_appeals_require_authentication(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 401)
        self.assertEqual(
            self.post_json(
                self.list_url,
                {
                    "apartment_id": str(self.apartment.id),
                    "title": "Тема",
                    "description": "Описание",
                },
            ).status_code,
            401,
        )

    def test_create_appeal_for_owned_apartment_creates_history(self):
        self.login_as(self.user)

        response = self.post_json(
            self.list_url,
            {
                "apartment_id": str(self.apartment.id),
                "title": "Не работает лифт",
                "description": "Лифт остановился",
            },
        )

        self.assertEqual(response.status_code, 201)
        appeal = Appeal.objects.get(author=self.user)
        self.assertEqual(appeal.apartment_id, self.apartment.id)
        self.assertEqual(appeal.domik_id, self.domik.id)
        self.assertEqual(appeal.status, Appeal.Status.NEW)

        history = AppealHistory.objects.get(appeal=appeal)
        self.assertEqual(history.status, Appeal.Status.NEW)
        self.assertEqual(history.changed_by_id, self.user.id)
        self.assertEqual(response.json()["management_org"]["id"], str(self.org.id))

    def test_create_appeal_rejects_foreign_apartment(self):
        self.login_as(self.user)
        response = self.post_json(
            self.list_url,
            {
                "apartment_id": str(self.other_apartment.id),
                "title": "Чужая заявка",
                "description": "Описание",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Appeal.objects.count(), 0)

    def test_create_appeal_validates_payload(self):
        self.login_as(self.user)
        response = self.post_json(
            self.list_url,
            {"apartment_id": str(self.apartment.id), "title": "Тема"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.json()["status"])

    def test_list_returns_only_current_users_appeals_newest_first(self):
        first = self.create_appeal(
            author=self.user,
            apartment=self.apartment,
            title="Старое",
        )
        second = self.create_appeal(
            author=self.user,
            apartment=self.apartment,
            title="Новое",
        )
        self.create_appeal(
            author=self.other_user,
            apartment=self.other_apartment,
            title="Чужое",
        )
        self.login_as(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.json()["appeals"]]
        self.assertEqual(ids, [str(second.id), str(first.id)])

    def test_detail_returns_history_and_blocks_foreign_appeal(self):
        appeal = self.create_appeal(author=self.user, apartment=self.apartment)
        AppealHistory.objects.create(
            appeal=appeal,
            status=Appeal.Status.IN_PROGRESS,
            changed_by=None,
            text="Принято в работу",
        )
        foreign = self.create_appeal(
            author=self.other_user,
            apartment=self.other_apartment,
        )
        self.login_as(self.user)

        own = self.client.get(f"/api/v1/user/appeals/{appeal.id}")
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.json()["id"], str(appeal.id))
        self.assertEqual(len(own.json()["history"]), 2)
        self.assertEqual(own.json()["domik"]["management_org"]["id"], str(self.org.id))

        denied = self.client.get(f"/api/v1/user/appeals/{foreign.id}")
        self.assertEqual(denied.status_code, 404)

    def test_appeal_collection_rejects_unsupported_method(self):
        self.login_as(self.user)
        self.assertEqual(self.client.put(self.list_url).status_code, 405)
