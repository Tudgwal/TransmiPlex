import os
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import datetime
from .utils import get_file_info

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