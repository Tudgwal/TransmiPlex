import os
from functools import lru_cache
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

@lru_cache(maxsize=1000)
def get_directory_size(directory):
    """
    Calcule et met en cache la taille d'un dossier
    """
    # Essayer de récupérer la taille depuis le cache
    cache_key = f"dir_size_{directory}"
    cached_size = cache.get(cache_key)
    if cached_size is not None:
        return cached_size

    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    continue
    except (OSError, PermissionError):
        return 0

    # Mettre en cache pour 1 heure
    cache.set(cache_key, total_size, 3600)
    return total_size

def get_file_info(path):
    """
    Obtient les informations d'un fichier ou dossier
    """
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

def get_items_async(base_dir, search_query=''):
    """
    Récupère les informations des fichiers de manière asynchrone
    """
    items = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        try:
            for item in os.listdir(base_dir):
                if search_query.lower() in item.lower():
                    full_path = os.path.join(base_dir, item)
                    futures.append(executor.submit(get_file_info, full_path))
            
            for future in futures:
                try:
                    items.append(future.result())
                except Exception as e:
                    print(f"Erreur lors du traitement d'un fichier: {e}")
                    continue
        except (FileNotFoundError, PermissionError) as e:
            print(f"Erreur d'accès au dossier: {e}")
    
    return items