from flask import Flask, request, render_template, jsonify
from elasticsearch import Elasticsearch

#Initialise l'app Flask
app = Flask(__name__)

#configuraton d'un filtre Jinja2 pour formater les nombres
@app.template_filter('format_number')
def format_number_filter(value):
    return f"{value:,}".replace(",", " ")

#Connexion à elasticSearch
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "unsplash_final"

TRANSLATIONS = {
    "ville": "city",
    "montagne": "mountain",
    "plage": "beach"
}

@app.route('/')
def home():
    return render_template('search.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    translated_query = TRANSLATIONS.get(query, query)
    
    body = {
    "query": {
        "bool": {
            "should": [
                {
                    "match": {
                        "keywords": {
                            "query": translated_query,
                            "boost": 5
                        }
                    }
                },
                {
                    "match": {
                        "description": {
                            "query": translated_query,
                            "boost": 2 ,
                            "fuzziness": "AUTO"
                        }
                    }
                },
                {
                    "match": {
                        "alt_description": {
                            "query": translated_query,
                            "boost": 1 ,
                            "fuzziness": "AUTO"
                        }
                    }
                }
            ],
            "minimum_should_match": 1
        }
    },
    "size": 12
}

    
    results = es.search(index=INDEX_NAME, body=body)
    return render_template('results.html',
                        results=results["hits"]["hits"],
                        query=query,
                        total=results["hits"]["total"]["value"])

@app.route('/suggest')
def suggest():
    prefix = request.args.get('q', '').lower()
    
    if len(prefix) < 2:
        return jsonify([])
    
    body = {
        "suggest": {
            "keyword-suggest": {
                "prefix": prefix,
                "completion": {
                    "field": "keywords_suggest",
                    "skip_duplicates": True,
                    "size": 5
                }
            }
        }
    }
    
    try:
        suggestions = es.search(index=INDEX_NAME, body=body)
        options = suggestions['suggest']['keyword-suggest'][0]['options']
        return jsonify([opt['text'] for opt in options])
    except Exception as e:
        print(f"Erreur de suggestion: {str(e)}")
        return jsonify([])

if __name__ == '__main__':
    # Debug désactivé : à activer uniquement en développement local.
    app.run(debug=False)