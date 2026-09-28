from django.core.management.base import BaseCommand
from django.db import transaction

from apihandler.models import (
    ManagementOrganization,
    User,
    Domik,
    Apartment,
    ApartmentKey,
)


# Тестовые данные (совпадают с README.md и DATA-API.yaml)
ORG_NAME = "УК Тест"
ORG_INN = "1234567890"

UK_MAX_ID = "uk_demo"
UK_NAME = "Сотрудник"
UK_LAST_NAME = "УК"
UK_PASSWORD = "uk_demo_pass"

RESIDENT_MAX_ID = "resident_demo"
RESIDENT_NAME = "Иван"
RESIDENT_LAST_NAME = "Жильцов"
RESIDENT_PASSWORD = "resident_pass"

DOMIK_ADDRESS = "г. Тест, ул. Тестовая, д. 1"
DOMIK_FIAS_ID = "demo-fias-1"

APARTMENTS_COUNT = 10
APARTMENT_ENTRANCE = "1"

BIND_CODE = "1234567890"
BIND_APARTMENT_NUMBER = "1"


class Command(BaseCommand):
    help = "Создаёт тестовые данные для проверки основного сценария"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующие демо-данные перед созданием",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        org = self._create_org()
        uk = self._create_uk(org)
        resident = self._create_resident()
        domik = self._create_domik(org)
        apartments = self._create_apartments(domik)
        key = self._create_bind_key(apartments[0], uk)

        self._print_summary(org, uk, resident, domik, apartments, key)

    def _reset(self):
        self.stdout.write(self.style.WARNING("Удаляю старые демо-данные..."))
        Domik.objects.filter(fias_id=DOMIK_FIAS_ID).delete()
        User.objects.filter(max_id__in=[UK_MAX_ID, RESIDENT_MAX_ID]).delete()
        ManagementOrganization.objects.filter(inn=ORG_INN).delete()

    def _create_org(self):
        org, created = ManagementOrganization.objects.update_or_create(
            inn=ORG_INN,
            defaults={"name": ORG_NAME},
        )
        self.stdout.write(f"УК {'создана' if created else 'обновлена'}: {org}")
        return org

    def _create_uk(self, org):
        uk = User.objects.filter(max_id=UK_MAX_ID).first()
        created = uk is None

        if uk is None:
            uk = User.objects.create_jkuser(
                max_id=UK_MAX_ID,
                name=UK_NAME,
                last_name=UK_LAST_NAME,
                management_org=org,
            )
        else:
            uk.name = UK_NAME
            uk.last_name = UK_LAST_NAME
            uk.management_org = org
            uk.is_jk = True
            uk.is_active = True

        uk.set_password(UK_PASSWORD)
        uk.save()
        self.stdout.write(
            f"Сотрудник УК {'создан' if created else 'обновлён'}: {uk.max_id}"
        )
        return uk

    def _create_resident(self):
        resident = User.objects.filter(max_id=RESIDENT_MAX_ID).first()
        created = resident is None

        if resident is None:
            resident = User.objects.create_user(
                max_id=RESIDENT_MAX_ID,
                name=RESIDENT_NAME,
                last_name=RESIDENT_LAST_NAME,
            )
        else:
            resident.name = RESIDENT_NAME
            resident.last_name = RESIDENT_LAST_NAME
            resident.is_active = True

        resident.set_password(RESIDENT_PASSWORD)
        resident.save()
        self.stdout.write(
            f"Житель {'создан' if created else 'обновлён'}: {resident.max_id}"
        )
        return resident

    def _create_domik(self, org):
        domik, created = Domik.objects.update_or_create(
            fias_id=DOMIK_FIAS_ID,
            defaults={
                "address": DOMIK_ADDRESS,
                "management_org": org,
            },
        )
        self.stdout.write(f"Дом {'создан' if created else 'обновлён'}: {domik}")
        return domik

    def _create_apartments(self, domik):
        apartments = []
        created_count = 0

        for i in range(1, APARTMENTS_COUNT + 1):
            apartment, created = Apartment.objects.update_or_create(
                domik=domik,
                number=str(i),
                defaults={"entrance": APARTMENT_ENTRANCE},
            )
            apartments.append(apartment)
            if created:
                created_count += 1

        self.stdout.write(
            f"Квартиры: всего {len(apartments)}, создано {created_count}"
        )
        return apartments

    def _create_bind_key(self, apartment, uk):
        ApartmentKey.objects.filter(
            apartment=apartment,
            purpose=ApartmentKey.Purpose.BIND,
        ).delete()

        key = ApartmentKey.objects.create(
            apartment=apartment,
            code=BIND_CODE,
            purpose=ApartmentKey.Purpose.BIND,
            created_by=uk,
        )
        self.stdout.write(f"Код привязки: {key.code} (кв. {apartment.number})")
        return key

    def _print_summary(self, org, uk, resident, domik, apartments, key):
        line = "=" * 60
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(line))
        self.stdout.write(self.style.SUCCESS("  Тестовые данные готовы"))
        self.stdout.write(self.style.SUCCESS(line))
        self.stdout.write("")
        self.stdout.write(f"  УК:            {org.name} (ИНН {org.inn})")
        self.stdout.write(f"  Сотрудник УК:  {uk.max_id} / {UK_PASSWORD}")
        self.stdout.write(f"  Житель:        {resident.max_id} / {RESIDENT_PASSWORD}")
        self.stdout.write(f"  Дом:           {domik.address}")
        self.stdout.write(f"  Квартир:       {len(apartments)}")
        self.stdout.write(f"  Код привязки:  {key.code} (кв. {key.apartment.number})")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(line))