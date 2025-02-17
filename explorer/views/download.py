import os
import mimetypes
from django.http import FileResponse, JsonResponse

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
