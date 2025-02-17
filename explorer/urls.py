from django.urls import path
from .views import logging, list, delete, link, download

app_name = 'explorer'

urlpatterns = [
    path('', list.file_list, name='file_list'),
    path('check-symlink/', list.check_symlink, name='check_symlink'),
    path('list-files/', list.list_directory_files, name='list_files'),
    path('login/', logging.login, name='login'),
    path('logout/', logging.logout, name='logout'),
    path('download/<path:item_path>/', download.download_item, name='download_item'),
    path('delete/', delete.delete_item, name='delete_item'),
    path('create-plex-link/', link.create_plex_link, name='create_plex_link'),
]