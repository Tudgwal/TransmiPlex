from django.urls import path
from . import views

app_name = 'explorer'

urlpatterns = [
    path('', views.file_list, name='file_list'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('download/<path:item_path>/', views.download_item, name='download_item'),
    path('delete/', views.delete_item, name='delete_item'),
    path('list-files/', views.list_directory_files, name='list_files'),
    path('create-plex-link/', views.create_plex_link, name='create_plex_link'),
    path('check-symlink/', views.check_symlink, name='check_symlink'),
]