import os
import re
import shutil
import mimetypes
import json
from datetime import datetime
from django.http import FileResponse, JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse
from django.conf import settings
from dotenv import load_dotenv
from pathlib import Path
from .utils import get_items_async
from transmission_rpc import Client
from urllib.parse import unquote

load_dotenv()

def login(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if password == settings.EXPLORER_PASSWORD:
            request.session['is_authenticated'] = True
            return redirect('explorer:file_list')
        else:
            return render(request, 'explorer/login.html', {'error': 'Mot de passe incorrect'})
    return render(request, 'explorer/login.html')

def logout(request):
    request.session.flush()
    return redirect('explorer:login')

def check_symlink_exists(path):
    """Vérifie si un lien symbolique existe pour ce fichier"""
    plex_base_dir = os.getenv('PLEX_BASE_DIRECTORY')
    full_path = os.path.realpath(path)
    
    if plex_base_dir:
        for plex_type in ['films', 'series', 'documentaires', 'livres', 'anime']:
            plex_type_dir = os.path.join(plex_base_dir, f"plex-{plex_type}")
            if os.path.exists(plex_type_dir):
                for item in os.listdir(plex_type_dir):
                    item_path = os.path.join(plex_type_dir, item)
                    if os.path.islink(item_path) and os.path.realpath(item_path) == full_path:
                        return True
    return False

def list_directory_files(request):
    path = request.GET.get('path')
    base_dir = os.getenv('BASE_DIRECTORY')
    full_path = os.path.join(base_dir, path)
    
    if not os.path.realpath(full_path).startswith(os.path.realpath(base_dir)):
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    try:
        files = []
        for item in os.listdir(full_path):
            if not item.startswith('.'):
                item_path = os.path.join(path, item)
                files.append({
                    'name': item,
                    'path': item_path
                })
        return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
def create_plex_link(request):
    try:
        data = json.loads(request.body)
        base_dir = os.getenv('BASE_DIRECTORY')
        plex_base_dir = os.getenv('PLEX_BASE_DIRECTORY')

        # Validation du format du titre
        title = data['title']
        if not re.match(r'^.+\(\d{4}\)$', title):
            return JsonResponse({
                'error': 'Format de titre incorrect. Utilisez: "Titre (Année)"'
            }, status=400)
        
        # Créer le dossier plex-{type} s'il n'existe pas
        plex_type_dir = os.path.join(plex_base_dir, f"plex-{data['type']}")
        os.makedirs(plex_type_dir, exist_ok=True)
        
        title = data['title']
        source_path = os.path.join(base_dir, data['itemPath'])
        
        if data['isDirectory'] == 'true' and 'selected_files' in data:
            # Traitement pour plusieurs fichiers
            for file_path in data['selected_files']:
                full_source = os.path.join(base_dir, file_path)
                filename = os.path.basename(file_path)
                # Essayer de garder le numéro d'épisode
                episode_match = re.search(r'[Ss]\d+[Ee]\d+|[Ee]\d+|[\d]+', filename)
                if episode_match:
                    episode_num = episode_match.group(0)
                    target_name = f"{title} - {episode_num}{os.path.splitext(filename)[1]}"
                else:
                    target_name = f"{title}{os.path.splitext(filename)[1]}"
                target_path = os.path.join(plex_type_dir, target_name)
                os.symlink(full_source, target_path)
        else:
            # Traitement pour un seul fichier
            extension = os.path.splitext(source_path)[1]
            target_path = os.path.join(plex_type_dir, f"{title}{extension}")
            os.symlink(source_path, target_path)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_directory_size(directory):
    """Calcule la taille totale d'un dossier et de son contenu de façon récursive"""
    total_size = 0
    try:
        # Parcourir le dossier de façon récursive
        for dirpath, dirnames, filenames in os.walk(directory):
            # Ajouter la taille de tous les fichiers dans le dossier actuel
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    # Gérer les erreurs potentielles (fichiers inaccessibles, etc.)
                    continue
    except (OSError, PermissionError):
        # Gérer les erreurs d'accès au dossier
        return 0
    return total_size

def get_file_info(path):
    """Obtient les informations d'un fichier ou dossier"""
    stats = os.stat(path)
    is_dir = os.path.isdir(path)
    
    # Si c'est un dossier, calculer sa taille réelle
    size = get_directory_size(path) if is_dir else stats.st_size
    
    return {
        'name': os.path.basename(path),
        'path': path,
        'size': size,
        'modified': datetime.fromtimestamp(stats.st_mtime),
        'is_dir': is_dir
    }

@ensure_csrf_cookie
def file_list(request):
    base_dir = os.getenv('BASE_DIRECTORY')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'name')
    sort_direction = request.GET.get('direction', 'asc')
    current_path = request.GET.get('path', '')

    # Construire le chemin complet
    if current_path:
        current_dir = os.path.join(base_dir, current_path)
    else:
        current_dir = base_dir

    # Vérifier que le chemin est sécurisé
    if not os.path.realpath(current_dir).startswith(os.path.realpath(base_dir)):
        current_dir = base_dir
        current_path = ''

    items = []
    
    try:
        for item in os.listdir(current_dir):
            if not item.startswith('.'):
                if search_query.lower() in item.lower():
                    full_path = os.path.join(current_dir, item)
                    relative_path = os.path.join(current_path, item) if current_path else item
                    item_info = get_file_info(full_path)
                    item_info['path'] = relative_path
                    # Ajouter l'information sur l'existence d'un symlink
                    item_info['has_symlink'] = check_symlink_exists(full_path)
                    items.append(item_info)

    except (FileNotFoundError, PermissionError) as e:
        # En cas d'erreur, retourner à la racine
        return HttpResponseRedirect(reverse('explorer:file_list'))

    # Trier les éléments
    if sort_by == 'name':
        items.sort(key=lambda x: (not x.get('is_parent', False), x['name'].lower()), 
                  reverse=(sort_direction == 'desc'))
    elif sort_by == 'date':
        items.sort(key=lambda x: (not x.get('is_parent', False), x['modified'] or datetime.min), 
                  reverse=(sort_direction == 'desc'))
    elif sort_by == 'size':
        items.sort(key=lambda x: (not x.get('is_parent', False), x['size']), 
                  reverse=(sort_direction == 'desc'))

    return render(request, 'explorer/file_list.html', {
        'items': items,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_direction': sort_direction,
        'current_path': current_path,
    })

