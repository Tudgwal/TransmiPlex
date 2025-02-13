import json
import os
import re
from django.http import JsonResponse
from django.views.decorators.http import require_POST

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