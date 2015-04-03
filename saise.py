#!/usr/bin/env python
# -*- coding: utf8 -*-

# SAISE - SAuvegarde Incrémentale SEcurisé
# Permet de sauvegarder en utilisant rsync + "hard link" pour l'incrémental + ssh
# Développé par J.RAIGNEAU - julien@raigneau.net - http://www.tifauve.net
#Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at
#http://www.apache.org/licenses/LICENSE-2.0
#Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


import logging
import re
import os,sys
import ezPyCrypto
from time import strftime
import time
import datetime
import pynotify

from configuration import Configuration

VERSION = "0.7"

NB_ERREURS = 0




#fonctions utilesytho
#####################################
def cryptDir(dir,cryptKey):
    global myConfiguration
    #vérifier sir dir ou file
    if os.path.isdir(dir):
        #creation du répertoire distant
        for dir2backup in myConfiguration.getDirs2backup():
            if dir.startswith(dir2backup):
                relativePath = dir.replace(dir2backup+"/","")
                item = os.path.join(myConfiguration.getBackupmasterdir(),"current",dir2backup.split("/")[-1],relativePath)
                logging.info("Création du répertoire %s." % item)
                execSSH("mkdir %s" % item) #creation répertoire
               
        for root, dirs, files in os.walk(dir):
            for name in dirs:
                name = os.path.join(root, name)
                for dir2backup in myConfiguration.getDirs2backup():
                    if name.startswith(dir2backup):
                        relativePath = name.replace(dir2backup+"/","")
                        item = os.path.join(myConfiguration.getBackupmasterdir(),"current",dir2backup.split("/")[-1],relativePath)
                        execSSH("mkdir %s" % item) #creation répertoire
                        logging.info("Création du répertoire %s." % item)
            for name in files:
                cryptFile(os.path.join(root, name),cryptKey)

    else:
        cryptFile(dir,cryptKey)

def cryptFile(file,cryptKey):
    global myConfiguration
    global NB_ERREURS
   
    #TODO: à revoir
   #construction du chemin distant
    filename = file.split("/")[-1]
    for dir in myConfiguration.getDirs2backup():
        if file.startswith(dir):
            relativePath = file.replace(dir+"/","")
            relativePath = relativePath.replace(relativePath.split("/")[-1],"")
            distantItem = os.path.join(myConfiguration.getBackupmasterdir(),"previous",dir.split("/")[-1],relativePath)
   
    distantItem = distantItem + filename      
    print "distant item: %s" % distantItem
   
    #Etape1: vérifier si une version non cryptée existe => à supprimer dans ce cas
    stdout= execSSH('ls %s' % distantItem)
    print stdout
    if len(stdout)>1:
        print "remove %s" % distantItem
        #stdout= execSSH('rm %s' % distantItem)
    #Etape2: vérifier si la date de la version distante est plus vieille que la date de la version courant
    distantItem = distantItem + ".crypted"
    stdout= execSSH('ls --full-time %s' % distantItem)
    dateFile = stdout[0].split(" ")[6] + " " + stdout[0].split(" ")[7]
    dateFile = dateFile.split(".")[0]
    print "stdout for %s is %s" % (distantItem,dateFile)
    distantDateFile = datetime.datetime(*time.strptime(dateFile, "%Y-%m-%d %H:%M:%S")[0:6])
   
    #>>> yesterday = datetime.datetime(*time.strptime("2008-08-09 9:47:48", "%Y-%m-%d %H:%M:%S")[0:6])
    #>>> yesterday - today

    #Etape2.1: crypter
    #Etape2.2: copier
   
   
    logging.info('Cryptage de %s' % file)
    try:
        fd = open(file,"rb")
        enc = fd.read()
        fd.close()
    except IOError:
        logging.error("Impossible d'ouvrir %s. Ce fichier ne sera pas sauvegardé!" % file)
        NB_ERREURS = NB_ERREURS +1
    else:
       codedString = cryptKey.encString(enc)
       cryptedFile = file + ".crypted"
       try:
           fd = open(cryptedFile,"w")
           fd.write(codedString)
           fd.close()  
       except IOError:
           logging.error("Impossible de créer %s. Ce fichier ne sera pas sauvegardé!" % cryptedFile)
           NB_ERREURS = NB_ERREURS +1
       else:
           #construction du chemin distant
           for dir in myConfiguration.getDirs2backup():
               if file.startswith(dir):
                   relativePath = file.replace(dir+"/","")
                   relativePath = relativePath.replace(relativePath.split("/")[-1],"")
                   item = os.path.join(myConfiguration.getBackupmasterdir(),"current",dir.split("/")[-1],relativePath)
                   error = os.system("scp -P %s -i %s %s %s@%s:%s" % (myConfiguration.getSsh_port(),myConfiguration.getSsh_Key(),cryptedFile,myConfiguration.getSsh_user(),myConfiguration.getSsh_destination(),item))
                   #print "scp -P %s -i %s %s %s@%s:%s" % (myConfiguration.getSsh_port(),myConfiguration.getSsh_Key(),cryptedFile,myConfiguration.getSsh_user(),myConfiguration.getSsh_destination(),item)
                   if error <> 0:
                       logging.error("La copie de %s ne s'est pas déroulé correctement" % cryptedFile)
                       NB_ERREURS = NB_ERREURS +1
           #sftp.put(cryptedFile,'')
           os.remove(cryptedFile)
