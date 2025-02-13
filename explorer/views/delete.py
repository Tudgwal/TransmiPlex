import os
import json
from urllib.parse import unquote
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from transmission_rpc import Client

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

        for plex_type in ['films', 'series', 'documentaires', 'livres', 'anime']:
            plex_type_dir = os.path.join(plex_base_dir, f"plex-{plex_type}")
            if os.path.exists(plex_type_dir):
                for item in os.listdir(plex_type_dir):
                    item_path = os.path.join(plex_type_dir, item)
                    if os.path.islink(item_path) and os.path.realpath(item_path) == os.path.realpath(full_path):
                        os.unlink(item_path)

        # Si on supprime un fichier/dossier (pas juste un symlink)
        if delete_type in ['file', 'both']:
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