from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from apihandler.serializers.appeal import AppealCreateSerializer
from apihandler.models import User, Apartment, Appeal, AppealHistory, UserApartment, Domik


def parse_json(request):
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse({'status': 'Некорректный JSON'}, status=400)


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
            {'status': 'Такой пользователь уже существует', 'id': str(user.id)},
            status=200,
        )

    try:
        user = User.objects.create_user(max_id=max_id, name=name)
    except ValueError as e:
        return JsonResponse({'status': str(e)}, status=400)

    login(request, user)
    return JsonResponse({'status': 'ok', 'id': str(user.id)}, status=200)

@csrf_exempt
@require_POST
@login_required
def create_apartment_view(request):
    data, error = parse_json(request)
    if error:
        return error

    domik_id = data.get("domik_id")
    number = data.get("number")

    if not domik_id or not number:
        return JsonResponse({"status": "Поля domik_id и number обязательны"}, status=400)

    apartment = Apartment.objects.filter(domik_id=domik_id, number=number).first()

    if apartment is None:
        return JsonResponse({"status": "Квартира не найдена"}, status=404)

    user_apartment, created = UserApartment.objects.get_or_create(user=request.user, apartment=apartment, defaults={"role": UserApartment.Role.RESIDENT})

    if not created:
        return JsonResponse({"status": "Квартира уже добавлена"}, status=409)

    return JsonResponse({
        "id": str(apartment.id),
        "number": apartment.number,
        "domik_id": str(apartment.domik_id),
        "role": user_apartment.role
    }, status=201)

@csrf_exempt
@require_POST
@login_required
def create_appeals_view(request):
    data, error = parse_json(request)
    if error:
        return error

    serializer = AppealCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    apartment = Apartment.objects.filter(id=data["apartment_id"], user_apartments__user=request.user).first()

    if apartment is None:
        return JsonResponse({"status": "Квартира не найдена"}, status=404)

    appeal = Appeal.objects.create(
        author=request.user,
        apartment=apartment,
        domik=apartment.domik,
        title=data["title"],
        description=data["description"],
        status=Appeal.Status.NEW
    )

    AppealHistory.objects.create(
        appeal=appeal,
        status=Appeal.Status.NEW,
        changed_by=request.user,
    )

    return JsonResponse({
        "id": appeal.id,
        "title": appeal.title,
        "description": appeal.description,
        "management_org": apartment.domik.management_org,
        "status": appeal.status,
        "created_at": appeal.created_at
    }, status=201)



