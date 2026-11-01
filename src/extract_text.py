import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

def extract_text_vectors(documents):
    # Concatène description + keywords
   # Nettoyage du texte avant vectorisation
    text_data = [
        f"{doc.get('description', '')} {' '.join(doc.get('keywords', []))}".lower() 
        for doc in documents
    ]
    # TF-IDF vectorisation
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=4000,
        ngram_range=(1, 2),  # Capture les bigrammes
        min_df=3  # Ignore les termes trop rares
    )
    # Gestion mémoire optimale
    vectors = vectorizer.fit_transform(text_data)
    
    # Sauvegarder le modèle et les vecteurs
    with open("text_vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    with open("text_vectors.npz", "wb") as f:
        from scipy import sparse
        sparse.save_npz(f, vectors)
    
     # Sauvegarde additionnelle du vocabulaire
    with open("text_features.json", "w") as f:
        json.dump(vectorizer.get_feature_names_out().tolist(), f)

    print("Vecteurs textuels extraits et sauvegardés.")
    return vectors

# Utilisation
if __name__ == "__main__":
    import json
    
    with open("documents.json", "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    extract_text_vectors(documents)

