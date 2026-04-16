from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ GROQ ============
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = None

if GROQ_API_KEY:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except:
        pass


def get_db():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    return None


def execute_sql(sql: str):
    sql_clean = re.sub(r'```sql\n?|```\n?', '', sql.strip())
    sql_clean = sql_clean.replace('\n', ' ').replace('\r', ' ')
    sql_clean = ' '.join(sql_clean.split())
    
    sql_clean = sql_clean.replace('WEEKDAY(', 'EXTRACT(DOW FROM ')
    sql_clean = sql_clean.replace('MONTH(', 'EXTRACT(MONTH FROM ')
    sql_clean = sql_clean.replace('YEAR(', 'EXTRACT(YEAR FROM ')
    sql_clean = sql_clean.replace('NOW()', 'CURRENT_TIMESTAMP')
    sql_clean = sql_clean.replace('CURDATE()', 'CURRENT_DATE')
    
    if not sql_clean.upper().startswith("SELECT"):
        return None, "SELECT uniquement"
    
    try:
        conn = get_db()
        if not conn:
            return None, "Base de données non connectée"
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql_clean)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results, None
    except Exception as e:
        return None, str(e)


# ============ ENDPOINTS ============

@app.get("/dashboard/kpis")
def get_kpis():
    conn = get_db()
    if not conn:
        return {"error": "Base de données non connectée"}
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT COUNT(*) as vehicules_actifs FROM vehicules WHERE statut='actif'")
        v = cursor.fetchone()
        cursor.execute("""
            SELECT COALESCE(SUM(recette),0) as recettes_mois 
            FROM trajets 
            WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) 
            AND EXTRACT(YEAR FROM date_heure_depart)=EXTRACT(YEAR FROM CURRENT_TIMESTAMP) 
            AND statut='termine'
        """)
        r = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as incidents_non_resolus FROM incidents WHERE resolu=0")
        i = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as trajets_en_cours FROM trajets WHERE statut='en_cours'")
        t = cursor.fetchone()
        return {
            "vehicules_actifs": v['vehicules_actifs'] if v else 0,
            "recettes_mois": float(r['recettes_mois']) if r else 0,
            "incidents_non_resolus": i['incidents_non_resolus'] if i else 0,
            "trajets_en_cours": t['trajets_en_cours'] if t else 0
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


@app.get("/dashboard/trajets-chart")
def get_trajets_chart():
    conn = get_db()
    if not conn:
        return {"labels": ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"], "trajets": [0]*7, "recettes": [0]*7}
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT EXTRACT(DOW FROM date_heure_depart) as jour, 
                   COUNT(*) as nb, 
                   COALESCE(SUM(recette),0) as recettes
            FROM trajets 
            WHERE date_heure_depart IS NOT NULL
            GROUP BY EXTRACT(DOW FROM date_heure_depart)
            ORDER BY jour
        """)
        results = cursor.fetchall()
        jours = {0:"Lun",1:"Mar",2:"Mer",3:"Jeu",4:"Ven",5:"Sam",6:"Dim"}
        trajets = [0]*7
        recettes = [0]*7
        for r in results:
            if r['jour'] is not None:
                jour_index = int(r['jour'])
                if 0 <= jour_index <= 6:
                    trajets[jour_index] = r['nb'] or 0
                    recettes[jour_index] = float(r['recettes'] or 0)
        return {"labels": [jours[i] for i in range(7)], "trajets": trajets, "recettes": recettes}
    except:
        return {"labels": ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"], "trajets": [0]*7, "recettes": [0]*7}
    finally:
        cursor.close()
        conn.close()


class ChatRequest(BaseModel):
    question: str


SYSTEM_PROMPT = """Tu es un assistant IA convivial pour la gestion de transport.

Si l'utilisateur dit "bonjour", "salut", répond chaleureusement.
Si l'utilisateur dit "merci", répond avec politesse.

SCHEMA: chauffeurs(nom,prenom), vehicules(immatriculation,marque,modele,statut), trajets(date_heure_depart,recette,statut), incidents(resolu), lignes(code_ligne,nom)

Valeurs: statut vehicules: 'actif','en_maintenance','hors_service'
Jours: EXTRACT(DOW FROM date) (lundi=0)

Exemple bonjour: {"sql": null, "natural": "👋 Bonjour ! Comment puis-je vous aider ?"}
Exemple CA: {"sql": "SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) AND statut='termine'", "natural": "💰 Chiffre d'affaires du mois :"}

Réponds UNIQUEMENT au format JSON."""


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question
    q = question.lower().strip()
    
    # Salutations
    if q in ["bonjour", "salut", "coucou", "hello", "hi"]:
        return {"natural_response": "👋 Bonjour ! Je suis TranspoBot. Posez-moi des questions sur vos véhicules, chauffeurs, trajets ou recettes.", "sql": None, "results": []}
    
    if q in ["merci", "thanks", "bravo"]:
        return {"natural_response": "😊 Avec plaisir ! N'hésitez pas si vous avez d'autres questions.", "sql": None, "results": []}
    
    # Chiffre d'affaires
    if "chiffre d affaires" in q or "ca du mois" in q:
        conn = get_db()
        if not conn:
            return {"natural_response": "❌ Base de données non connectée", "sql": None, "results": []}
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) AND statut='termine'")
            row = cursor.fetchone()
            return {"natural_response": f"💰 Chiffre d'affaires du mois : {row['total']:,.0f} FCFA", "sql": None, "results": [{"total": row['total']}]}
        finally:
            cursor.close()
            conn.close()
    
    # GROQ pour les autres questions
    if client is None:
        return {"natural_response": "❌ IA non configurée (GROQ_API_KEY manquante)", "sql": None, "results": []}
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=500
        )
        response_text = response.choices[0].message.content
        
        match = re.search(r'\{[^{}]*"sql"[^{}]*"natural"[^{}]*\}', response_text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            sql = data.get("sql", "").strip()
            natural = data.get("natural", "")
            
            if not sql or sql == "null":
                return {"natural_response": natural, "sql": None, "results": []}
            
            if sql and "SELECT" in sql.upper():
                results, error = execute_sql(sql)
                if error:
                    return {"natural_response": f"❌ Erreur: {error}", "sql": sql, "results": []}
                return {"natural_response": natural, "sql": sql, "results": results}
        
        return {"natural_response": response_text[:300], "sql": None, "results": []}
    except Exception as e:
        return {"natural_response": f"❌ Erreur: {str(e)}", "sql": None, "results": []}


@app.get("/")
async def root():
    return {"message": "TranspoBot API - Vercel"}


# Handler pour Vercel
handler = app