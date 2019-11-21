"""website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views

import officehours.views as views
import website.settings as settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('', include('social_django.urls', namespace='social')),
    path('<str:course_offering_slug>/requests/today', views.requests_today, name='requests-today'),
    path('<str:course_offering_slug>/requests/all', views.requests_all, name='requests-all'),
    path('<str:course_offering_slug>/requests/<int:request_id>', views.request_detail, name='request-detail'),
    path('<str:course_offering_slug>/my-request', views.my_request, name='my-request'),
    path('<str:course_offering_slug>/status', views.status, name='status'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), {'next_page': settings.LOGOUT_REDIRECT_URL},
    name='logout')
]
