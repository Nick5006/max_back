from django.core.management.base import BaseCommand
from django.db import transaction

from apihandler.models import Domik
from apihandler.gis_api import data_collector

PAGE_SIZE = 50000
DELETE_BATCH_SIZE = 1000

class Command(BaseCommand):
    help = "Синхронизация домов с реестром"

    def handle(self, *args, **options):
        self.stdout.write("Syncing houses...")

        registry_fias_ids = set()

        first_payload = data_collector.get_houses(PAGE_SIZE, 1)
        meta = first_payload.get("meta", {})
        total_pages = meta.get("last_page", 1)
        total_count = meta.get("total", 0)

        self.stdout.write(f"Total pages: {total_pages}\n"
                          f"Total count: {total_count}")

        first_houses = first_payload.get("data", [])
        registry_fias_ids.update({house.get("fias_guid") for house in first_houses})
        self.sync_page(first_houses, page = 1)

        for page in range(2, total_pages + 1):
            self.stdout.write(f"Loading page {page}/{total_pages}...")

            payload = data_collector.get_houses(PAGE_SIZE, page)
            houses = payload.get("data", [])

            registry_fias_ids.update({house.get("fias_guid") for house in houses})
            self.sync_page(houses, page = page)

        deleted_count = self.delete_missing_houses(registry_fias_ids)

        self.stdout.write(f"DELETED {deleted_count} houses\n")
        self.stdout.write("Synced")

    def delete_missing_houses(self, registry_fias_ids):
        db_fias_ids = set(Domik.objects.exclude(fias_id="").exclude(fias_id__isnull=True).values_list("fias_id", flat=True))

        fias_ids_to_delete = (db_fias_ids - registry_fias_ids)

        if not fias_ids_to_delete:
            return 0

        fias_ids_to_delete = list(fias_ids_to_delete)
        deleted = 0

        for start in range(0, len(fias_ids_to_delete), DELETE_BATCH_SIZE):
            batch = fias_ids_to_delete[start:start+DELETE_BATCH_SIZE]
            queryset = Domik.objects.filter(fias_id__in=batch)
            count = queryset.count()
            queryset.delete()

            deleted += count

        return deleted


    def sync_page(self, houses, page: int):
        if not houses:
            return

        fias_ids = [house["fias_guid"] for house in houses]

        existing = {
            domik.fias_id: domik
            for domik in Domik.objects.filter(
                fias_id__in=fias_ids
            )
        }

        to_create, to_update = [], []

        for house in houses:
            fias_id = house.get("fias_guid")
            address = house.get("address")

            if not fias_id or not address:
                continue

            domik = existing.get(fias_id)

            if not domik:
                to_create.append(Domik(fias_id=fias_id, address=address))

            else:
                if domik.address != address:
                    domik.address = address
                    to_update.append(domik)

        with transaction.atomic():
            if to_create:
                Domik.objects.bulk_create(to_create, batch_size = 1000)

            if to_update:
                Domik.objects.bulk_update(to_update, fields=["address"], batch_size = 1000)

        self.stdout.write(f"Page {page} synced\n"
                          f"Updated: {len(to_update)}\n"
                          f"Created: {len(to_create)}\n")