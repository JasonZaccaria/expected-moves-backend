from django.urls import path
from . import views

urlpatterns = [
    path('post/', views.main.as_view()),
    path('get/', views.main.as_view()),
]