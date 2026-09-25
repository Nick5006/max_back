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
from django.contrib import admin
from django.urls import path

from apihandler.views import login_view, me_view, apartments_view, appeals_view, appeal_detail_view, uk_domiks_view, \
    uk_domik_detail_view, uk_appeals_view, uk_update_appeal_status_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/login', login_view),
    path('api/v1/me', me_view),
    path('api/v1/user/apartments', apartments_view),
    path('api/v1/user/appeals', appeals_view),
    path('api/v1/user/appeals/<uuid:appeal_id>', appeal_detail_view),
    path('api/v1/uk/domiks', uk_domiks_view),
    path('api/v1/uk/domiks/<uuid:domik_id>', uk_domik_detail_view),
    path('api/v1/uk/appeals', uk_appeals_view),
    path('api/v1/uk/appeals/<uuid:appeal_id>/status', uk_update_appeal_status_view),
]
