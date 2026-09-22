from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from apihandler.models import User


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