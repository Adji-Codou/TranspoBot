"""
TranspoBot - Version Intelligence Artificielle PostgreSQL
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ CONFIGURATION GROQ ============
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = None

if GROQ_API_KEY:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Intelligence Artificielle configurée")
    except Exception as e:
        print(f"⚠️ Erreur config IA: {e}")

# ============ CONNEXION BASE DE DONNÉES ============
def get_db():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "transpobot")
    )

def execute_sql(sql: str):
    """Nettoie et exécute la requête SQL générée par l'IA"""
    # Nettoyage des balises Markdown si présentes
    sql_clean = re.sub(r'```sql\n?|```\n?', '', sql.strip())
    
    if not sql_clean.upper().startswith("SELECT"):
        return None, "Seules les lectures (SELECT) sont autorisées."
    
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql_clean)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results, None
    except Exception as e:
        return None, str(e)

# ============ LOGIQUE IA (PROMPT) ============
SYSTEM_PROMPT = """
Tu es TranspoBot, l'assistant IA expert de la gestion de transport.
Ton rôle est d'analyser la question de l'utilisateur et de générer une requête SQL PostgreSQL pour interroger la base de données.

SCHEMA DISPONIBLE :
- chauffeurs (id, nom, prenom, telephone, statut)
- vehicules (id, immatriculation, marque, modele, statut)
- trajets (id, date_heure_depart, recette, statut, chauffeur_id, vehicule_id)
- incidents (id, trajet_id, type_incident, resolu, date_incident)
- lignes (id, code_ligne, nom, point_depart, point_arrivee)

RÈGLES CRITIQUES :
1. PostgreSQL : Utilise CURRENT_DATE, CURRENT_TIMESTAMP et EXTRACT(DOW FROM ...).
2. Toujours retourner un JSON strict avec deux clés : 
   - "sql": La requête SQL (ou null si c'est une salutation).
   - "natural": Une réponse polie et courte décrivant ce que tu fais ou répondant à la salutation.
3. Si la question est "Bonjour", réponds poliment sans SQL.
4. Si la question demande des données, génère le SQL correspondant.

FORMAT DE RÉPONSE ATTENDU (JSON) :
{"sql": "SELECT ...", "natural": "Voici les résultats pour..."}
"""

class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
def chat(request: ChatRequest):
    if client is None:
        return {"natural_response": "Désolé, l'IA n'est pas configurée.", "sql": None, "results": []}

    try:
        # Appel à Llama 3 via Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.question}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        # Parsing de la réponse de l'IA
        ai_data = json.loads(chat_completion.choices[0].message.content)
        sql_query = ai_data.get("sql")
        natural_text = ai_data.get("natural", "Voici ce que j'ai trouvé :")
        
        db_results = []
        if sql_query:
            db_results, error = execute_sql(sql_query)
            if error:
                natural_text = f"Désolé, j'ai eu un problème avec la base de données : {error}"

        return {
            "natural_response": natural_text,
            "sql": sql_query,
            "results": db_results if db_results else []
        }

    except Exception as e:
        return {"natural_response": f"Erreur système : {str(e)}", "sql": None, "results": []}

# ============ AUTRES ENDPOINTS (TABLEAU DE BORD) ============

@app.get("/dashboard/kpis")
def get_kpis():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT COUNT(*) as v FROM vehicules WHERE statut='actif'")
        v = cursor.fetchone()
        cursor.execute("SELECT COALESCE(SUM(recette),0) as r FROM trajets WHERE statut='termine'")
        r = cursor.fetchone()
        return {
            "vehicules_actifs": v['v'],
            "recettes_mois": float(r['r']),
            "incidents_non_resolus": 0,
            "trajets_en_cours": 0
        }
    finally:
        cursor.close()
        conn.close()

@app.get("/", response_class=HTMLResponse)
async def get_html():
    path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>TranspoBot est en ligne</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))