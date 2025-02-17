from django.shortcuts import render, redirect
from django.conf import settings

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