from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_csv, name='upload_csv'),
    path('download/<int:pk>/', views.download_audio, name='download_audio'),
    path('audios/', views.audio_list, name='audio_list'),
]
