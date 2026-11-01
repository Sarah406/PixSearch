import sys
import pandas as pd
import os
import json

class UnsplashDatabase:

    #Initialise la classe avec le chemin vers les données
    def __init__(self, data_path):
        self.data_path = data_path
        self.datasets = {
            'photos': None,
            'keywords': None,
            'colors': None
        }
        
    #Charge les fichiers de base de données photos.tsv000 et keywords.tsv000
    def load_basic_data(self):
        try:
            # Charge les 2 fichiers essentiels
            self.datasets['photos'] = pd.read_csv(
                os.path.join(self.data_path, "photos.tsv000"), 
                sep='\t', 
                header=0,
                usecols=['photo_id', 'photo_image_url', 'photo_description', 'stats_views']
            )
            
            self.datasets['keywords'] = pd.read_csv(
                os.path.join(self.data_path, "keywords.tsv000"),
                sep='\t',
                header=0,
                usecols=['photo_id', 'keyword']
            )
            
            print("Données de base chargées avec succès")
            return True
            
        except Exception as e:
            print(f"Erreur lors du chargement: {str(e)}")
            return False
    
    #Charge les données ou les fichiers supplémentaires si disponibles (ex : couleurs) (optionnel)
    def load_additional_data(self):
        try:
            # Exemple avec colors.tsv000
            if os.path.exists(os.path.join(self.data_path, "colors.tsv000")):
                self.datasets['colors'] = pd.read_csv(
                    os.path.join(self.data_path, "colors.tsv000"),
                    sep='\t',
                    header=0,
                    usecols=['photo_id', 'hex']
                )
                print("Données supplémentaires chargées")
            return True
        except Exception as e:
            print(f"Erreur données supplémentaires: {str(e)}")
            return False
    

   #Nettoie les descriptions et supprime les images invalides: "Nettoyage basique des données"
    def clean_data(self):
        if self.datasets['photos'] is not None: 
            # Nettoie les descriptions
            self.datasets['photos']['photo_description'] = (
                self.datasets['photos']['photo_description']
                .fillna("No description")
                .str[:500]  # Limite la taille
            )
            # Filtre les photos sans image_url
            self.datasets['photos'] = self.datasets['photos'].dropna(subset=['photo_image_url'])
            print("Données nettoyées")


   #Structure les données sous forme de documents exploitables
    def prepare_documents(self, limit=None):
        """Prépare les documents pour l'indexation"""
        if self.datasets['photos'] is None:
            return []

        # Option pour limiter le nombre de documents (utile pour les tests)
        photos = self.datasets['photos']
        if limit:
            photos = photos.head(limit)
        
        documents = []
        for _, photo in photos.iterrows():
            doc = {
                "id": photo['photo_id'],
                "url": photo['photo_image_url'],
                "description": photo['photo_description'],
                "views": int(photo['stats_views']),
                "keywords": [],
                "colors": []
            }
            
            # Ajoute les keywords si disponibles
            if self.datasets['keywords'] is not None:
                doc['keywords'] = self.datasets['keywords'][
                    self.datasets['keywords']['photo_id'] == photo['photo_id']
                ]['keyword'].tolist()
            
            # Ajoute les couleurs si disponibles
            if self.datasets['colors'] is not None:
                doc['colors'] = self.datasets['colors'][
                    self.datasets['colors']['photo_id'] == photo['photo_id']
                ]['hex'].tolist()
            
            documents.append(doc)
        
        print(f"{len(documents)} documents préparés")
        return documents
    
    #Sauvegarde les documents dans un fichier JSON utilisable pour l'indexation
    def save_to_json(self, documents, filename="documents.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            print(f"Données sauvegardées dans {filename}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {str(e)}")
            return False

if __name__ == "__main__":
    # 1. Initialisation
    db = UnsplashDatabase(sys.argv[1] if len(sys.argv) > 1 else "MyDataBase")
    
    # 2. Chargement des données (étape par étape)
    if db.load_basic_data():
        db.load_additional_data()  # Optionnel
        db.clean_data()
        
        # 3. Préparation des documents (peut limiter avec limit=100 pour tester)
        documents = db.prepare_documents()  
        
        # 4. Sauvegarde
        if documents:
            db.save_to_json(documents)
            
            # Affiche un exemple
            print("\nExemple de document:")
            print(json.dumps(documents[0], indent=2))