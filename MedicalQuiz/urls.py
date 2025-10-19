"""
URL configuration for MedicalQuiz project.

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
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from Quizzes.views import home



@login_required
def root_redirect(request):
    return redirect("Quizzes:home")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("Quizzes/", include("Quizzes.urls")),
    path("accounts/", include("accounts.urls")),
    path("", home, name="home"),  # 👈 public landing page
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)