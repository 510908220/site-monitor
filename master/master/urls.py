"""heartbeats URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from app.urls import router
from django.contrib.auth.views import logout
from ui.views import login_user
urlpatterns = [

    path('admin/', admin.site.urls),
    path('login/', login_user, name='login'),
    path('logout/', logout, name='logout'),
    path('api/token/', obtain_auth_token, name='api-token'),
    path('api/', include(router.urls)),
    path('', include("ui.urls")),
]

# urlpatterns = [path('silk/', include('silk.urls', namespace='silk'))] + urlpatterns
