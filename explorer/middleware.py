from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps
from django.conf import settings

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Liste des chemins qui ne nécessitent pas d'authentification
        public_paths = [reverse('explorer:login')]
        
        # Si l'utilisateur n'est pas authentifié et n'est pas sur une page publique
        if not request.session.get('is_authenticated') and request.path not in public_paths:
            return redirect('explorer:login')
            
        response = self.get_response(request)
        return response