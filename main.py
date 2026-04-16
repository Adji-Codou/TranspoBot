"""
TranspoBot - Version PostgreSQL avec IA intelligente
Adapté de ta version MySQL d'origine
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
        print("✅ Groq configuré")
    except Exception as e:
        print(f"⚠️ Erreur Groq: {e}")
else:
    print("❌ GROQ_API_KEY non trouvée")

def get_db():
    # Priorité à DATABASE_URL pour Render
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    
    # Fallback local
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "transpobot")
    )

# ============ API KPIs ============

@app.get("/login")
async def login_page():
    login_path = os.path.join(os.path.dirname(__file__), "login.html")
    if os.path.exists(login_path):
        with open(login_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>login.html non trouvé</h1>")

@app.get("/dashboard/kpis")
def get_kpis():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT COUNT(*) as vehicules_actifs FROM vehicules WHERE statut='actif'")
        v = cursor.fetchone()
        cursor.execute("SELECT COALESCE(SUM(recette),0) as recettes_mois FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) AND EXTRACT(YEAR FROM date_heure_depart)=EXTRACT(YEAR FROM CURRENT_TIMESTAMP) AND statut='termine'")
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
        print(f"Erreur KPIs: {e}")
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

# ============ GRAPHIQUE ============
@app.get("/dashboard/trajets-chart")
def get_trajets_chart():
    conn = get_db()
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
    except Exception as e:
        print(f"Erreur graphique: {e}")
        return {"labels": ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"], "trajets": [0]*7, "recettes": [0]*7}
    finally:
        cursor.close()
        conn.close()

# ============ CHATBOT ============
class ChatRequest(BaseModel):
    question: str

def execute_sql(sql: str):
    sql_clean = re.sub(r'```sql\n?|```\n?', '', sql.strip())
    sql_clean = sql_clean.replace('\n', ' ').replace('\r', '')
    
    # Conversion MySQL -> PostgreSQL
    sql_clean = sql_clean.replace('WEEKDAY(', 'EXTRACT(DOW FROM ')
    sql_clean = sql_clean.replace('MONTH(', 'EXTRACT(MONTH FROM ')
    sql_clean = sql_clean.replace('YEAR(', 'EXTRACT(YEAR FROM ')
    sql_clean = sql_clean.replace('NOW()', 'CURRENT_TIMESTAMP')
    sql_clean = sql_clean.replace('CURDATE()', 'CURRENT_DATE')
    
    if not sql_clean.upper().startswith("SELECT"):
        return None, "SELECT uniquement"
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

# PROMPT SYSTÈME INTELLIGENT (inspiré de ton ancien)
SYSTEM_PROMPT = """
Tu es un assistant IA spécialisé dans la gestion de transport. Tu dois être poli, amical et très intelligent.

RÈGLES IMPORTANTES:
1. Si l'utilisateur dit "bonjour", "salut", "coucou", "ça va", "comment ça va" : réponds chaleureusement
2. Si l'utilisateur dit "merci", "bravo" : réponds avec plaisir
3. Pour les questions sur les données : génère une requête SQL adaptée
4. Pour les questions générales : réponds normalement sans SQL

Voici le SCHEMA EXACT de la base de données PostgreSQL:

trajets: id, date_heure_depart, recette, statut
chauffeurs: id, nom, prenom, statut
vehicules: id, immatriculation, marque, modele, statut
incidents: id, trajet_id, type_incident, resolu
lignes: id, code_ligne, nom, point_depart, point_arrivee

VALEURS EXACTES:
- statut vehicules: 'actif', 'en_maintenance', 'hors_service'
- statut chauffeurs: 'actif', 'en_conge', 'suspendu'
- statut trajets: 'planifie', 'en_cours', 'termine', 'annule'
- resolu incidents: 0 = non résolu, 1 = résolu

JOURS DE LA SEMAINE (DOW):
- lundi = 0, mardi = 1, mercredi = 2, jeudi = 3, vendredi = 4, samedi = 5, dimanche = 6

