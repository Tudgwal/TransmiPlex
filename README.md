# Content Warning
J'ai codé ça en une soirée et vraiment n'importe comment. Si ce message est encore là, c'est que je n'ai pas encore pris le temps de revenir dessus. Bisous.

# File Explorer avec intégration Plex et Transmission

Un explorateur de fichiers web avec gestion des liens symboliques pour Plex et intégration de Transmission. Permet de gérer facilement vos fichiers téléchargés et leur organisation dans votre bibliothèque Plex.

## 🚀 Fonctionnalités

- 📁 Navigation dans les dossiers
- 🔍 Recherche de fichiers
- ↕️ Tri par nom, date et taille
- 🎬 Intégration Plex avec création de liens symboliques
- 🌐 Gestion des torrents Transmission
- 🔒 Interface sécurisée par mot de passe
- 📱 Interface responsive

### Actions disponibles

- **Ouvrir/Télécharger** : Naviguer dans les dossiers ou télécharger des fichiers
- **Plex** : Créer des liens symboliques vers votre bibliothèque Plex avec un nommage standardisé
- **Supprimer** : Options multiples de suppression (fichier, lien symbolique ou les deux)

## 📋 Prérequis

- Python 3.8+
- Django 5.0+
- Transmission-daemon
- Accès à un serveur Plex (optionnel)

## 🛠️ Installation

1. Clonez le dépôt :
    ```bash
    bash git clone [url-du-repo] cd file-explorer
    ```

2. Créez un environnement virtuel :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

4. Créez un fichier `.env` à la racine du projet :
    ```bash
    cp .env.dist .env
    ```

5. Effectuez les migrations :
    ```bash
    python manage.py migrate
    ```

6. Lancez le serveur :
    ```bash
    python manage.py runserver
    ```

## ⚙️ Configuration

### Structure des dossiers Plex

Les liens symboliques sont créés dans des sous-dossiers spécifiques :
- `plex-film/`
- `plex-serie/`
- `plex-documentaire/`
- `plex-livre/`
- `plex-bd/`

### Format de nommage

Les fichiers dans Plex suivent le format :
- Films : `Titre (Année)`
- Exemple : `Avatar (2009)`

## 🔒 Sécurité

- Authentification requise pour accéder à l'interface
- Validation des chemins de fichiers
- Protection CSRF
- Gestion des permissions de fichiers

## 🔄 Intégration Transmission

- Suppression automatique des torrents lors de la suppression de fichiers
- Gestion récursive des dossiers et sous-dossiers
- Synchronisation avec l'état des téléchargements

## 🛠️ Développement
### Technologies utilisées

- Backend : Django
- Frontend : HTML, CSS, JavaScript
- API : Transmission RPC

## ⚠️ Notes importantes

- Assurez-vous d'avoir les permissions nécessaires pour créer des liens symboliques
- Configurez correctement les chemins dans le fichier `.env`
- Utilisez HTTPS en production
- Faites des sauvegardes régulières de vos données

## 🐛 Résolution des problèmes courants

1. **Erreur de permission** : Vérifiez les droits d'accès aux dossiers
2. **Liens symboliques non créés** : Vérifiez les chemins dans `.env`
3. **Transmission non connecté** : Vérifiez les paramètres de connexion

## 📮 Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue.