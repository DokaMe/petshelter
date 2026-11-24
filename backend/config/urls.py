from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/animals/', include('animals.urls')),
    path('api/chat/', include('chatbot.urls')),
    path('api/auth/', include('people.urls')),
]