# PixSearch

Moteur de recherche d'images (projet académique, avril 2025) sur le dataset Unsplash Lite.

## Fonctionnement
1. `DataBase.py` : lit les fichiers TSV d'Unsplash (pandas), nettoie les données et génère `documents.json` (25 000 photos).
2. `extract_text.py` : vectorisation TF-IDF (scikit-learn, 4 000 termes, bigrammes) des descriptions et mots-clés.
3. `extract_image.py` : détection d'objets (YOLOv8n) et vecteurs d'images (MobileNetV3-small), modèles pré-entraînés, sur un échantillon de 500 images.
4. `indexation.py` : création de l'index Elasticsearch (analyseur français, autocomplétion) et indexation des documents de `output_vectors.json`.
5. `app.py` : application Flask avec les routes `/` (accueil), `/search` (recherche) et `/suggest` (autocomplétion).

La recherche interroge Elasticsearch sur les mots-clés (poids 5) et la description (poids 2, avec tolérance aux fautes de frappe).

## Utilisation
Depuis le dossier `src/`, avec Elasticsearch 8.17 lancé sur http://localhost:9200 :

    python DataBase.py chemin/vers/MyDataBase
    python extract_text.py
    python extract_image.py
    python indexation.py
    python app.py

Dépendances : `pip install -r requirements.txt`

Le dataset n'est pas inclus : il se télécharge sur le site officiel d'Unsplash (voir leurs conditions d'utilisation).

## Limites
- Modèles pré-entraînés utilisés tels quels : aucun entraînement ni évaluation chiffrée dans ce dépôt.
- Les vecteurs visuels et TF-IDF sont calculés mais ne sont pas utilisés par la requête de recherche, qui repose sur Elasticsearch et le texte.
- Les vecteurs visuels ne sont calculés que pour 500 documents.
- La traduction des requêtes se limite à un dictionnaire de trois mots (ville, montagne, plage), appliqué seulement si la requête entière correspond.
