
# Prévention Risques Naturels

Ce projet permet d'extraire et d'analyser des données de risques naturels pour des adresses spécifiques en France. Il utilise des services web pour obtenir des coordonnées géographiques, télécharge des rapports PDF, et extrait des informations pertinentes via OCR.

## Structure du projet

- **`adressesTest.csv`** : Fichier contenant les adresses à analyser.
- **`risquesNaturels.py`** : Script principal qui orchestre le flux de travail complet.
- **`risquesNaturels.py`** : Contient des fonctions utilitaires pour la conversion d'adresses, la récupération de coordonnées, le téléchargement de PDF, et le traitement OCR.
- **`output.csv`** : Fichier de sortie contenant les résultats de l'analyse.
- **`requirements.txt`** : Liste des modules Python requis.

## Fonctionnalités

- **Conversion d'adresses** : Utilise la fonction `convertir_en_diminutif` pour convertir les adresses en diminutifs afin de faciliter la recherche.
- **Récupération de coordonnées** : Utilise la fonction `latlon` pour obtenir les coordonnées géographiques (latitude et longitude) d'une adresse.
- **Téléchargement de PDF** : Utilise la fonction `pdf` pour télécharger des rapports PDF basés sur les coordonnées géographiques.
- **Traitement OCR** : Utilise la fonction `process_pdf` pour extraire du texte des PDF téléchargés à l'aide de la reconnaissance optique de caractères (OCR).
- **Extraction de données** : Utilise la fonction `extract_data` pour extraire des informations spécifiques des textes obtenus via OCR.

## Installation

Clonez le dépôt :

```bash

git clone https://github.com/Vaal34/PreventionRisquesNaturels.git

```

Installez les dépendances :

```bash

pip install -r requirements.txt

```

## Utilisation

Pour exécuter le script principal :

```bash

python3 risquesNaturels.py adressesTest.csv

```