FONCTIONS POSTGRESQL À UTILISER:
- EXTRACT(DOW FROM date_heure_depart) pour le jour de la semaine
- EXTRACT(MONTH FROM date_heure_depart) pour le mois
- EXTRACT(YEAR FROM date_heure_depart) pour l'année
- CURRENT_TIMESTAMP pour la date/heure actuelle
- COALESCE pour les valeurs NULL

EXEMPLES:
Question: "chiffre d'affaires du mois"
SQL: SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) AND EXTRACT(YEAR FROM date_heure_depart)=EXTRACT(YEAR FROM CURRENT_TIMESTAMP) AND statut='termine'

Question: "nombre de trajets le lundi"
SQL: SELECT COUNT(*) as total FROM trajets WHERE EXTRACT(DOW FROM date_heure_depart)=0

Question: "quel chauffeur a le plus d'incidents"
SQL: SELECT c.nom, c.prenom, COUNT(i.id) as nb_incidents FROM chauffeurs c JOIN trajets t ON c.id=t.chauffeur_id JOIN incidents i ON t.id=i.trajet_id GROUP BY c.id, c.nom, c.prenom ORDER BY nb_incidents DESC LIMIT 1

Question: "bonjour"
SQL: NE PAS METTRE DE SQL, juste répondre avec un message amical

