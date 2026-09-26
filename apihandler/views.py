from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
from apihandler.serializers.appeal import AppealCreateSerializer, AppealListSerializer
from apihandler.models import (
    User,
    Apartment,
    Appeal,
    AppealHistory,
    UserApartment,
    ManagementOrganization,
    Domik,
    Poll,
    Choice,
    Vote,
    Notification,
)
from django.db import transaction
from functools import wraps

from apihandler.serializers.notification import NotificationSerializer
from apihandler.serializers.poll import get_user_domik_ids, serialize_poll_choice, serialize_poll
from django.db.models import Count, Prefetch, Q
from django.db import IntegrityError


def api_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"status": "Не авторизован"}, status=401)
        return view(request, *args, **kwargs)
    return wrapper

def uk_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"status": "Не авторизован"}, status=401)
        if not request.user.is_jk:
            return JsonResponse({"status": "Только для сотрудников УК"}, status=403)
        if not request.user.management_org_id:
            return JsonResponse({"status": "Нет привязки к УК"}, status=403)
        return view(request, *args, **kwargs)

    return wrapper


def serialize_management_org(org):
    if org is None:
        return None
    return {"id": str(org.id), "name": org.name}


MAX_APARTMENTS_PER_HOUSE = 1000


def parse_json(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({'status': 'Некорректный JSON'}, status=400)
    if not isinstance(data, dict):
        return None, JsonResponse(
            {'status': 'Тело запроса должно быть JSON-объектом'},
            status=400,
        )
    return data, None


@csrf_exempt
@require_POST
def login_view(request):
    data, error = parse_json(request)
    if error:
        return error

    max_id = data.get("max_id")
    name = data.get("name")

    if not max_id or not name:
        return JsonResponse({'status': 'Нужны поля max_id и name'}, status=400)

    if User.objects.filter(max_id=max_id).exists():
        user = User.objects.get(max_id=max_id)
        login(request, user)
        return JsonResponse(
            {
                'status': 'Такой пользователь уже существует',
                'id': str(user.id),
                'is_jk': user.is_jk,
            },
            status=200,
        )

    is_jk = data.get("is_jk", False)

    if is_jk:
        management_data = data.get("management_org")

        if not management_data:
            return JsonResponse(
                {"status": "Для сотрудника УК необходимо указать management_org"},
                status=400,
            )

        org_name = management_data.get("name")
        org_inn = management_data.get("inn")

        if not org_name or not org_inn:
            return JsonResponse(
                {"status": "Для management_org нужны поля name и inn"},
                status=400,
            )

        management_org, created = ManagementOrganization.objects.get_or_create(
            inn=org_inn,
            defaults={"name": org_name},
        )

        try:
            user = User.objects.create_jkuser(
                max_id=max_id,
                name=name,
                management_org=management_org,
            )
        except ValueError as e:
            return JsonResponse({'status': str(e)}, status=400)

    else:
        try:
            user = User.objects.create_user(max_id=max_id, name=name)
        except ValueError as e:
            return JsonResponse({'status': str(e)}, status=400)

    login(request, user)
    return JsonResponse({
        "status": "ok",
        "id": str(user.id),
        "is_jk": user.is_jk,
        "management_org": (
            {
                "id": str(user.management_org.id),
                "name": user.management_org.name,
                "inn": user.management_org.inn,
            }
            if user.management_org
            else None
        ),
    }, status=200)


@csrf_exempt
@api_login_required
def appeals_view(request):
    if request.method == "GET":
        return get_appeals(request)

    if request.method == "POST":
        return create_appeal(request)

    return JsonResponse(
        {"status": "Method not allowed"},
        status=405,
    )


def create_appeal(request):
    data, error = parse_json(request)
    if error:
        return error

    serializer = AppealCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    apartment = Apartment.objects.filter(
        id=data["apartment_id"],
        user_apartments__user=request.user,
    ).first()

    if apartment is None:
        return JsonResponse({"status": "Квартира не найдена"}, status=404)

    appeal = Appeal.objects.create(
        author=request.user,
        apartment=apartment,
        domik=apartment.domik,
        title=data["title"],
        description=data["description"],
        status=Appeal.Status.NEW,
    )

    AppealHistory.objects.create(
        appeal=appeal,
        status=Appeal.Status.NEW,
        changed_by=request.user,
    )

    return JsonResponse({
        "id": str(appeal.id),
        "title": appeal.title,
        "description": appeal.description,
        "management_org": serialize_management_org(apartment.domik.management_org),
        "status": appeal.status,
        "created_at": appeal.created_at,
    }, status=201)


def get_appeals(request):
    appeals = (
        Appeal.objects
        .filter(author=request.user)
        .select_related("apartment", "domik")
        .order_by("-created_at")
    )
    serializer = AppealListSerializer(appeals, many=True)

    return JsonResponse({"appeals": serializer.data}, status=200)


@csrf_exempt
@api_login_required
def me_view(request):
    user = request.user
    user_apartments = user.user_apartments.select_related("apartment__domik")

    return JsonResponse({
        "id": str(user.id),
        "max_id": user.max_id,
        "name": user.name,
        "last_name": user.last_name,
        "is_jk": user.is_jk,
        "management_org": serialize_management_org(user.management_org),
        "apartments": [
            {
                "id": str(ua.apartment.id),
                "number": ua.apartment.number,
                "entrance": ua.apartment.entrance,
                "domik_id": str(ua.apartment.domik.id),
                "domik_address": ua.apartment.domik.address,
                "management_org": serialize_management_org(
                    ua.apartment.domik.management_org
                ),
                "role": ua.role,
                "role_display": ua.get_role_display(),
                "is_primary": ua.is_primary,
            }
            for ua in user_apartments
        ],
    })


@csrf_exempt
@api_login_required
def apartments_view(request):
    if request.method == "GET":
        return list_user_apartments(request)
    if request.method == "POST":
        return create_apartment(request)
    return JsonResponse({"status": "Method not allowed"}, status=405)


def list_user_apartments(request):
    user_apartments = request.user.user_apartments.select_related("apartment__domik")

    return JsonResponse({
        "apartments": [
            {
                "id": str(ua.apartment.id),
                "number": ua.apartment.number,
                "entrance": ua.apartment.entrance,
                "domik_id": str(ua.apartment.domik.id),
                "domik_address": ua.apartment.domik.address,
                "management_org": serialize_management_org(
                    ua.apartment.domik.management_org
                ),
                "role": ua.role,
                "role_display": ua.get_role_display(),
                "is_primary": ua.is_primary,
            }
            for ua in user_apartments
        ],
    }, status=200)


def create_apartment(request):
    data, error = parse_json(request)
    if error:
        return error

    domik_id = data.get("domik_id")
    number = data.get("number")

    if not domik_id or not number:
        return JsonResponse(
            {"status": "Поля domik_id и number обязательны"},
            status=400,
        )

    apartment = Apartment.objects.filter(domik_id=domik_id, number=number).first()

    if apartment is None:
        return JsonResponse({"status": "Квартира не найдена"}, status=404)

    is_first = not UserApartment.objects.filter(user=request.user).exists()

    user_apartment, created = UserApartment.objects.get_or_create(
        user=request.user,
        apartment=apartment,
        defaults={
            "role": UserApartment.Role.RESIDENT,
            "is_primary": is_first,
        },
    )

    if not created:
        return JsonResponse({"status": "Квартира уже добавлена"}, status=409)

    return JsonResponse({
        "id": str(apartment.id),
        "number": apartment.number,
        "domik_id": str(apartment.domik_id),
        "role": user_apartment.role,
        "is_primary": user_apartment.is_primary,
    }, status=201)


@csrf_exempt
@api_login_required
@require_GET
def appeal_detail_view(request, appeal_id):
    appeal = Appeal.objects.filter(
        id=appeal_id,
        author=request.user,
    ).select_related("domik", "apartment").first()

    if appeal is None:
        return JsonResponse({"status": "Обращение не найдено"}, status=404)

    history = appeal.appeal_history.select_related("changed_by").all()

    return JsonResponse({
        "id": str(appeal.id),
        "title": appeal.title,
        "description": appeal.description,
        "status": appeal.status,
        "status_display": appeal.get_status_display(),
        "domik": {
            "id": str(appeal.domik.id),
            "address": appeal.domik.address,
            "management_org": serialize_management_org(appeal.domik.management_org),
        },
        "apartment": {
            "id": str(appeal.apartment.id),
            "number": appeal.apartment.number,
        } if appeal.apartment else None,
        "created_at": appeal.created_at,
        "updated_at": appeal.updated_at,
        "history": [
            {
                "status": h.status,
                "status_display": h.get_status_display(),
                "text": h.text,
                "changed_by": h.changed_by.name if h.changed_by else None,
                "changed_at": h.changed_at,
            }
            for h in history
        ],
    })


@csrf_exempt
@uk_required
def uk_domiks_view(request):
    if request.method == "GET":
        return list_uk_domiks(request)
    if request.method == "POST":
        return create_domik(request)
    return JsonResponse({"status": "Method not allowed"}, status=405)


def list_uk_domiks(request):
    domiks = (
        Domik.objects
        .filter(management_org=request.user.management_org)
        .order_by("address")
    )

    return JsonResponse({
        "domiks": [
            {
                "id": str(d.id),
                "address": d.address,
                "fias_id": d.fias_id,
                "management_org": serialize_management_org(d.management_org),
                "apartments_count": d.apartments.count(),
                "appeals_count": d.appeals.count(),
                "new_appeals_count": d.appeals.filter(
                    status=Appeal.Status.NEW
                ).count(),
                "created_at": d.created_at,
            }
            for d in domiks
        ],
    }, status=200)


def create_domik(request):
    management_org = request.user.management_org

    if not management_org:
        return JsonResponse({"status": "Нет привязки к УК"}, status=403)

    data, error = parse_json(request)
    if error:
        return error

    address = (data.get("address") or "").strip()
    fias_id = (data.get("fias_id") or "").strip()
    apartments = data.get("apartments") or {}

    if not address:
        return JsonResponse({"status": "Поле address обязательно"}, status=400)

    if fias_id and Domik.objects.filter(fias_id=fias_id).exists():
        return JsonResponse(
            {"status": "Дом с таким ФИАС ID уже существует"},
            status=409,
        )

    if Domik.objects.filter(address=address).exists():
        return JsonResponse(
            {"status": "Дом с таким адресом уже существует"},
            status=409,
        )

    from_num = apartments.get("from")
    to_num = apartments.get("to")
    entrance = (apartments.get("entrance") or "").strip()

    if from_num is None or to_num is None:
        return JsonResponse(
            {"status": "Нужны apartments.from и apartments.to"},
            status=400,
        )

    try:
        from_num = int(from_num)
        to_num = int(to_num)
    except (ValueError, TypeError):
        return JsonResponse(
            {"status": "from и to должны быть целыми числами"},
            status=400,
        )

    if from_num < 1:
        return JsonResponse({"status": "from должен быть >= 1"}, status=400)

    if to_num < from_num:
        return JsonResponse({"status": "to должен быть >= from"}, status=400)

    total = to_num - from_num + 1
    if total > MAX_APARTMENTS_PER_HOUSE:
        return JsonResponse(
            {
                "status": (
                    f"Слишком большой диапазон: "
                    f"макс {MAX_APARTMENTS_PER_HOUSE} квартир"
                ),
            },
            status=400,
        )

    with transaction.atomic():
        domik = Domik.objects.create(
            address=address,
            fias_id=fias_id,
            management_org=management_org,
        )

        apartments_to_create = [
            Apartment(domik=domik, number=str(n), entrance=entrance)
            for n in range(from_num, to_num + 1)
        ]
        Apartment.objects.bulk_create(apartments_to_create)

    return JsonResponse({
        "status": "ok",
        "domik_id": str(domik.id),
        "address": domik.address,
        "management_org": serialize_management_org(management_org),
        "apartments_created": len(apartments_to_create),
    }, status=201)


@csrf_exempt
@uk_required
def uk_domik_detail_or_delete_view(request, domik_id):
    management_org = request.user.management_org

    if request.method == "GET":
        domik = Domik.objects.filter(
            id=domik_id,
            management_org=management_org,
        ).first()

        if domik is None:
            return JsonResponse(
                {"status": "Дом не найден или нет доступа"},
                status=404,
            )

        apartments = domik.apartments.order_by("number")

        return JsonResponse({
            "id": str(domik.id),
            "address": domik.address,
            "fias_id": domik.fias_id,
            "management_org": serialize_management_org(domik.management_org),
            "created_at": domik.created_at,
            "apartments": [
                {
                    "id": str(a.id),
                    "number": a.number,
                    "entrance": a.entrance,
                    "residents_count": a.user_apartments.count(),
                }
                for a in apartments
            ],
        })

    if request.method == "DELETE":
        deleted, _ = Domik.objects.filter(
            id=domik_id,
            management_org=management_org,
        ).delete()
        if not deleted:
            return JsonResponse({"status": "Дом не найден"}, status=404)
        return JsonResponse({"status": "ok"}, status=200)

    return JsonResponse({"status": "Неправильный метод"}, status=405)


@csrf_exempt
@require_POST
@uk_required
def uk_update_appeal_status_view(request, appeal_id):
    appeal = Appeal.objects.filter(
        id=appeal_id,
        domik__management_org=request.user.management_org,
    ).first()

    if appeal is None:
        return JsonResponse({"status": "Обращение не найдено"}, status=404)

    data, error = parse_json(request)
    if error:
        return error

    new_status = data.get("status")
    text = (data.get("text") or "").strip()

    valid_statuses = dict(Appeal.Status.choices)
    if new_status not in valid_statuses:
        return JsonResponse({
            "status": "Некорректный статус",
            "allowed": list(valid_statuses.keys()),
        }, status=400)

    with transaction.atomic():
        appeal.status = new_status
        appeal.save(update_fields=["status", "updated_at"])

        AppealHistory.objects.create(
            appeal=appeal,
            status=new_status,
            changed_by=request.user,
            text=text,
        )

    return JsonResponse({
        "status": "ok",
        "appeal_id": str(appeal.id),
        "new_status": appeal.status,
        "status_display": appeal.get_status_display(),
    })


@csrf_exempt
@uk_required
def uk_appeals_view(request):
    status_filter = request.GET.get("status")
    domik_id = request.GET.get("domik_id")

    qs = (
        Appeal.objects
        .filter(domik__management_org=request.user.management_org)
        .select_related("author", "domik", "apartment")
        .order_by("-created_at")
    )

    if status_filter:
        qs = qs.filter(status=status_filter)
    if domik_id:
        qs = qs.filter(domik_id=domik_id)

    return JsonResponse({
        "appeals": [
            {
                "id": str(a.id),
                "title": a.title,
                "status": a.status,
                "status_display": a.get_status_display(),
                "author": {
                    "id": str(a.author.id),
                    "name": a.author.name,
                    "last_name": a.author.last_name,
                },
                "domik_id": str(a.domik.id),
                "domik_address": a.domik.address,
                "apartment_number": a.apartment.number if a.apartment else None,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
            }
            for a in qs
        ],
    })


@csrf_exempt
@api_login_required
def polls_view(request):
    if request.method == "GET":
        return list_polls(request)
    return JsonResponse({"status": "Method not allowed"}, status=405)


def list_polls(request):
    domik_ids = get_user_domik_ids(request.user)

    polls = (
        Poll.objects
        .filter(domik_id__in=domik_ids)
        .select_related("author", "domik")
        .prefetch_related(
            Prefetch(
                "choices",
                queryset=Choice.objects.annotate(votes_count=Count("votes")),
            )
        )
        .annotate(total_votes=Count("votes"))
    )

    domik_id = request.GET.get("domik_id")
    if domik_id:
        polls = polls.filter(domik_id=domik_id)

    only_active = request.GET.get("active")
    if only_active == "1":
        polls = polls.filter(is_active=True)

    return JsonResponse({
        "polls": [serialize_poll(p, request) for p in polls],
    }, status=200)

def _poll_accessible_q(user):
    q = Q(domik_id__in=get_user_domik_ids(user))
    if user.is_jk and user.management_org_id:
        q |= Q(domik__management_org_id=user.management_org_id)
    return q

@csrf_exempt
@api_login_required
def poll_detail_view(request, poll_id):
    poll = (
        Poll.objects
        .filter(_poll_accessible_q(request.user), id=poll_id)
        .select_related("author", "domik")
        .prefetch_related(
            Prefetch(
                "choices",
                queryset=Choice.objects.annotate(votes_count=Count("votes")),
            )
        )
        .first()
    )

    if poll is None:
        return JsonResponse({"status": "Опрос не найден"}, status=404)

    return JsonResponse(serialize_poll(poll, request), status=200)


@csrf_exempt
@require_POST
@api_login_required
def poll_vote_view(request, poll_id):
    if request.user.is_jk:
        return JsonResponse(
            {"status": "Сотрудники УК не голосуют"}, status=403
        )

    poll = Poll.objects.filter(
        _poll_accessible_q(request.user), id=poll_id
    ).first()

    if poll is None:
        return JsonResponse({"status": "Опрос не найден"}, status=404)

    if not poll.is_active:
        return JsonResponse({"status": "Опрос закрыт"}, status=400)

    data, error = parse_json(request)
    if error:
        return error

    choice_id = data.get("choice_id")
    if not choice_id:
        return JsonResponse({"status": "Поле choice_id обязательно"}, status=400)

    choice = Choice.objects.filter(id=choice_id, poll=poll).first()
    if choice is None:
        return JsonResponse(
            {"status": "Вариант не найден в этом опросе"}, status=404
        )

    vote, created = Vote.objects.update_or_create(
        poll=poll,
        user=request.user,
        defaults={"choice": choice},
    )

    total_votes = poll.votes.count()

    return JsonResponse({
        "status": "ok",
        "created": created,
        "poll_id": str(poll.id),
        "choice_id": str(choice.id),
        "total_votes": total_votes,
    }, status=201 if created else 200)

@csrf_exempt
@api_login_required
def poll_results_view(request, poll_id):
    poll = (
        Poll.objects
        .filter(_poll_accessible_q(request.user), id=poll_id)
        .select_related("author", "domik")
        .first()
    )
    if poll is None:
        return JsonResponse({"status": "Опрос не найден"}, status=404)

    choices = (
        poll.choices
        .annotate(votes_count=Count("votes"))
        .order_by("-votes_count", "order")
    )
    total = sum(c.votes_count for c in choices)

    results = []
    for c in choices:
        percent = round(c.votes_count * 100 / total, 1) if total else 0.0
        results.append({
            "id": str(c.id),
            "text": c.text,
            "votes_count": c.votes_count,
            "percent": percent,
        })

    return JsonResponse({
        "poll_id": str(poll.id),
        "title": poll.title,
        "total_votes": total,
        "results": results,
    }, status=200)

def create_poll(request):
    data, error = parse_json(request)
    if error:
        return error

    domik_id = data.get("domik_id")
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    choices_data = data.get("choices") or []

    if not domik_id:
        return JsonResponse({"status": "Поле domik_id обязательно"}, status=400)
    if not title:
        return JsonResponse({"status": "Поле title обязательно"}, status=400)
    if not isinstance(choices_data, list) or len(choices_data) < 2:
        return JsonResponse(
            {"status": "Нужно минимум 2 варианта ответа"}, status=400
        )

    domik = Domik.objects.filter(
        id=domik_id,
        management_org=request.user.management_org,
    ).first()
    if domik is None:
        return JsonResponse(
            {"status": "Дом не найден или нет доступа"}, status=404
        )

    texts = []
    for c in choices_data:
        if isinstance(c, dict):
            t = (c.get("text") or "").strip()
        else:
            t = (c or "").strip()
        if t:
            texts.append(t)

    if len(texts) < 2:
        return JsonResponse(
            {"status": "Нужно минимум 2 непустых варианта"}, status=400
        )

    if len(set(texts)) != len(texts):
        return JsonResponse(
            {"status": "Варианты не должны повторяться"}, status=400
        )

    with transaction.atomic():
        poll = Poll.objects.create(
            author=request.user,
            domik=domik,
            title=title,
            description=description,
        )
        Choice.objects.bulk_create([
            Choice(poll=poll, text=t, order=i) for i, t in enumerate(texts)
        ])

    poll = (
        Poll.objects
        .select_related("author", "domik")
        .prefetch_related("choices")
        .get(pk=poll.pk)
    )
    return JsonResponse(serialize_poll(poll, request), status=201)


@csrf_exempt
@require_POST
@uk_required
def uk_poll_close_view(request, poll_id):
    poll = (
        Poll.objects
        .filter(id=poll_id)
        .select_related("domik")
        .first()
    )
    if poll is None:
        return JsonResponse({"status": "Опрос не найден"}, status=404)

    if poll.domik.management_org_id != request.user.management_org_id:
        return JsonResponse({"status": "Нет прав"}, status=403)

    poll.is_active = False
    poll.save(update_fields=["is_active"])

    return JsonResponse({
        "status": "ok",
        "poll_id": str(poll.id),
        "is_active": poll.is_active,
    }, status=200)


@csrf_exempt
@uk_required
def uk_poll_delete_view(request, poll_id):
    if request.method != "DELETE":
        return JsonResponse({"status": "Method not allowed"}, status=405)

    poll = (
        Poll.objects
        .filter(id=poll_id)
        .select_related("domik")
        .first()
    )
    if poll is None:
        return JsonResponse({"status": "Опрос не найден"}, status=404)

    if poll.domik.management_org_id != request.user.management_org_id:
        return JsonResponse({"status": "Нет прав"}, status=403)

    poll.delete()
    return JsonResponse({"status": "ok"}, status=200)

@csrf_exempt
@uk_required
def uk_polls_view(request):
    if request.method == "GET":
        polls = (
            Poll.objects
            .filter(domik__management_org=request.user.management_org)
            .select_related("author", "domik")
            .prefetch_related(
                Prefetch(
                    "choices",
                    queryset=Choice.objects.annotate(votes_count=Count("votes")),
                )
            )
            .annotate(total_votes=Count("votes"))
        )

        domik_id = request.GET.get("domik_id")
        if domik_id:
            polls = polls.filter(domik_id=domik_id)

        return JsonResponse({
            "polls": [serialize_poll(p, request) for p in polls],
        }, status=200)

    if request.method == "POST":
        return create_poll(request)

    return JsonResponse({"status": "Method not allowed"}, status=405)

@csrf_exempt
@uk_required
def uk_notifications_view(request):
    if request.method == "GET":
        return uk_get_notifications(request)

    elif request.method == "POST":
        return uk_create_notification(request)

    else:
        return JsonResponse({"status": "Method not allowed"}, status=405)

def uk_create_notification(request):
    data, error = parse_json(request)

    if error:
        return JsonResponse({"status": error}, status=400)

    serializer = NotificationSerializer(data=data)

    if not serializer.is_valid():
        return JsonResponse({"status": serializer.errors}, status=400)

    data = serializer.data
    domik = Domik.objects.filter(id=data["domik_id"], management_org=request.user.management_org).first()

    if domik is None:
        return JsonResponse({"status": "Дом не найден"}, status=404)

    notification = Notification.objects.create(
        domik=domik,
        created_by=request.user,
        title=data["title"],
        text=data["text"],
    )

    return JsonResponse({
        "status": "ok",
        "notification": {
            "id": str(notification.id),
            "title": notification.title,
            "text": notification.text,
            "created_at": notification.created_at,
            "domik": {
                "id": str(domik.id),
                "address": domik.address,
            },
        },
    }, status=201)

def uk_get_notifications(request):
    notifications = (
        Notification.objects
        .filter(
            domik__management_org=request.user.management_org
        )
        .select_related(
            "domik",
            "created_by",
        )
        .order_by("-created_at")
    )

    return JsonResponse({
        "notifications": [
            {
                "id": str(notification.id),
                "title": notification.title,
                "text": notification.text,
                "created_at": notification.created_at,

                "domik": {
                    "id": str(notification.domik.id),
                    "address": notification.domik.address,
                },

                "created_by": (
                    {
                        "id": str(notification.created_by.id),
                        "name": notification.created_by.name,
                    }
                    if notification.created_by
                    else None
                ),
            }
            for notification in notifications
        ],
    })

@csrf_exempt
@api_login_required
@require_GET
def notifications_view(request):
    notifications = (
        Notification.objects
        .filter(
            domik__apartments__user_apartments__user=request.user
        )
        .select_related(
            "domik",
            "domik__management_org",
            "created_by",
        )
        .distinct()
        .order_by("-created_at")
    )

    return JsonResponse({
        "notifications": [
            {
                "id": str(notification.id),
                "title": notification.title,
                "text": notification.text,
                "created_at": notification.created_at,

                "domik": {
                    "id": str(notification.domik.id),
                    "address": notification.domik.address,
                },

                "management_org": (
                    {
                        "id": str(
                            notification.domik.management_org.id
                        ),
                        "name":
                            notification.domik.management_org.name,
                    }
                    if notification.domik.management_org
                    else None
                ),
            }
            for notification in notifications
        ],
    }, status=200)

@csrf_exempt
@uk_required
def uk_apartments_view(request, domik_id):
    domik = Domik.objects.filter(
        id=domik_id,
        management_org=request.user.management_org,
    ).first()

    if domik is None:
        return JsonResponse({"status": "Дом не найден или нет доступа"}, status=404)

    if request.method == "GET":
        apartments = domik.apartments.order_by("number")
        return JsonResponse({
            "domik_id": str(domik.id),
            "address": domik.address,
            "apartments": [
                {
                    "id": str(a.id),
                    "number": a.number,
                    "entrance": a.entrance,
                    "residents_count": a.user_apartments.count(),
                }
                for a in apartments
            ],
        }, status=200)

    if request.method == "POST":
        data, error = parse_json(request)
        if error:
            return error

        number = (data.get("number") or "").strip()
        entrance = (data.get("entrance") or "").strip()

        if not number:
            return JsonResponse({"status": "Поле number обязательно"}, status=400)

        if Apartment.objects.filter(domik=domik, number=number).exists():
            return JsonResponse(
                {"status": f"Квартира с номером {number} уже есть в этом доме"},
                status=409,
            )

        apartment = Apartment.objects.create(
            domik=domik, number=number, entrance=entrance,
        )
        return JsonResponse({
            "status": "ok",
            "id": str(apartment.id),
            "number": apartment.number,
            "entrance": apartment.entrance,
        }, status=201)

    return JsonResponse({"status": "Method not allowed"}, status=405)


@csrf_exempt
@uk_required
def uk_apartment_detail_view(request, domik_id, apartment_id):
    domik = Domik.objects.filter(
        id=domik_id,
        management_org=request.user.management_org,
    ).first()

    if domik is None:
        return JsonResponse({"status": "Дом не найден или нет доступа"}, status=404)

    apartment = Apartment.objects.filter(id=apartment_id, domik=domik).first()
    if apartment is None:
        return JsonResponse({"status": "Квартира не найдена"}, status=404)

    if request.method == "GET":
        residents = apartment.user_apartments.select_related("user").all()
        return JsonResponse({
            "id": str(apartment.id),
            "number": apartment.number,
            "entrance": apartment.entrance,
            "domik_id": str(domik.id),
            "domik_address": domik.address,
            "residents": [
                {
                    "user_id": str(ua.user.id),
                    "max_id": ua.user.max_id,
                    "name": ua.user.name,
                    "last_name": ua.user.last_name,
                    "role": ua.role,
                    "role_display": ua.get_role_display(),
                    "is_primary": ua.is_primary,
                }
                for ua in residents
            ],
            "appeals_count": apartment.appeals.count(),
        }, status=200)

    if request.method == "PATCH":
        data, error = parse_json(request)
        if error:
            return error

        updated_fields = []

        if "number" in data:
            new_number = (data.get("number") or "").strip()
            if not new_number:
                return JsonResponse({"status": "number не может быть пустым"}, status=400)
            if new_number != apartment.number:
                if Apartment.objects.filter(domik=domik, number=new_number).exclude(pk=apartment.pk).exists():
                    return JsonResponse(
                        {"status": f"Квартира с номером {new_number} уже есть в этом доме"},
                        status=409,
                    )
                apartment.number = new_number
                updated_fields.append("number")

        if "entrance" in data:
            new_entrance = (data.get("entrance") or "").strip()
            if new_entrance != apartment.entrance:
                apartment.entrance = new_entrance
                updated_fields.append("entrance")

        if not updated_fields:
            return JsonResponse({"status": "Нечего обновлять"}, status=400)

        try:
            apartment.save(update_fields=updated_fields)
        except IntegrityError:
            return JsonResponse(
                {"status": "Конфликт уникальности: такой номер уже есть"},
                status=409,
            )

        return JsonResponse({
            "status": "ok",
            "id": str(apartment.id),
            "number": apartment.number,
            "entrance": apartment.entrance,
            "updated_fields": updated_fields,
        }, status=200)

    if request.method == "DELETE":
        residents_count = apartment.user_apartments.count()
        if residents_count:
            return JsonResponse(
                {"status": f"Нельзя удалить: в квартире {residents_count} жильцов/собственников"},
                status=409,
            )

        appeals_count = apartment.appeals.count()
        if appeals_count:
            return JsonResponse(
                {"status": f"Нельзя удалить: по квартире есть обращения ({appeals_count})"},
                status=409,
            )

        apartment.delete()
        return JsonResponse({"status": "ok"}, status=200)

    return JsonResponse({"status": "Method not allowed"}, status=405)