import json

from django.test import TestCase

from apihandler.models import (
    Apartment,
    Appeal,
    AppealHistory,
    Choice,
    Domik,
    ManagementOrganization,
    Poll,
    User,
    UserApartment,
)


class ApiTestCase(TestCase):
    def request_json(self, method, url, payload=None):
        data = "" if payload is None else json.dumps(payload)
        return getattr(self.client, method)(
            url,
            data=data,
            content_type="application/json",
        )

    def post_json(self, url, payload=None):
        return self.request_json("post", url, payload)

    def patch_json(self, url, payload=None):
        return self.request_json("patch", url, payload)

    def login_as(self, user):
        self.client.force_login(user)

    def create_org(self, *, name="УК Тест", inn="1234567890"):
        return ManagementOrganization.objects.create(name=name, inn=inn)

    def create_user(
        self,
        *,
        max_id="resident-1",
        name="Иван",
        last_name="Иванов",
        is_jk=False,
        management_org=None,
    ):
        if is_jk:
            return User.objects.create_jkuser(
                max_id=max_id,
                name=name,
                last_name=last_name,
                management_org=management_org,
            )
        return User.objects.create_user(
            max_id=max_id,
            name=name,
            last_name=last_name,
            management_org=management_org,
        )

    def create_domik(
        self,
        *,
        address="г Понск, улица Поновая, д 52",
        fias_id="fias-1",
        management_org=None,
    ):
        return Domik.objects.create(
            address=address,
            fias_id=fias_id,
            management_org=management_org,
        )

    def create_apartment(self, domik, *, number="42", entrance="1"):
        return Apartment.objects.create(
            domik=domik,
            number=number,
            entrance=entrance,
        )

    def link_apartment(
        self,
        user,
        apartment,
        *,
        role=UserApartment.Role.RESIDENT,
        is_primary=False,
    ):
        return UserApartment.objects.create(
            user=user,
            apartment=apartment,
            role=role,
            is_primary=is_primary,
        )

    def create_appeal(
        self,
        *,
        author,
        apartment,
        title="Не работает лифт",
        description="Лифт не работает",
        status=Appeal.Status.NEW,
        history=True,
    ):
        appeal = Appeal.objects.create(
            author=author,
            apartment=apartment,
            domik=apartment.domik,
            title=title,
            description=description,
            status=status,
        )
        if history:
            AppealHistory.objects.create(
                appeal=appeal,
                status=status,
                changed_by=author,
                text="Обращение создано",
            )
        return appeal

    def create_poll(
        self,
        *,
        author,
        domik,
        title="Новый опрос",
        description="Описание",
        choices=("Да", "Нет"),
        is_active=True,
    ):
        poll = Poll.objects.create(
            author=author,
            domik=domik,
            title=title,
            description=description,
            is_active=is_active,
        )
        for order, text in enumerate(choices):
            Choice.objects.create(poll=poll, text=text, order=order)
        return poll