Réponds UNIQUEMENT au format JSON: {"sql": "requete_sql_ou_rien", "natural": "reponse_naturelle"}
"""

@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question
    q = question.lower().strip()
    
    # ========== TRAITEMENT DES SALUTATIONS ==========
    salutations = ["bonjour", "salut", "coucou", "hello", "hi", "hey", "ça va", "comment ça va", "bienvenue", "cava", "yo"]
    remerciements = ["merci", "thanks", "thank you", "bravo", "merci beaucoup", "c'est gentil"]
    
    for mot in salutations:
        if mot in q:
            return {
                "natural_response": "👋 Bonjour ! Je suis TranspoBot, votre assistant IA pour la gestion de transport.\n\n❓ Je peux répondre à toutes vos questions sur :\n• Les véhicules (actifs, en maintenance)\n• Les chauffeurs (performances, incidents)\n• Les trajets (nombre, recettes)\n• Les incidents\n• Les lignes\n\nPosez-moi votre question en langage naturel !",
                "sql": None,
                "results": []
            }
    
    for mot in remerciements:
        if mot in q:
            return {
                "natural_response": "🤖 Avec plaisir ! Je reste à votre disposition pour toute question sur vos données de transport.",
                "sql": None,
                "results": []
            }
    
    # ========== TRAITEMENT DIRECT PRIORITAIRE ==========
    
    # 1. Chiffre d'affaires
    if "chiffre d affaires" in q or "ca du mois" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(recette),0) as total 
                FROM trajets 
                WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) 
                AND EXTRACT(YEAR FROM date_heure_depart)=EXTRACT(YEAR FROM CURRENT_TIMESTAMP) 
                AND statut='termine'
            """)
            row = cursor.fetchone()
            return {
                "natural_response": f"💰 Chiffre d'affaires du mois : {row['total']:,.0f} FCFA",
                "sql": "SELECT SUM(recette) FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_DATE) AND statut='termine'",
                "results": [{"total": row['total']}]
            }
        finally:
            cursor.close()
            conn.close()
    
    # 2. Véhicules en maintenance
    if "vehicules en maintenance" in q or "véhicules en maintenance" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'en_maintenance'")
            rows = cursor.fetchall()
            natural = "🔧 Véhicules en maintenance :" if rows else "✅ Aucun véhicule en maintenance"
            return {
                "natural_response": natural,
                "sql": "SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'en_maintenance'",
                "results": rows
            }
        finally:
            cursor.close()
            conn.close()
    
    # 3. Lundi et mardi (avec ou sans incidents)
    if "lundi et mardi" in q or "mardi et lundi" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            if "incident" in q:
                cursor.execute("""
                    SELECT 
                        CASE WHEN EXTRACT(DOW FROM t.date_heure_depart)=0 THEN 'Lundi' 
                             WHEN EXTRACT(DOW FROM t.date_heure_depart)=1 THEN 'Mardi' END as jour,
                        COUNT(DISTINCT t.id) as nb_trajets,
                        COUNT(i.id) as nb_incidents
                    FROM trajets t
                    LEFT JOIN incidents i ON t.id = i.trajet_id
                    WHERE EXTRACT(DOW FROM t.date_heure_depart) IN (0,1)
                    GROUP BY jour
                """)
                natural = "📊 Nombre de trajets et incidents le lundi et mardi :"
            else:
                cursor.execute("""
                    SELECT 
                        CASE WHEN EXTRACT(DOW FROM date_heure_depart)=0 THEN 'Lundi' 
                             WHEN EXTRACT(DOW FROM date_heure_depart)=1 THEN 'Mardi' END as jour,
                        COUNT(*) as nb_trajets
                    FROM trajets
                    WHERE EXTRACT(DOW FROM date_heure_depart) IN (0,1)
                    GROUP BY jour
                """)
                natural = "📊 Nombre de trajets le lundi et mardi :"
            
            results = cursor.fetchall()
            return {
                "natural_response": natural,
                "sql": "SELECT CASE WHEN EXTRACT(DOW FROM date_heure_depart)=0 THEN 'Lundi' WHEN EXTRACT(DOW FROM date_heure_depart)=1 THEN 'Mardi' END as jour, COUNT(*) as nb_trajets FROM trajets WHERE EXTRACT(DOW FROM date_heure_depart) IN (0,1) GROUP BY jour",
                "results": results
            }
        finally:
            cursor.close()
            conn.close()
    
    # 4. Samedi et dimanche
    if "samedi et dimanche" in q or "dimanche et samedi" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT 
                    CASE WHEN EXTRACT(DOW FROM date_heure_depart)=5 THEN 'Samedi' 
                         WHEN EXTRACT(DOW FROM date_heure_depart)=6 THEN 'Dimanche' END as jour,
                    COUNT(*) as nb_trajets,
                    COALESCE(SUM(recette),0) as total_recettes
                FROM trajets
                WHERE EXTRACT(DOW FROM date_heure_depart) IN (5,6)
                GROUP BY jour
            """)
            results = cursor.fetchall()
            return {
                "natural_response": "📊 Nombre de trajets et recettes le samedi et dimanche :",
                "sql": "SELECT CASE WHEN EXTRACT(DOW FROM date_heure_depart)=5 THEN 'Samedi' WHEN EXTRACT(DOW FROM date_heure_depart)=6 THEN 'Dimanche' END as jour, COUNT(*) as nb_trajets, SUM(recette) as total_recettes FROM trajets WHERE EXTRACT(DOW FROM date_heure_depart) IN (5,6) GROUP BY jour",
                "results": results
            }
        finally:
            cursor.close()
            conn.close()
    
    # 5. Chauffeur avec le plus d'incidents
    if "plus d'incidents" in q or "chauffeur a le plus d'incidents" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT c.nom, c.prenom, COUNT(i.id) as nb_incidents
                FROM chauffeurs c
                JOIN trajets t ON c.id = t.chauffeur_id
                JOIN incidents i ON t.id = i.trajet_id
                GROUP BY c.id, c.nom, c.prenom
                ORDER BY nb_incidents DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return {
                    "natural_response": f"🚨 Le chauffeur avec le plus d'incidents est {row['prenom']} {row['nom']} avec {row['nb_incidents']} incidents.",
                    "sql": "SELECT c.nom, c.prenom, COUNT(i.id) as nb_incidents FROM chauffeurs c JOIN trajets t ON c.id=t.chauffeur_id JOIN incidents i ON t.id=i.trajet_id GROUP BY c.id ORDER BY nb_incidents DESC LIMIT 1",
                    "results": [row]
                }
            return {"natural_response": "Aucun incident trouvé", "sql": None, "results": []}
        finally:
            cursor.close()
            conn.close()
    
    # 6. Recettes et trajets par chauffeur
    if "recettes et trajets par chauffeur" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, 
                       COALESCE(SUM(t.recette),0) as total_recettes,
                       COUNT(t.id) as nb_trajets
                FROM chauffeurs c
                LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine'
                GROUP BY c.id, c.prenom, c.nom
                ORDER BY total_recettes DESC
            """)
            results = cursor.fetchall()
            return {
                "natural_response": "💰 Recettes et trajets par chauffeur :",
                "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, COALESCE(SUM(t.recette),0) as total_recettes, COUNT(t.id) as nb_trajets FROM chauffeurs c LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC",
                "results": results
            }
        finally:
            cursor.close()
            conn.close()
    
    # 7. Liste des lignes
    if "liste des lignes" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes")
            results = cursor.fetchall()
            return {
                "natural_response": "🚏 Liste des lignes :",
                "sql": "SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes",
                "results": results
            }
        finally:
            cursor.close()
            conn.close()
    
    # 8. Nombre de trajets par jour (simple)
    jours_simples = {"lundi":0, "mardi":1, "mercredi":2, "jeudi":3, "vendredi":4, "samedi":5, "dimanche":6}
    for jour, index in jours_simples.items():
        if jour in q and "nombre" in q and "trajet" in q and "et" not in q:
            conn = get_db()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                cursor.execute("SELECT COUNT(*) as total FROM trajets WHERE EXTRACT(DOW FROM date_heure_depart) = %s", (index,))
                row = cursor.fetchone()
                return {
                    "natural_response": f"Il y a {row['total']} trajets le {jour}.",
                    "sql": f"SELECT COUNT(*) FROM trajets WHERE EXTRACT(DOW FROM date_heure_depart) = {index}",
                    "results": [{"total": row['total']}]
                }
            finally:
                cursor.close()
                conn.close()
    
    # ========== GROQ POUR LES AUTRES QUESTIONS ==========
    if client is None:
        return {"natural_response": "❌ IA non configurée.", "sql": None, "results": []}
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}],
            temperature=0.1,
            max_tokens=800
        )
        response_text = response.choices[0].message.content
        
        match = re.search(r'\{[^{}]*"sql"[^{}]*"natural"[^{}]*\}', response_text, re.DOTALL)
        
        if match:
            try:
                json_str = match.group()
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                data = json.loads(json_str)
                sql = data.get("sql", "")
                natural = data.get("natural", response_text[:200])
                results = []
                if sql and sql.strip():
                    # Vérifier que ce n'est pas une fausse requête
                    if "SELECT '" in sql.upper() and "FROM" not in sql.upper():
                        return {
                            "natural_response": "Je ne peux pas répondre à cette question. Posez-moi une question sur vos données de transport.",
                            "sql": None,
                            "results": []
                        }
                    results, error = execute_sql(sql)
                    if error:
                        natural = f"❌ {error}\n\n{natural}"
                return {"natural_response": natural, "sql": sql if sql else None, "results": results if results else []}
            except:
                pass
        
        return {"natural_response": response_text[:500], "sql": None, "results": []}
        
    except Exception as e:
        return {"natural_response": f"❌ Erreur: {str(e)}", "sql": None, "results": []}

# ============ ENDPOINTS ============
@app.get("/vehicules")
def get_vehicules():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, immatriculation, marque, modele, statut FROM vehicules")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.get("/chauffeurs")
def get_chauffeurs():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, nom, prenom, telephone, statut FROM chauffeurs")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.get("/lignes")
def get_lignes():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.get("/trajets")
def get_trajets(limit: int = 10):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT t.id, t.date_heure_depart, t.statut, t.recette, 
                   CONCAT(c.prenom, ' ', c.nom) as chauffeur
            FROM trajets t 
            LEFT JOIN chauffeurs c ON t.chauffeur_id = c.id
            ORDER BY t.date_heure_depart DESC 
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.get("/", response_class=HTMLResponse)
async def get_html():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>TranspoBot</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)