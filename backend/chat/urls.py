from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('chat/', views.chat, name='chat'),
    path('history/', views.history, name='history'),
    path('sessions/', views.get_sessions, name='sessions'),
    path('sessions/new/', views.new_session, name='new_session'),
]