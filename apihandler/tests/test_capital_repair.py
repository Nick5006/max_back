from decimal import Decimal
from unittest.mock import patch

from apihandler.models import CapitalRepair, CapitalRepairWork

from .base import ApiTestCase


class CapitalRepairApiTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.other_org = self.create_org(name="Другая УК", inn="9999999999")
        self.uk = self.create_user(
            max_id="uk",
            name="Сотрудник",
            is_jk=True,
            management_org=self.org,
        )
        self.user = self.create_user(max_id="resident", name="Житель")
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)
        self.link_apartment(self.user, self.apartment, is_primary=True)
        self.foreign_domik = self.create_domik(
            address="Чужой дом",
            fias_id="foreign",
            management_org=self.other_org,
        )

    def user_url(self, domik=None):
        return f"/api/v1/user/domik/{(domik or self.domik).id}/capital-repair"

    def uk_url(self, domik=None):
        return f"/api/v1/uk/domiks/{(domik or self.domik).id}/capital-repair"

    def test_resident_get_requires_house_membership(self):
        self.login_as(self.user)
        response = self.client.get(self.user_url(self.foreign_domik))
        self.assertEqual(response.status_code, 403)

    def test_resident_get_returns_empty_section_when_not_configured(self):
        self.login_as(self.user)
        response = self.client.get(self.user_url())

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["capital_repair"])
        self.assertEqual(response.json()["works"], [])

    def test_resident_get_returns_account_and_works(self):
        cr = CapitalRepair.objects.create(
            domik=self.domik,
            tariff_per_sqm=Decimal("12.50"),
            collected_total=Decimal("100000.00"),
            spent_total=Decimal("25000.00"),
        )
        work = CapitalRepairWork.objects.create(
            capital_repair=cr,
            work_type="Ремонт крыши",
            planned_year=2027,
            cost=Decimal("50000.00"),
        )
        self.login_as(self.user)

        response = self.client.get(self.user_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["capital_repair"]["balance"], "75000.00")
        self.assertEqual(response.json()["works"][0]["id"], str(work.id))

    def test_uk_get_is_scoped_to_own_house(self):
        self.login_as(self.uk)
        own = self.client.get(self.uk_url())
        self.assertEqual(own.status_code, 200)
        self.assertIsNone(own.json()["capital_repair"])

        foreign = self.client.get(self.uk_url(self.foreign_domik))
        self.assertEqual(foreign.status_code, 404)

    @patch("apihandler.views._send_to_domik_users")
    def test_uk_create_capital_repair_account(self, send_to_users):
        self.login_as(self.uk)
        response = self.post_json(self.uk_url(), {"tariff_per_sqm": "13.75"})

        self.assertEqual(response.status_code, 201)
        cr = CapitalRepair.objects.get(domik=self.domik)
        self.assertEqual(cr.tariff_per_sqm, Decimal("13.75"))
        self.assertEqual(response.json()["capital_repair"]["tariff_per_sqm"], "13.75")
        send_to_users.assert_called_once()

        duplicate = self.post_json(self.uk_url(), {"tariff_per_sqm": "14.00"})
        self.assertEqual(duplicate.status_code, 409)

    def test_uk_create_rejects_invalid_or_negative_tariff(self):
        self.login_as(self.uk)
        invalid = self.post_json(self.uk_url(), {"tariff_per_sqm": "abc"})
        self.assertEqual(invalid.status_code, 400)

        negative = self.post_json(self.uk_url(), {"tariff_per_sqm": "-1"})
        self.assertEqual(negative.status_code, 400)
        self.assertFalse(CapitalRepair.objects.filter(domik=self.domik).exists())

    @patch("apihandler.views._send_to_domik_users")
    def test_uk_patch_updates_only_changed_numeric_fields(self, send_to_users):
        cr = CapitalRepair.objects.create(
            domik=self.domik,
            tariff_per_sqm=Decimal("10.00"),
            collected_total=Decimal("100.00"),
            spent_total=Decimal("20.00"),
        )
        self.login_as(self.uk)

        response = self.patch_json(
            self.uk_url(),
            {"collected_total": "150.00", "spent_total": "20.00"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["updated_fields"], ["collected_total"])
        cr.refresh_from_db()
        self.assertEqual(cr.collected_total, Decimal("150.00"))
        self.assertEqual(cr.balance, Decimal("130.00"))
        send_to_users.assert_called_once()

        no_changes = self.patch_json(
            self.uk_url(),
            {"collected_total": "150.00"},
        )
        self.assertEqual(no_changes.status_code, 400)

    def test_uk_patch_requires_account_and_rejects_negative_values(self):
        self.login_as(self.uk)
        missing = self.patch_json(self.uk_url(), {"spent_total": "1"})
        self.assertEqual(missing.status_code, 404)

        CapitalRepair.objects.create(domik=self.domik)
        negative = self.patch_json(self.uk_url(), {"spent_total": "-1"})
        self.assertEqual(negative.status_code, 400)


class CapitalRepairWorkApiTests(ApiTestCase):
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
        self.cr = CapitalRepair.objects.create(domik=self.domik, tariff_per_sqm=Decimal("10.00"))
        self.foreign_domik = self.create_domik(
            address="Чужой дом",
            fias_id="foreign",
            management_org=self.other_org,
        )
        self.login_as(self.uk)

    def works_url(self, domik=None):
        return f"/api/v1/uk/domiks/{(domik or self.domik).id}/capital-repair/works"

    def detail_url(self, work, domik=None):
        return f"{self.works_url(domik)}/{work.id}"

    def test_list_works(self):
        first = CapitalRepairWork.objects.create(
            capital_repair=self.cr,
            work_type="Лифт",
            planned_year=2028,
        )
        second = CapitalRepairWork.objects.create(
            capital_repair=self.cr,
            work_type="Крыша",
            planned_year=2027,
        )

        response = self.client.get(self.works_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.json()["works"]],
            [str(second.id), str(first.id)],
        )

    @patch("apihandler.views._send_to_domik_users")
    def test_create_work_persists_valid_values_and_notifies(self, send_to_users):
        response = self.post_json(
            self.works_url(),
            {
                "work_type": "Ремонт крыши",
                "planned_year": 2028,
                "status": CapitalRepairWork.Status.IN_PROGRESS,
                "cost": "250000.50",
                "contractor": "ООО Ремонт",
                "description": "Замена покрытия",
            },
        )

        self.assertEqual(response.status_code, 201)
        work = CapitalRepairWork.objects.get(work_type="Ремонт крыши")
        self.assertEqual(work.cost, Decimal("250000.50"))
        self.assertEqual(work.status, CapitalRepairWork.Status.IN_PROGRESS)
        send_to_users.assert_called_once()

    def test_create_work_validates_year_status_and_cost(self):
        cases = [
            ({"work_type": "Работа", "planned_year": "bad"}, 400),
            ({"work_type": "Работа", "planned_year": 1800}, 400),
            ({"work_type": "Работа", "planned_year": 2028, "status": "bad"}, 400),
            ({"work_type": "Работа", "planned_year": 2028, "cost": "bad"}, 400),
            ({"work_type": "Работа", "planned_year": 2028, "cost": "-1"}, 400),
        ]
        for payload, status in cases:
            with self.subTest(payload=payload):
                response = self.post_json(self.works_url(), payload)
                self.assertEqual(response.status_code, status)
        self.assertEqual(CapitalRepairWork.objects.count(), 0)

    def test_works_require_existing_account_and_own_house(self):
        own_without_account = self.create_domik(
            address="Второй свой дом",
            fias_id="own-2",
            management_org=self.org,
        )
        missing = self.client.get(self.works_url(own_without_account))
        self.assertEqual(missing.status_code, 404)

        foreign = self.client.get(self.works_url(self.foreign_domik))
        self.assertEqual(foreign.status_code, 404)

    @patch("apihandler.views._send_to_domik_users")
    def test_patch_work_updates_fields(self, send_to_users):
        work = CapitalRepairWork.objects.create(
            capital_repair=self.cr,
            work_type="Лифт",
            planned_year=2028,
            cost=Decimal("100.00"),
        )

        response = self.patch_json(
            self.detail_url(work),
            {
                "work_type": "Новый лифт",
                "status": CapitalRepairWork.Status.DONE,
                "cost": None,
                "contractor": "Подрядчик",
            },
        )

        self.assertEqual(response.status_code, 200)
        work.refresh_from_db()
        self.assertEqual(work.work_type, "Новый лифт")
        self.assertEqual(work.status, CapitalRepairWork.Status.DONE)
        self.assertIsNone(work.cost)
        self.assertEqual(work.contractor, "Подрядчик")
        self.assertEqual(
            response.json()["updated_fields"],
            ["work_type", "status", "cost", "contractor"],
        )
        send_to_users.assert_called_once()

    def test_patch_work_rejects_empty_or_invalid_values(self):
        work = CapitalRepairWork.objects.create(
            capital_repair=self.cr,
            work_type="Лифт",
            planned_year=2028,
        )
        url = self.detail_url(work)

        self.assertEqual(self.patch_json(url, {}).status_code, 400)
        self.assertEqual(self.patch_json(url, {"work_type": ""}).status_code, 400)
        self.assertEqual(self.patch_json(url, {"planned_year": "bad"}).status_code, 400)
        self.assertEqual(self.patch_json(url, {"status": "bad"}).status_code, 400)
        self.assertEqual(self.patch_json(url, {"cost": "-1"}).status_code, 400)

    @patch("apihandler.views._send_to_domik_users")
    def test_delete_work(self, send_to_users):
        work = CapitalRepairWork.objects.create(
            capital_repair=self.cr,
            work_type="Лифт",
            planned_year=2028,
        )

        response = self.client.delete(self.detail_url(work))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CapitalRepairWork.objects.filter(pk=work.pk).exists())
        send_to_users.assert_called_once()
