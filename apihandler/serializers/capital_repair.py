def serialize_capital_repair_work(w):
    return {
        "id": str(w.id),
        "work_type": w.work_type,
        "planned_year": w.planned_year,
        "status": w.status,
        "status_display": w.get_status_display(),
        "cost": str(w.cost) if w.cost is not None else None,
        "contractor": w.contractor,
        "description": w.description,
        "completed_at": w.completed_at,
    }


def serialize_capital_repair(cr):
    if cr is None:
        return None
    return {
        "id": str(cr.id),
        "domik_id": str(cr.domik_id),
        "tariff_per_sqm": str(cr.tariff_per_sqm),
        "collected_total": str(cr.collected_total),
        "spent_total": str(cr.spent_total),
        "balance": str(cr.balance),
        "updated_at": cr.updated_at,
    }