def download_item(request, item_path):
    """Vue pour télécharger un fichier uniquement"""
    base_dir = os.getenv('BASE_DIRECTORY')
    full_path = os.path.join(base_dir, item_path)
    
    # Vérifier que le chemin est sécurisé (dans le dossier autorisé)
    if not os.path.realpath(full_path).startswith(os.path.realpath(base_dir)):
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)

    try:
        if os.path.isfile(full_path):
            # Pour un fichier, le télécharger directement
            mime_type, _ = mimetypes.guess_type(full_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
                
            response = FileResponse(
                open(full_path, 'rb'),
                content_type=mime_type
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_path)}"'
            return response
        else:
            return JsonResponse({'error': 'Ce n\'est pas un fichier'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def check_symlink(request):
    path = request.GET.get('path')
    if not path:
        return JsonResponse({'error': 'Chemin non spécifié'}, status=400)

    base_dir = os.getenv('BASE_DIRECTORY')
    plex_base_dir = os.getenv('PLEX_BASE_DIRECTORY')
    full_path = os.path.join(base_dir, path)

    has_symlink = False
    if plex_base_dir:
        # Vérifier dans tous les dossiers plex
        for plex_type in ['films', 'series', 'documentaires', 'livres', 'anime']:
            plex_type_dir = os.path.join(plex_base_dir, f"plex-{plex_type}")
            if os.path.exists(plex_type_dir):
                for item in os.listdir(plex_type_dir):
                    item_path = os.path.join(plex_type_dir, item)
                    if os.path.islink(item_path) and os.path.realpath(item_path) == os.path.realpath(full_path):
                        has_symlink = True
                        break
            if has_symlink:
                break

    return JsonResponse({'has_symlink': has_symlink})

def get_transmission_client():
    """Crée et retourne un client Transmission"""
    return Client(
        host=os.getenv('TRANSMISSION_HOST', 'localhost'),
        port=int(os.getenv('TRANSMISSION_PORT', 9091)),
        username=os.getenv('TRANSMISSION_USER'),
        password=os.getenv('TRANSMISSION_PASSWORD')
    )

def find_torrent_by_path(client, path):
    """Trouve le torrent correspondant au chemin donné"""
    torrents = client.get_torrents()
    real_path = os.path.realpath(path)
    
    for torrent in torrents:
        # Vérifier le dossier de téléchargement du torrent
        if os.path.realpath(torrent.download_dir) == os.path.dirname(real_path):
            # Vérifier si le nom correspond
            if os.path.basename(real_path) in [torrent.name, unquote(torrent.name)]:
                return torrent
    return None

def get_root_parent(path, base_dir):
    """
    Retourne le dossier parent qui est à la racine pour un chemin donné
    """
    current_path = path
    while os.path.dirname(current_path) != base_dir:
        current_path = os.path.dirname(current_path)
        if current_path == base_dir or current_path == '/':
            return None
    return current_path

@require_POST
def delete_item(request):
    try:
        data = json.loads(request.body)
        path = data.get('path')
        delete_type = data.get('delete_type')

        base_dir = os.getenv('BASE_DIRECTORY')
        plex_base_dir = os.getenv('PLEX_BASE_DIRECTORY')
        full_path = os.path.join(base_dir, path)

        if not os.path.realpath(full_path).startswith(os.path.realpath(base_dir)):
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)

        # Trouver le dossier parent à la racine
        root_parent = get_root_parent(full_path, base_dir)
        is_root_item = os.path.dirname(full_path) == base_dir

        for plex_type in ['films', 'series', 'documentaires', 'livres', 'anime']:
            plex_type_dir = os.path.join(plex_base_dir, f"plex-{plex_type}")
            if os.path.exists(plex_type_dir):
                for item in os.listdir(plex_type_dir):
                    item_path = os.path.join(plex_type_dir, item)
                    if os.path.islink(item_path) and os.path.realpath(item_path) == os.path.realpath(full_path):
                        os.unlink(item_path)

        # Si on supprime un fichier/dossier (pas juste un symlink)
        if delete_type in ['file', 'both']:
            if root_parent:
                # On supprime le dossier parent à la racine
                try:
                    client = get_transmission_client()
                    torrent = find_torrent_by_path(client, root_parent)
                    if torrent:
                        client.remove_torrent(torrent.id, delete_data=True)
                except Exception as e:
                    print(f"Erreur lors de la suppression du torrent: {e}")

                return JsonResponse({'success': True, 'deleted_parent': True})

            # Si c'est un élément à la racine
            elif is_root_item:
                try:
                    client = get_transmission_client()
                    torrent = find_torrent_by_path(client, full_path)
                    if torrent:
                        client.remove_torrent(torrent.id, delete_data=True)
                except Exception as e:
                    print(f"Erreur lors de la suppression du torrent: {e}")

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)