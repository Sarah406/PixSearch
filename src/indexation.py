from elasticsearch import Elasticsearch, helpers
import json
import os
from pathlib import Path
from elasticsearch.helpers import BulkIndexError

# 1. Configuration
DATASET_PATH = Path("output_vectors.json")  # Chemin vers le fichier de données (issu de extract_image.py)
ES_HOST = "http://localhost:9200"
INDEX_NAME = "unsplash_final"  # Nouveau nom d'index

# 2. Connexion Elasticsearch
es = Elasticsearch(ES_HOST)

# 3. Mapping simplifié mais efficace
mapping = {
        "settings": {
            "number_of_shards": 1,
            "analysis": {
                "filter": {
                    "french_elision": {
                        "type": "elision",
                        "articles": ["l", "m", "t", "qu", "n", "s", "j", "d"]
                    }
                },
                "analyzer": {
                    "french": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "french_elision", "asciifolding"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "description": {"type": "text", "analyzer": "french"},
                "keywords": {"type": "keyword"},
                "keywords_suggest": {"type": "completion"},  # champ pour les suggestions
                "image_url": {"type": "keyword"},
                "views": {"type": "integer"}  
            }
        }
    }

def create_index():
    """Crée l'index avec gestion des erreurs"""
    try:
        if es.indices.exists(index=INDEX_NAME):
            es.indices.delete(index=INDEX_NAME)
        
        es.indices.create(index=INDEX_NAME, body=mapping)
        print(f"Index {INDEX_NAME} créé avec succès")
        return True
    except Exception as e:
        print(f"Erreur création index: {str(e)}")
        return False

def load_documents():
    """Charge les documents avec validation"""
    if not DATASET_PATH.exists():
        print(f"Fichier introuvable: {DATASET_PATH}")
        print(f"Contenu du dossier: {os.listdir()}")
        return None
    
    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            docs = json.load(f)
            print(f"{len(docs)} documents chargés")
            return docs
    except Exception as e:
        print(f"Erreur chargement fichier: {str(e)}")
        return None

def index_documents(documents):
    """Indexation avec nettoyage des vecteurs"""
    actions = []
    for doc in documents:
        # Validation des champs obligatoires
        if not all(k in doc for k in ["description", "keywords", "url"]):
            continue
        
        # Nettoyage des objets détectés
        valid_objects = []
        for obj in doc.get("detected_objects", []):
            vector = obj.get("vector", [])
            if (
                isinstance(vector, list) and
                len(vector) == 576 and
                all(isinstance(x, (float, int)) for x in vector)
            ):
                valid_objects.append(obj)
        
        # Ajoute les objets valides au document 
        doc["detected_objects"] = valid_objects
        
        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                "description": doc.get("description", ""),
                "keywords": doc.get("keywords", []),
                "keywords_suggest": {
                    "input": doc.get("keywords", []),
                    "weight": doc.get("views", 0)
                },
                "image_url": doc.get("url", ""),
                "views": doc.get("views", 0),
            }
        })

   
    try:
        success, _ = helpers.bulk(es, actions, chunk_size=100, raise_on_error=True)
        print(f"\nIndexation réussie: {success}/{len(documents)} documents")
        return True
    except BulkIndexError as e:
        print(f"\nErreur d'indexation: {len(e.errors)} documents échoués")
        for i, error in enumerate(e.errors[:5]):
            print(f"Erreur {i+1}: {error}")
        return False


if __name__ == "__main__":
    print("\n=== Début indexation ===")
    
    # Étape 1: Création index
    if not create_index():
        exit(1)
    
    # Étape 2: Chargement données
    documents = load_documents()
    if not documents:
        exit(1)
    
    # Étape 3: Indexation
    if not index_documents(documents):
        exit(1)
    
    print("=== Indexation terminée avec succès ===")