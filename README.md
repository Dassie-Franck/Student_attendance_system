# Student Attendance System - Reconnaissance Faciale

##  Description du projet
Ce projet a pour objectif de mettre en place un système de **présence automatisée pour étudiants** basé sur la reconnaissance faciale.  
Il permet de détecter un visage via la webcam, de l'identifier grâce aux embeddings générés, et de marquer l'étudiant comme **présent**.

Technologies utilisées :
- Python 3.10+ dans un environement .venv pour gerer la compatibiliter avec les bibiotheque de gestion embedding et reconnaissance faciale
- [DeepFace](https://github.com/serengil/deepface) (pour la reconnaissance faciale)
- OpenCV (pour la capture et affichage vidéo)
- NumPy et JSON (pour la gestion des embeddings)
- TensorFlow (backend DeepFace)

---

##  Fonctionnalités réalisées

1. **Génération d’embeddings pour chaque étudiant**
   - Images utilisées : `avant.jpg` (profil frontal).  
   - Fichier généré : `dataset/etudiant_id/embeddings.json`.  
   - Modèles DeepFace disponibles : `ArcFace`, `Facenet512`, etc.

2. **Reconnaissance faciale via webcam**
   - Détection du visage et extraction de l’embedding.
   - Comparaison avec les embeddings stockés.
   - Affichage du nom et d’un cadre coloré autour du visage.
   - FPS affichés pour mesurer la fluidité.
   - Gestion des cas : visage inconnu ou mal éclairé. (pas encore gerer)

3. **Optimisation**
   - Recalcul de l’embedding toutes les `FRAME_SKIP` frames pour améliorer la fluidité.
   - Gestion des erreurs lors de la capture vidéo ou de la reconnaissance.
   - Distance cosinus utilisée pour la comparaison.

4. **Prise en compte des conditions difficiles**
   - Gestion de la luminosité faible.
   - Reconnaissance même si l’étudiant est assis au fond de la salle (en ajustant le seuil).

---
NB: le fonctionement des roles attribuer aux ResponsableFiliere , Enseignant , Delegue , Etudiant
---
1️⃣ Responsable de filière (Head / ResponsableFiliere)

Peut créer un compte pour lui-même.

Peut créer des comptes pour les enseignants et les délégués.

Peut superviser la création des cours.

Peut voir l’état de présence des étudiants et statistiques global.

Peut attribuer ou modifier certains droits si nécessaire.

2️⃣ Enseignant

Peut se connecter à l’application.

Peut créer des cours pour effectuer l'appel(reconnaissance faciale).

Peut marquer la présence des étudiants via la caméra / reconnaissance faciale.

Peut associer son compte à un cours via user_id.

>Ne peut pas créer de comptes pour d’autres utilisateurs.

3️⃣ Délégué

Peut se connecter à l’application.

>Peut creer un cours seulement si l’enseignant est absent.

Peut marquer la présence des étudiants.

>Ne peut pas créer de comptes.

>Ne peut pas créer ou modifier les cours.
---
##  differents liens pour acceder aux pages front de test

page login accessible par tout le monde
>http://127.0.0.1:5000/auth/login

page register accessible uniquement par le responsable
>http://127.0.0.1:5000/auth/register

page creation de cours accessible par le delegue et enseignant
>http://127.0.0.1:5000/cours/create

page liste de cours accessible par le delegue et enseignant
>http://127.0.0.1:5000/cours/list

page dashboard accessible uniquement pas le responsableFiliere
>http://127.0.0.1:5000/dashboard/head

page dashboard  accessible par le delegue et enseignant
>http://127.0.0.1:5000/dashboard/enseignant

page creation d'etudiant accessible uniquement par le responsable

>http://127.0.0.1:5000/students/create

## Etapes d'utilisation :
1- cloner le repot et ouvrir avec pycharm 

2- install tout les dependances pour les bibiotheques

3- executez le run.app

4- les etapes 1 et 2 et 3 sont dependantes , toujours verifier la reussites de chaque etapes avant de continuer

---

>  Les images **ne sont pas incluses sur GitHub** pour éviter de surcharger le repo. vous devez generer vous meme vos images.

---

##  Comment utiliser le projet

1. **Installer les dépendances** :

```bash
pip install -r requirements.txt


