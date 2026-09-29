from unittest.mock import patch

from apihandler.models import Apartment, ApartmentKey, Appeal, AppealHistory, Domik, UserApartment

from .base import ApiTestCase


class UkAccessTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.resident = self.create_user()
        self.uk_without_org = self.create_user(
            max_id="uk-no-org",
            name="УК без организации",
            is_jk=True,
            management_org=None,
        )

    def test_uk_endpoint_requires_authentication(self):
        response = self.client.get("/api/v1/uk/domiks")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"status": "Не авторизован"})

    def test_uk_endpoint_rejects_resident(self):
        self.login_as(self.resident)
        response = self.client.get("/api/v1/uk/domiks")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"status": "Только для сотрудников УК"})

    def test_uk_endpoint_rejects_uk_user_without_org(self):
        self.login_as(self.uk_without_org)
        response = self.client.get("/api/v1/uk/domiks")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"status": "Нет привязки к УК"})


class UkHouseApiTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.other_org = self.create_org(name="Другая УК", inn="9999999999")
        self.uk = self.create_user(
            max_id="uk-user",
            name="Сотрудник",
            is_jk=True,
            management_org=self.org,
        )
        self.other_uk = self.create_user(
            max_id="other-uk",
            name="Другой сотрудник",
            is_jk=True,
            management_org=self.other_org,
        )
        self.domik = self.create_domik(management_org=self.org)
        self.foreign_domik = self.create_domik(
            address="г Понск, улица Чужая, д 1",
            fias_id="foreign-fias",
            management_org=self.other_org,
        )

    def test_list_contains_only_houses_of_current_org_with_counters(self):
        apartment = self.create_apartment(self.domik)
        resident = self.create_user(max_id="resident", name="Житель")
        self.create_appeal(author=resident, apartment=apartment)
        self.create_apartment(self.foreign_domik, number="1")
        self.login_as(self.uk)

        response = self.client.get("/api/v1/uk/domiks")

        self.assertEqual(response.status_code, 200)
        items = response.json()["domiks"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(self.domik.id))
        self.assertEqual(items[0]["apartments_count"], 1)
        self.assertEqual(items[0]["appeals_count"], 1)
        self.assertEqual(items[0]["new_appeals_count"], 1)

    def test_create_house_creates_ranges_atomically_and_assigns_current_org(self):
        self.login_as(self.uk)
        response = self.post_json(
            "/api/v1/uk/domiks",
            {
                "address": "г Понск, улица Новая, д 10",
                "fias_id": "new-fias",
                "apartments": [
                    {"from": 1, "to": 2, "entrance": "1"},
                    {"from": 3, "to": 4, "entrance": "2"},
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        created = Domik.objects.get(fias_id="new-fias")
        self.assertEqual(created.management_org_id, self.org.id)
        self.assertEqual(
            list(created.apartments.order_by("number").values_list("number", "entrance")),
            [("1", "1"), ("2", "1"), ("3", "2"), ("4", "2")],
        )
        self.assertEqual(response.json()["apartments_created"], 4)

    def test_create_house_rejects_duplicate_address_fias_and_overlapping_ranges(self):
        self.login_as(self.uk)

        duplicate_address = self.post_json(
            "/api/v1/uk/domiks",
            {
                "address": self.domik.address,
                "fias_id": "another-fias",
                "apartments": {"from": 1, "to": 1},
            },
        )
        self.assertEqual(duplicate_address.status_code, 409)

        duplicate_fias = self.post_json(
            "/api/v1/uk/domiks",
            {
                "address": "Другой адрес",
                "fias_id": self.domik.fias_id,
                "apartments": {"from": 1, "to": 1},
            },
        )
        self.assertEqual(duplicate_fias.status_code, 409)

        before = Domik.objects.count()
        overlap = self.post_json(
            "/api/v1/uk/domiks",
            {
                "address": "г Понск, улица Диапазонная, д 5",
                "fias_id": "range-fias",
                "apartments": [
                    {"from": 1, "to": 3},
                    {"from": 3, "to": 5},
                ],
            },
        )
        self.assertEqual(overlap.status_code, 400)
        self.assertEqual(Domik.objects.count(), before)

    def test_house_detail_and_delete_are_scoped_to_current_org(self):
        apartment = self.create_apartment(self.domik)
        self.login_as(self.uk)

        detail = self.client.get(f"/api/v1/uk/domiks/{self.domik.id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["apartments"][0]["id"], str(apartment.id))

        foreign = self.client.get(f"/api/v1/uk/domiks/{self.foreign_domik.id}")
        self.assertEqual(foreign.status_code, 404)

        delete_foreign = self.client.delete(f"/api/v1/uk/domiks/{self.foreign_domik.id}")
        self.assertEqual(delete_foreign.status_code, 404)
        self.assertTrue(Domik.objects.filter(pk=self.foreign_domik.pk).exists())

        delete_own = self.client.delete(f"/api/v1/uk/domiks/{self.domik.id}")
        self.assertEqual(delete_own.status_code, 200)
        self.assertFalse(Domik.objects.filter(pk=self.domik.pk).exists())


class UkApartmentManagementTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.other_org = self.create_org(name="Другая УК", inn="9999999999")
        self.uk = self.create_user(
            max_id="uk",
            name="Сотрудник",
            is_jk=True,
            management_org=self.org,
        )
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)
        self.second_apartment = self.create_apartment(self.domik, number="43")
        self.foreign_domik = self.create_domik(
            address="Чужой дом",
            fias_id="foreign",
            management_org=self.other_org,
        )
        self.login_as(self.uk)

    def test_list_and_create_apartment(self):
        list_response = self.client.get(f"/api/v1/uk/domiks/{self.domik.id}/apartments")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["apartments"]), 2)

        create_response = self.post_json(
            f"/api/v1/uk/domiks/{self.domik.id}/apartments",
            {"number": "44", "entrance": "2"},
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertTrue(Apartment.objects.filter(domik=self.domik, number="44").exists())

        duplicate = self.post_json(
            f"/api/v1/uk/domiks/{self.domik.id}/apartments",
            {"number": "44"},
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_apartment_detail_lists_residents_and_appeals(self):
        resident = self.create_user(max_id="resident", name="Житель")
        self.link_apartment(resident, self.apartment, is_primary=True)
        self.create_appeal(author=resident, apartment=self.apartment)

        response = self.client.get(
            f"/api/v1/uk/domiks/{self.domik.id}/apartments/{self.apartment.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["residents"][0]["user_id"], str(resident.id))
        self.assertEqual(response.json()["appeals_count"], 1)

    def test_patch_apartment_updates_fields_and_prevents_duplicate_number(self):
        url = f"/api/v1/uk/domiks/{self.domik.id}/apartments/{self.apartment.id}"
        response = self.patch_json(url, {"number": "100", "entrance": "5"})
        self.assertEqual(response.status_code, 200)
        self.apartment.refresh_from_db()
        self.assertEqual(self.apartment.number, "100")
        self.assertEqual(self.apartment.entrance, "5")

        duplicate = self.patch_json(url, {"number": self.second_apartment.number})
        self.assertEqual(duplicate.status_code, 409)

        no_changes = self.patch_json(url, {"number": "100", "entrance": "5"})
        self.assertEqual(no_changes.status_code, 400)

    def test_delete_apartment_only_when_it_has_no_residents_or_appeals(self):
        resident = self.create_user(max_id="resident", name="Житель")
        relation = self.link_apartment(resident, self.apartment, is_primary=True)
        url = f"/api/v1/uk/domiks/{self.domik.id}/apartments/{self.apartment.id}"

        with_resident = self.client.delete(url)
        self.assertEqual(with_resident.status_code, 409)

        relation.delete()
        appeal = self.create_appeal(author=resident, apartment=self.apartment)
        with_appeal = self.client.delete(url)
        self.assertEqual(with_appeal.status_code, 409)

        appeal.delete()
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(Apartment.objects.filter(pk=self.apartment.pk).exists())

    @patch("apihandler.views.secrets.choice", return_value="7")
    def test_generate_bind_key_creates_then_rotates_single_key(self, mocked_choice):
        url = (
            f"/api/v1/uk/domiks/{self.domik.id}/apartments/"
            f"{self.apartment.id}/generate-key"
        )

        first = self.post_json(url, {})
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()["code"], "7777777777")
        key = ApartmentKey.objects.get(apartment=self.apartment, purpose=ApartmentKey.Purpose.BIND)
        self.assertEqual(key.created_by_id, self.uk.id)

        second = self.post_json(url, {"purpose": ApartmentKey.Purpose.BIND})
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            ApartmentKey.objects.filter(
                apartment=self.apartment,
                purpose=ApartmentKey.Purpose.BIND,
            ).count(),
            1,
        )

        invalid = self.post_json(url, {"purpose": "unknown"})
        self.assertEqual(invalid.status_code, 400)

    def test_cannot_manage_apartment_in_foreign_house(self):
        response = self.client.get(f"/api/v1/uk/domiks/{self.foreign_domik.id}/apartments")
        self.assertEqual(response.status_code, 404)


class UkAppealApiTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.other_org = self.create_org(name="Другая УК", inn="9999999999")
        self.uk = self.create_user(
            max_id="uk",
            name="Сотрудник",
            is_jk=True,
            management_org=self.org,
        )
        self.resident = self.create_user(max_id="resident", name="Житель")
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)
        self.appeal = self.create_appeal(author=self.resident, apartment=self.apartment)

        foreign_domik = self.create_domik(
            address="Чужой дом",
            fias_id="foreign",
            management_org=self.other_org,
        )
        foreign_apartment = self.create_apartment(foreign_domik, number="1")
        self.foreign_appeal = self.create_appeal(
            author=self.resident,
            apartment=foreign_apartment,
            title="Чужое обращение",
        )
        self.login_as(self.uk)

    def test_list_and_detail_are_scoped_to_current_org(self):
        response = self.client.get("/api/v1/uk/appeals")
        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.json()["appeals"]]
        self.assertEqual(ids, [str(self.appeal.id)])

        detail = self.client.get(f"/api/v1/uk/appeals/{self.appeal.id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["author"]["id"], str(self.resident.id))
        self.assertEqual(len(detail.json()["history"]), 1)

        foreign = self.client.get(f"/api/v1/uk/appeals/{self.foreign_appeal.id}")
        self.assertEqual(foreign.status_code, 404)

    @patch("apihandler.views.send_message")
    def test_update_status_changes_appeal_creates_history_and_notifies_author(self, send_message):
        response = self.post_json(
            f"/api/v1/uk/appeals/{self.appeal.id}/status",
            {"status": Appeal.Status.IN_PROGRESS, "text": "Мастер назначен"},
        )

        self.assertEqual(response.status_code, 200)
        self.appeal.refresh_from_db()
        self.assertEqual(self.appeal.status, Appeal.Status.IN_PROGRESS)
        history = AppealHistory.objects.filter(appeal=self.appeal).order_by("changed_at")
        self.assertEqual(history.count(), 2)
        self.assertEqual(history.last().changed_by_id, self.uk.id)
        self.assertEqual(history.last().text, "Мастер назначен")
        send_message.assert_called_once()
        self.assertEqual(send_message.call_args.args[0], self.resident.max_id)

    def test_update_status_validates_status_and_scope(self):
        invalid = self.post_json(
            f"/api/v1/uk/appeals/{self.appeal.id}/status",
            {"status": "wrong"},
        )
        self.assertEqual(invalid.status_code, 400)
        self.appeal.refresh_from_db()
        self.assertEqual(self.appeal.status, Appeal.Status.NEW)

        foreign = self.post_json(
            f"/api/v1/uk/appeals/{self.foreign_appeal.id}/status",
            {"status": Appeal.Status.DONE},
        )
        self.assertEqual(foreign.status_code, 404)
