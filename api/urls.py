"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""URL configuration for api project."""
"""URL configuration for api project."""
from django.contrib import admin
from django.urls import path

from apihandler.views import (
    login_view, me_view, apartments_view, appeals_view, appeal_detail_view,
    uk_domiks_view, uk_domik_detail_or_delete_view, uk_appeals_view,
    uk_update_appeal_status_view,
    polls_view, poll_detail_view, poll_vote_view, poll_results_view,
    uk_polls_view, uk_poll_close_view, uk_poll_delete_view,
    uk_notifications_view, notifications_view, user_notification_detail_view, uk_notification_detail_view,
    uk_apartments_view, uk_apartment_detail_view, user_capital_repair_view, uk_capital_repair_view,
    uk_capital_repair_works_view, uk_capital_repair_work_detail_view, search_domiks_view, uk_appeal_detail_view,
    uk_generate_ap_key_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/login', login_view),
    path('api/v1/me', me_view),
    path('api/v1/domiks', search_domiks_view),
    path('api/v1/user/apartments', apartments_view),
    path('api/v1/user/appeals', appeals_view),
    path('api/v1/user/appeals/<uuid:appeal_id>', appeal_detail_view),
    path('api/v1/user/polls', polls_view),
    path('api/v1/user/polls/<uuid:poll_id>', poll_detail_view),
    path('api/v1/user/polls/<uuid:poll_id>/vote', poll_vote_view),
    path('api/v1/user/polls/<uuid:poll_id>/results', poll_results_view),
    path('api/v1/user/notifications', notifications_view),
    path('api/v1/user/notifications/<uuid:notification_id>', user_notification_detail_view),
    path('api/v1/uk/notifications', uk_notifications_view),
    path('api/v1/uk/notifications/<uuid:notification_id>', uk_notification_detail_view),
    path('api/v1/uk/domiks', uk_domiks_view),
    path('api/v1/uk/domiks/<uuid:domik_id>', uk_domik_detail_or_delete_view),
    path('api/v1/uk/appeals', uk_appeals_view),
    path('api/v1/uk/appeals/<uuid:appeal_id>', uk_appeal_detail_view),
    path('api/v1/uk/appeals/<uuid:appeal_id>/status', uk_update_appeal_status_view),
    path('api/v1/uk/polls', uk_polls_view),
    path('api/v1/uk/polls/<uuid:poll_id>/close', uk_poll_close_view),
    path('api/v1/uk/polls/<uuid:poll_id>', uk_poll_delete_view),
    path('api/v1/uk/domiks/<uuid:domik_id>/apartments', uk_apartments_view),
    path('api/v1/uk/domiks/<uuid:domik_id>/apartments/<uuid:apartment_id>', uk_apartment_detail_view),
    path('api/v1/uk/domiks/<uuid:domik_id>/apartments/<uuid:apartment_id>/generate-key', uk_generate_ap_key_view),
    path('api/v1/user/domik/<uuid:domik_id>/capital-repair', user_capital_repair_view),
    path('api/v1/uk/domiks/<uuid:domik_id>/capital-repair', uk_capital_repair_view),
    path('api/v1/uk/domiks/<uuid:domik_id>/capital-repair/works', uk_capital_repair_works_view),
    path('api/v1/uk/domiks/<uuid:domik_id>/capital-repair/works/<uuid:work_id>', uk_capital_repair_work_detail_view),
]