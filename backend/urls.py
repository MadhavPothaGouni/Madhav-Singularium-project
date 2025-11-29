from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # serve frontend/index.html at root
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    path('admin/', admin.site.urls),
    path('api/tasks/', include('tasks.urls')),
]