#messages de notification à l'écran
def notify(message,priority,notification):
    if notification == True:
        titleNotify = "Saise - Sauvegarde Incrémentale Sécurisée"
        uriNotify = "file://" + os.path.join(sys.path[0], 'saise.png')
        n = pynotify.Notification(titleNotify, message,uriNotify)
        n.set_urgency(priority)
        n.show()
 
#Execute une commande distante et renvoi le résultat
def execSSH(cmd):
    global myConfiguration
    cmdSSH = "ssh -p %s -i %s %s@%s '%s'" % (myConfiguration.getSsh_port(),myConfiguration.getSsh_Key(),myConfiguration.getSsh_user(),myConfiguration.getSsh_destination(),cmd)
    out = os.popen(cmdSSH).read()
    out = out.split("\n")
    return out
   
#####################################
#début script

#Activation logs
logFile = os.path.join(sys.path[0],"saise.log")
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=logFile,
                    filemode='w')

#Lecture fichier de conf
logging.info('Ouverture fichier de configuration')
myConfiguration = Configuration(os.path.join(sys.path[0],'saise.yaml'))

#preparation libnotify
if myConfiguration.getNotification() == True:
    notification = True
    pynotify.init("Saise - Sauvegarde Incrémentale Sécurisée")
else:
    notification = False



backupdir = strftime("%Y%m%d_%H%M%S") #nom du nouveau repertoire
dateDebutBackup = strftime("%d/%m/%Y %H:%M:%S")
logging.info("Début du backup: %s" % dateDebutBackup)
notify("Début du backup: %s" % dateDebutBackup,pynotify.URGENCY_NORMAL,notification)

#vérifications iniales
#backupmasterDir est non nul
if myConfiguration.getBackupmasterdir() is None:
    logging.error("Le fichier de configuration n'est pas complet: pas de répertoire destination")
    notify("Le fichier de configuration n'est pas complet: pas de répertoire destination. Le programme ne peut continuer, merci de voir le fichier de log %s" % logFile,pynotify.URGENCY_CRITICAL,notification)
    NB_ERREURS = NB_ERREURS +1
    exit(-1)
if myConfiguration.getDirs2backup() == []:
    logging.error("Le fichier de configuration n'est pas complet: pas de répertoire à sauvegarder")
    notify("Le fichier de configuration n'est pas complet: pas de répertoire à sauvegarder. Le programme ne peut continuer, merci de voir le fichier de log %s" % logFile,pynotify.URGENCY_CRITICAL,notification)
    NB_ERREURS = NB_ERREURS +1
    exit(-1)
#il y a au moins un répertoire à sauvegarder

currentDir =  os.path.join(myConfiguration.getBackupmasterdir(),"current")

#ouverture client ssh
logging.info("Paramètres: %s %s %s %s" % (myConfiguration.getSsh_port(),myConfiguration.getSsh_destination(),myConfiguration.getSsh_user(),myConfiguration.getSsh_Key()))
stdout= execSSH('ls -r1 %s' % myConfiguration.getBackupmasterdir())

#print stdout

#traitement retour premiere commande (ls -rl)
dirs = []
for line in stdout:
    regexp = line.strip('\n')
    if re.match(r"\d{8}_\d{6}",regexp) is not None:
        dirs.append(regexp)

logging.info('Répertoires de sauvegarde actuellement sur le serveur: %s'% dirs)

#Suppression repertoire le plus vieux
if len(dirs) == myConfiguration.getIterations():
    oldbackupdir = dirs[-1]
    logging.info('Dernier repertoire à effacer %s' % oldbackupdir)
    execSSH('rm -rf %s/%s' % (myConfiguration.getBackupmasterdir(),oldbackupdir))

#création du repertoire via cp -al
if len(dirs) == 0:
    logging.info('Premier backup...cela peut durer !')
    execSSH( 'mkdir %s/%s;ln -s %s/%s/ %s/current' % (myConfiguration.getBackupmasterdir(),backupdir,myConfiguration.getBackupmasterdir(),backupdir,myConfiguration.getBackupmasterdir()))
else:
    lastbackupdir = dirs[0]
    logging.info('Le répertoire %s servira de référence - taggué previous ' % lastbackupdir)
    execSSH( 'cp -al %s/%s %s/%s;rm %s/current;ln -s %s/%s %s/current;' % (myConfiguration.getBackupmasterdir(),lastbackupdir,myConfiguration.getBackupmasterdir(),backupdir,myConfiguration.getBackupmasterdir(),myConfiguration.getBackupmasterdir(),backupdir,myConfiguration.getBackupmasterdir()))
    execSSH( 'ln -s %s/%s %s/previous;' % (myConfiguration.getBackupmasterdir(),lastbackupdir,myConfiguration.getBackupmasterdir()))


