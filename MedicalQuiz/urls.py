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
    path("", home, name="home"),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)