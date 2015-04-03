SAISE est le digne successeur d'[Obiran](/2008/05/obiran-outil-de-backup-incremental-en-ruby/) dont il reprend toutes les fonctionnalités, soit une sauvegarde incrémentale totale (chaque sauvegarde se suffit à elle même) distante via l'utilisation de la commande cp -al et de rsync. Les principes de base sont expliqués sur la page de présentation d'Obiran, lui-même disponible sur [http://code.google.com/p/obiran/](http://code.google.com/p/obiran/). 

SAISE apporte toutefois des différences importantes:

  * SAISE est écrit en [Python](http://www.python.org/) (contrairement à Obiran, en Ruby)
  * SAISE utilise la librairie [libnotify](http://www.galago-project.org/downloads.php) pour faire apparaître des notifications graphiques lors des backups (en option)
  * SAISE a un système de log plus abouti
  * Last but not least - SAISE permet de sécuriser les sauvegardes en cryptant à la volée les fichiers (à la demande de l'utilisateur)


**Le système cryptage de SAISE**

_Pourquoi du cryptage ?_

Il est intéressant de sauvegarder ses données personnelles sur un serveur distant, pour des raisons évidentes de résilience. Toutefois, il peut être dangereux de laisser des données en clair (fichiers de configuration avec mots de passe, correspondance administrative ou financière, photos personnelles...) sur un serveur dont on ne contrôle pas la sécurité.

Aussi il m'a semblé important de réécrire Obiran en y intégrant une composante "sécurité des données". Par conséquent, SAISE utilise la libraire python [ezPyCrypto](http://www.freenet.org.nz/ezPyCrypto/), basée elle-même sur [pyCrypto](http://www.amk.ca/python/code/crypto.html), qui permet de crypter/décrypter des fichiers facilement via des clés de grande taille et la plupart des algorithmes connus.

_Comment cela fonctionne ?_

Via le fichier de configuration, l'utilisateur choisit les fichiers/répertoires à crypter et lors de la sauvegarde ces fichiers seront copiés sur le serveur distant cryptés et avec l'extension .crypted. Les fichiers en clair restent sur le disque dur de l'utilisateur et ne sont donc pas lisibles sur le serveur distant (des clés des 1024 bits ou 2048 bits seront très difficiles à casser...).

L'algorithme de cryptage est donc très simple:
	
  1. Vérification de la présence d'une version non cryptée du fichier sur le répertoire distante => suppression dans ce cas
  2. Vérification de la date de création du fichier crypté distant et comparaison avec la date du fichier en local => Pas de traitement si le local n'est pas plus récent
  3. Cryptage du fichier et copie via scp sur le serveur distant.


A noter: Ce cryptage alourdit légèrement le traitement mais n'augmente pas trop la taille des fichiers.

**Versionnage**
	
  1. SAISE v0.7: Suppression de la dépendance à paramiko
  2. SAISE v0.6.2: Consolidation de la gestion de configuration pour gérer les valeurs "n'importe quoi" + ajout d'un compteur d'erreur.
  3. SAISE v0.6.1: améliorations de la gestion des notifications (cas d'erreur) et de la gestion des fichiers externes (conf, log)
  4. SAISE v0.6: Ajout de notifications graphiques d'événements via libnotify (pynotify)
  5. SAISE v0.5: 1ere version fonctionnelle
  6. SAISE v0.4: cryptage en bonne voie / les fichiers unitaires fonctionnent, reste à finir la partie "gestion des répertoires cryptés"
  7. SAISE v0.3: début du travail sur la synchronisation des fichiers cryptés.
  8. SAISE v0.2: le rsync fonctionne (isofonctionnalités avec obiran)
  9. SAISE Premier commit / connexion en ssh possible


**Dépendances**

Pour faire fonctionner SAISE, il vous faut:
	
  * SAISE
  * rsync
  * ssh
  * libraires python: [pynotify](http://roscidus.com/desktop/node/336) [ezPyCrypto](http://www.freenet.org.nz/ezPyCrypto/)

**License**

SAISE est sous [license apache v2.0](http://www.apache.org/licenses/LICENSE-2.0)

**Où trouver SAISE ?**

Ce projet est actuellement dans l'incubateur sur [Google Code](https://code.google.com/p/tifauve-labs/), et les sources sont gérés via subversion sur [http://code.google.com/p/tifauve-labs/source/browse/trunk/SAISE](http://code.google.com/p/tifauve-labs/source/browse/trunk/SAISE)
