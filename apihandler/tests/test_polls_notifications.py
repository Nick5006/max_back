from unittest.mock import patch

from apihandler.models import Choice, Notification, Poll, Vote

from .base import ApiTestCase


class PollApiTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.other_org = self.create_org(name="Другая УК", inn="9999999999")
        self.uk = self.create_user(
            max_id="uk",
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
        self.user = self.create_user(max_id="resident", name="Житель")
        self.second_user = self.create_user(max_id="resident-2", name="Житель 2")
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)
        self.second_apartment = self.create_apartment(self.domik, number="43")
        self.link_apartment(self.user, self.apartment, is_primary=True)
        self.link_apartment(self.second_user, self.second_apartment, is_primary=True)
        self.poll = self.create_poll(author=self.uk, domik=self.domik, title="Нужен шлагбаум?")
        self.choice_yes, self.choice_no = list(self.poll.choices.all())

        self.foreign_domik = self.create_domik(
            address="Чужой дом",
            fias_id="foreign",
            management_org=self.other_org,
        )
        self.foreign_poll = self.create_poll(
            author=self.other_uk,
            domik=self.foreign_domik,
            title="Чужой опрос",
        )

    def test_user_poll_list_contains_only_linked_houses(self):
        self.login_as(self.user)
        response = self.client.get("/api/v1/user/polls")

        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.json()["polls"]]
        self.assertEqual(ids, [str(self.poll.id)])

    def test_poll_detail_is_available_to_resident_and_uk_of_same_org(self):
        self.login_as(self.user)
        resident_response = self.client.get(f"/api/v1/user/polls/{self.poll.id}")
        self.assertEqual(resident_response.status_code, 200)
        self.assertEqual(len(resident_response.json()["choices"]), 2)

        self.client.logout()
        self.login_as(self.uk)
        uk_response = self.client.get(f"/api/v1/user/polls/{self.poll.id}")
        self.assertEqual(uk_response.status_code, 200)

        foreign = self.client.get(f"/api/v1/user/polls/{self.foreign_poll.id}")
        self.assertEqual(foreign.status_code, 404)

    def test_vote_creates_then_changes_single_vote(self):
        self.login_as(self.user)

        created = self.post_json(
            f"/api/v1/user/polls/{self.poll.id}/vote",
            {"choice_id": str(self.choice_yes.id)},
        )
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.json()["created"])
        self.assertEqual(Vote.objects.filter(poll=self.poll, user=self.user).count(), 1)

        changed = self.post_json(
            f"/api/v1/user/polls/{self.poll.id}/vote",
            {"choice_id": str(self.choice_no.id)},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertFalse(changed.json()["created"])
        vote = Vote.objects.get(poll=self.poll, user=self.user)
        self.assertEqual(vote.choice_id, self.choice_no.id)
        self.assertEqual(Vote.objects.filter(poll=self.poll, user=self.user).count(), 1)

    def test_vote_rejects_uk_closed_poll_and_choice_from_another_poll(self):
        self.login_as(self.uk)
        uk_vote = self.post_json(
            f"/api/v1/user/polls/{self.poll.id}/vote",
            {"choice_id": str(self.choice_yes.id)},
        )
        self.assertEqual(uk_vote.status_code, 403)

        self.client.logout()
        self.login_as(self.user)
        self.poll.is_active = False
        self.poll.save(update_fields=["is_active"])
        closed = self.post_json(
            f"/api/v1/user/polls/{self.poll.id}/vote",
            {"choice_id": str(self.choice_yes.id)},
        )
        self.assertEqual(closed.status_code, 400)

        self.poll.is_active = True
        self.poll.save(update_fields=["is_active"])
        foreign_choice = self.foreign_poll.choices.first()
        wrong_choice = self.post_json(
            f"/api/v1/user/polls/{self.poll.id}/vote",
            {"choice_id": str(foreign_choice.id)},
        )
        self.assertEqual(wrong_choice.status_code, 404)

    def test_results_calculate_vote_counts_and_percentages(self):
        Vote.objects.create(poll=self.poll, choice=self.choice_yes, user=self.user)
        Vote.objects.create(poll=self.poll, choice=self.choice_no, user=self.second_user)
        self.login_as(self.user)

        response = self.client.get(f"/api/v1/user/polls/{self.poll.id}/results")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_votes"], 2)
        by_id = {item["id"]: item for item in response.json()["results"]}
        self.assertEqual(by_id[str(self.choice_yes.id)]["votes_count"], 1)
        self.assertEqual(by_id[str(self.choice_yes.id)]["percent"], 50.0)
        self.assertEqual(by_id[str(self.choice_no.id)]["percent"], 50.0)

    @patch("apihandler.views._send_to_domik_users")
    def test_uk_create_poll_persists_choices_and_notifies_house(self, send_to_users):
        self.login_as(self.uk)
        response = self.post_json(
            "/api/v1/uk/polls",
            {
                "domik_id": str(self.domik.id),
                "title": "Цвет подъезда",
                "description": "Выберите вариант",
                "choices": ["Светлый", {"text": "Тёмный"}],
            },
        )

        self.assertEqual(response.status_code, 201)
        poll = Poll.objects.get(title="Цвет подъезда")
        self.assertEqual(poll.author_id, self.uk.id)
        self.assertEqual(
            list(poll.choices.order_by("order").values_list("text", flat=True)),
            ["Светлый", "Тёмный"],
        )
        send_to_users.assert_called_once()
        self.assertEqual(send_to_users.call_args.args[0], self.domik)

    def test_uk_create_poll_validates_choices_and_house_scope(self):
        self.login_as(self.uk)
        too_few = self.post_json(
            "/api/v1/uk/polls",
            {
                "domik_id": str(self.domik.id),
                "title": "Опрос",
                "choices": ["Один"],
            },
        )
        self.assertEqual(too_few.status_code, 400)

        duplicates = self.post_json(
            "/api/v1/uk/polls",
            {
                "domik_id": str(self.domik.id),
                "title": "Опрос",
                "choices": ["Да", "Да"],
            },
        )
        self.assertEqual(duplicates.status_code, 400)

        foreign = self.post_json(
            "/api/v1/uk/polls",
            {
                "domik_id": str(self.foreign_domik.id),
                "title": "Опрос",
                "choices": ["Да", "Нет"],
            },
        )
        self.assertEqual(foreign.status_code, 404)

    @patch("apihandler.views._send_to_domik_users")
    def test_uk_can_close_own_poll_but_not_foreign_poll(self, send_to_users):
        self.login_as(self.uk)
        own = self.post_json(f"/api/v1/uk/polls/{self.poll.id}/close", {})
        self.assertEqual(own.status_code, 200)
        self.poll.refresh_from_db()
        self.assertFalse(self.poll.is_active)
        send_to_users.assert_called_once()

        foreign = self.post_json(f"/api/v1/uk/polls/{self.foreign_poll.id}/close", {})
        self.assertEqual(foreign.status_code, 403)

    def test_uk_delete_poll_is_scoped_to_org(self):
        self.login_as(self.uk)
        foreign = self.client.delete(f"/api/v1/uk/polls/{self.foreign_poll.id}")
        self.assertEqual(foreign.status_code, 403)
        self.assertTrue(Poll.objects.filter(pk=self.foreign_poll.pk).exists())

        own = self.client.delete(f"/api/v1/uk/polls/{self.poll.id}")
        self.assertEqual(own.status_code, 200)
        self.assertFalse(Poll.objects.filter(pk=self.poll.pk).exists())


class NotificationApiTests(ApiTestCase):
    def setUp(self):
        self.org = self.create_org()
        self.other_org = self.create_org(name="Другая УК", inn="9999999999")
        self.uk = self.create_user(
            max_id="uk",
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
        self.user = self.create_user(max_id="resident", name="Житель")
        self.domik = self.create_domik(management_org=self.org)
        self.apartment = self.create_apartment(self.domik)
        self.link_apartment(self.user, self.apartment, is_primary=True)
        self.foreign_domik = self.create_domik(
            address="Чужой дом",
            fias_id="foreign",
            management_org=self.other_org,
        )
        self.foreign_apartment = self.create_apartment(self.foreign_domik, number="1")

    @patch("apihandler.views._send_to_domik_users")
    def test_uk_create_notification_persists_and_notifies(self, send_to_users):
        self.login_as(self.uk)
        response = self.post_json(
            "/api/v1/uk/notifications",
            {
                "domik_id": str(self.domik.id),
                "title": "Отключение воды",
                "text": "С 10:00 до 12:00",
            },
        )

        self.assertEqual(response.status_code, 201)
        notification = Notification.objects.get(title="Отключение воды")
        self.assertEqual(notification.domik_id, self.domik.id)
        self.assertEqual(notification.created_by_id, self.uk.id)
        send_to_users.assert_called_once()

    def test_uk_notification_endpoints_are_scoped_to_org(self):
        own = Notification.objects.create(
            domik=self.domik,
            created_by=self.uk,
            title="Своё",
            text="Текст",
        )
        foreign = Notification.objects.create(
            domik=self.foreign_domik,
            created_by=self.other_uk,
            title="Чужое",
            text="Текст",
        )
        self.login_as(self.uk)

        listing = self.client.get("/api/v1/uk/notifications")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(
            [item["id"] for item in listing.json()["notifications"]],
            [str(own.id)],
        )

        own_detail = self.client.get(f"/api/v1/uk/notifications/{own.id}")
        self.assertEqual(own_detail.status_code, 200)

        foreign_detail = self.client.get(f"/api/v1/uk/notifications/{foreign.id}")
        self.assertEqual(foreign_detail.status_code, 404)

    def test_resident_sees_notifications_only_for_linked_houses_without_duplicates(self):
        own = Notification.objects.create(
            domik=self.domik,
            created_by=self.uk,
            title="Своё",
            text="Текст",
        )
        foreign = Notification.objects.create(
            domik=self.foreign_domik,
            created_by=self.other_uk,
            title="Чужое",
            text="Текст",
        )
        second_apartment = self.create_apartment(self.domik, number="43")
        self.link_apartment(self.user, second_apartment)
        self.login_as(self.user)

        listing = self.client.get("/api/v1/user/notifications")
        self.assertEqual(listing.status_code, 200)
        ids = [item["id"] for item in listing.json()["notifications"]]
        self.assertEqual(ids, [str(own.id)])
        self.assertNotIn(str(foreign.id), ids)

        own_detail = self.client.get(f"/api/v1/user/notifications/{own.id}")
        self.assertEqual(own_detail.status_code, 200)
        self.assertEqual(own_detail.json()["management_org"]["id"], str(self.org.id))

        foreign_detail = self.client.get(f"/api/v1/user/notifications/{foreign.id}")
        self.assertEqual(foreign_detail.status_code, 404)

    def test_uk_cannot_create_notification_for_foreign_house(self):
        self.login_as(self.uk)
        response = self.post_json(
            "/api/v1/uk/notifications",
            {
                "domik_id": str(self.foreign_domik.id),
                "title": "Чужое",
                "text": "Текст",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Notification.objects.count(), 0)