#liste des fichiers/répertoire à exclure
excludedDirs = ""
for item in myConfiguration.getExcludedDirs():
    if excludedDirs == "":
        excludedDirs = "--exclude="+item
    else:
        excludedDirs = excludedDirs + " --exclude=" + item

#on rajoute les fichiers/répertoire cryptés
#ssi les patterns correspondent à ceux des dirs2backup
for item in myConfiguration.getCryptedDirs2Backup():
    for dir in myConfiguration.getDirs2backup():
        if item.startswith(dir):
            item = item.replace(dir+"/","") #on considére des pattern dans rsync => il faut donc récupérer juste ce qui sera commun entre master et backup
            if excludedDirs == "":
                excludedDirs = "--exclude="+item
            else:
                excludedDirs = excludedDirs + " --exclude=" + item

logging.info('Les patterns suivant seront exclus: %s'% excludedDirs)

#backup via rsync
for dir in myConfiguration.getDirs2backup():
    logging.info('Synchronisation de %s...' % dir)
    notify('Synchronisation de %s...' % dir,pynotify.URGENCY_NORMAL,notification)
    error = os.system('nice -n 19 rsync -az --delete %s --delete-excluded -e "ssh -p %s -i %s" %s %s@%s:%s/%s' % (excludedDirs,myConfiguration.getSsh_port(),myConfiguration.getSsh_Key(),dir,myConfiguration.getSsh_user(),myConfiguration.getSsh_destination(),myConfiguration.getBackupmasterdir(),backupdir))
    #print 'nice -n 19 rsync -az --delete %s --delete-excluded -e "ssh -p %s -i %s" %s %s@%s:%s/%s' % (excludedDirs,myConfiguration.getSsh_port(),myConfiguration.getSsh_Key(),dir,myConfiguration.getSsh_user(),myConfiguration.getSsh_destination(),myConfiguration.getBackupmasterdir(),backupdir)
    if error <> 0:
        logging.error("La synchronisation de %s ne s'est pas déroulé correctement" % dir)
        notify("La synchronisation de %s ne s'est pas déroulé correctement" % dir,pynotify.URGENCY_CRITICAL,notification)
        NB_ERREURS = NB_ERREURS +1
        if error == 5888: #error de répertoire n'existant pas
            logging.error("Le répertoire %s n'existe pas!" % dir)
            notify("Le répertoire %s n'existe pas!" % dir,pynotify.URGENCY_CRITICAL,notification)
    else:
       logging.info("Synchronisation de %s s'est terminée avec succès" % dir)
    #print 'nice -n 19 rsync -az --delete %s --delete-excluded -e "ssh -p %s -i %s" %s %s@%s:%s/%s' % (excludedDirs,myConfiguration.getSsh_port(),myConfiguration.getSsh_Key(),dir,myConfiguration.getSsh_user(),myConfiguration.getSsh_destination(),myConfiguration.getBackupmasterdir(),backupdir)

#cryptage et backup des fichiers à crypter
logging.info('Les fichiers non cryptés sont synchronisés, passage aux fichiers à crypter')
notify('Les fichiers non cryptés sont synchronisés, passage aux fichiers à crypter',pynotify.URGENCY_NORMAL,notification)
#chargement clé
try:
    fd = open(myConfiguration.getCryptKey(),"rb")
    pubPrivKey = fd.read()
    fd.close()
except IOError:
    logging.error("La clé de cryptage %s n'a pu être ouverte" % myConfiguration.getCryptKey())
    notify("La clé de cryptage %s n'a pu être ouverte" % myConfiguration.getCryptKey(),pynotify.URGENCY_CRITICAL,notification)
    NB_ERREURS = NB_ERREURS +1
    sys.exit(-1)
else:
    cryptKey = ezPyCrypto.key()
    cryptKey.importKey(pubPrivKey)
#cryptage
for dir in myConfiguration.getCryptedDirs2Backup():
    cryptDir(dir,cryptKey)
notify('Les fichiers cryptés sont synchronisés',pynotify.URGENCY_NORMAL,notification)

#Fin du backup
dateFinBackup = strftime("%d/%m/%Y %H:%M:%S")
if NB_ERREURS < 1:
    msg = ""
else:
    if NB_ERREURS == 1:
        msg = "Une erreur a été trouvée. Merci de consulter le fichier de log pour obtenir plus d'information."
    else:
        msg = "%s erreur(s) ont été trouvées. Merci de consulter le fichier de log pour obtenir plus d'information." % NB_ERREURS
       
logging.info("Fin du backup: %s.\n%s" % (dateFinBackup,msg))
error = os.system("scp -P %s -i %s %s %s@%s:%s" % (myConfiguration.getSsh_port(),myConfiguration.getSsh_Key(),logFile,myConfiguration.getSsh_user(),myConfiguration.getSsh_destination(),currentDir))
if error <> 0:
        logging.error("Impossible de copier le fichier de log %s sur la cible" % logFile)
        notify("Backup terminé mais avec des erreurs, merci de consulter le fichier de log %s"%logFile,pynotify.URGENCY_NORMAL,notification)
else:
    notify("Fin du backup: %s \n\n%s" % (dateFinBackup,msg),pynotify.URGENCY_NORMAL,notification)

