"""
TranspoBot - Version Finale avec fallback pour jours multiples
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import psycopg2
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
        print(f"⚠️ Erreur: {e}")
else:
    print("❌ GROQ_API_KEY non trouvée")

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER", "root"),
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
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as vehicules_actifs FROM vehicules WHERE statut='actif'")
        v = cursor.fetchone()
        cursor.execute("SELECT COALESCE(SUM(recette),0) as recettes_mois FROM trajets WHERE MONTH(date_heure_depart)=MONTH(NOW()) AND YEAR(date_heure_depart)=YEAR(NOW()) AND statut='termine'")
        r = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as incidents_non_resolus FROM incidents WHERE resolu=0")
        i = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as trajets_en_cours FROM trajets WHERE statut='en_cours'")
        t = cursor.fetchone()
        return {
            "vehicules_actifs": v['vehicules_actifs'],
            "recettes_mois": r['recettes_mois'],
            "incidents_non_resolus": i['incidents_non_resolus'],
            "trajets_en_cours": t['trajets_en_cours']
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

# ============ GRAPHIQUE ============
@app.get("/dashboard/trajets-chart")
def get_trajets_chart():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT WEEKDAY(date_heure_depart) as jour, COUNT(*) as nb, COALESCE(SUM(recette),0) as recettes
            FROM trajets GROUP BY WEEKDAY(date_heure_depart)
        """)
        results = cursor.fetchall()
        jours = {0:"Lun",1:"Mar",2:"Mer",3:"Jeu",4:"Ven",5:"Sam",6:"Dim"}
        trajets = [0]*7
        recettes = [0]*7
        for r in results:
            trajets[r['jour']] = r['nb']
            recettes[r['jour']] = r['recettes']
        return {"labels": [jours[i] for i in range(7)], "trajets": trajets, "recettes": recettes}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

# ============ CHATBOT ============
class ChatRequest(BaseModel):
    question: str

def execute_sql(sql: str):
    sql_clean = re.sub(r'```sql\n?|```\n?', '', sql.strip())
    sql_clean = sql_clean.replace('\n', ' ').replace('\r', '')
    if not sql_clean.upper().startswith("SELECT"):
        return None, "SELECT uniquement"
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql_clean)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results, None
    except Exception as e:
        return None, str(e)

def traiter_jours_multiple(question: str):
    """Traitement spécifique pour les questions avec plusieurs jours"""
    q = question.lower()
    
    jours_map = {
        "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3,
        "vendredi": 4, "samedi": 5, "dimanche": 6
    }
    
    # Détecter les jours dans la question
    jours_trouves = []
    for jour, index in jours_map.items():
        if jour in q:
            jours_trouves.append((jour, index))
    
    # Si plusieurs jours sont demandés
    if len(jours_trouves) >= 2:
        jours_noms = [j[0] for j in jours_trouves]
        jours_index = [j[1] for j in jours_trouves]
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Cas avec incidents
        if "incident" in q:
            cursor.execute(f"""
                SELECT 
                    CASE WHEN WEEKDAY(t.date_heure_depart) = {jours_index[0]} THEN '{jours_noms[0].capitalize()}'
                         WHEN WEEKDAY(t.date_heure_depart) = {jours_index[1]} THEN '{jours_noms[1].capitalize()}'
                    END as jour,
                    COUNT(DISTINCT t.id) as nb_trajets,
                    COUNT(i.id) as nb_incidents
                FROM trajets t
                LEFT JOIN incidents i ON t.id = i.trajet_id
                WHERE WEEKDAY(t.date_heure_depart) IN ({jours_index[0]}, {jours_index[1]})
                GROUP BY jour
            """)
        else:
            # Cas simple : nombre de trajets
            cursor.execute(f"""
                SELECT 
                    CASE WHEN WEEKDAY(date_heure_depart) = {jours_index[0]} THEN '{jours_noms[0].capitalize()}'
                         WHEN WEEKDAY(date_heure_depart) = {jours_index[1]} THEN '{jours_noms[1].capitalize()}'
                    END as jour,
                    COUNT(*) as nb_trajets
                FROM trajets
                WHERE WEEKDAY(date_heure_depart) IN ({jours_index[0]}, {jours_index[1]})
                GROUP BY jour
            """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if results:
            if "incident" in q:
                natural = f"📊 Nombre de trajets et incidents les {jours_noms[0]} et {jours_noms[1]} :"
            else:
                natural = f"📊 Nombre de trajets les {jours_noms[0]} et {jours_noms[1]} :"
            return natural, results
    return None, None

# PROMPT SYSTÈME
SYSTEM_PROMPT = """
Tu es un expert SQL. Voici le SCHEMA EXACT:

trajets: id, date_heure_depart, recette, statut
chauffeurs: id, nom, prenom, statut
vehicules: id, immatriculation, marque, modele, statut
incidents: id, trajet_id, type_incident, resolu

VALEURS EXACTES:
- statut vehicules: 'actif', 'en_maintenance', 'hors_service'
- statut chauffeurs: 'actif', 'en_conge', 'suspendu'
- statut trajets: 'planifie', 'en_cours', 'termine', 'annule'

JOURS: lundi=0, mardi=1, mercredi=2, jeudi=3, vendredi=4, samedi=5, dimanche=6

EXEMPLES:
Question: "chiffre d'affaires du mois"
SQL: SELECT SUM(recette) FROM trajets WHERE MONTH(date_heure_depart)=MONTH(CURDATE()) AND statut='termine'

Question: "nombre de trajets le lundi"
SQL: SELECT COUNT(*) FROM trajets WHERE WEEKDAY(date_heure_depart)=0

Question: "quel chauffeur a le plus d'incidents"
SQL: SELECT c.nom, c.prenom, COUNT(i.id) as nb FROM chauffeurs c JOIN trajets t ON c.id=t.chauffeur_id JOIN incidents i ON t.id=i.trajet_id GROUP BY c.id ORDER BY nb DESC LIMIT 1

Réponds UNIQUEMENT au format JSON: {"sql": "requete", "natural": "reponse"}
"""

@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question
    q = question.lower()
    
    # ========== TRAITEMENT DIRECT PRIORITAIRE ==========
    
    # 1. Chiffre d'affaires
    if "chiffre d affaires" in q or "ca du mois" in q:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE MONTH(date_heure_depart)=MONTH(NOW()) AND YEAR(date_heure_depart)=YEAR(NOW()) AND statut='termine'")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return {
            "natural_response": f"💰 Chiffre d'affaires du mois : {row['total']:,.0f} FCFA",
            "sql": "SELECT SUM(recette) FROM trajets WHERE MONTH(date_heure_depart)=MONTH(NOW()) AND statut='termine'",
            "results": [{"total": row['total']}]
        }
    
    # 2. Véhicules en maintenance
    if "vehicules en maintenance" in q or "véhicules en maintenance" in q:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'en_maintenance'")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if rows:
            natural = "🔧 Véhicules en maintenance :"
        else:
            natural = "✅ Aucun véhicule en maintenance"
        return {
            "natural_response": natural,
            "sql": "SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'en_maintenance'",
            "results": rows
        }
    
    # 3. Plusieurs jours (LUNDI ET MARDI, etc.)
    if "lundi et mardi" in q or "mardi et lundi" in q:
        if "incident" in q:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    CASE WHEN WEEKDAY(t.date_heure_depart)=0 THEN 'Lundi' WHEN WEEKDAY(t.date_heure_depart)=1 THEN 'Mardi' END as jour,
                    COUNT(DISTINCT t.id) as nb_trajets,
                    COUNT(i.id) as nb_incidents
                FROM trajets t
                LEFT JOIN incidents i ON t.id = i.trajet_id
                WHERE WEEKDAY(t.date_heure_depart) IN (0,1)
                GROUP BY jour
            """)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return {
                "natural_response": "📊 Nombre de trajets et incidents le lundi et mardi :",
                "sql": "SELECT CASE WHEN WEEKDAY(t.date_heure_depart)=0 THEN 'Lundi' WHEN WEEKDAY(t.date_heure_depart)=1 THEN 'Mardi' END as jour, COUNT(DISTINCT t.id) as nb_trajets, COUNT(i.id) as nb_incidents FROM trajets t LEFT JOIN incidents i ON t.id=i.trajet_id WHERE WEEKDAY(t.date_heure_depart) IN (0,1) GROUP BY jour",
                "results": results
            }
        else:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    CASE WHEN WEEKDAY(date_heure_depart)=0 THEN 'Lundi' WHEN WEEKDAY(date_heure_depart)=1 THEN 'Mardi' END as jour,
                    COUNT(*) as nb_trajets
                FROM trajets
                WHERE WEEKDAY(date_heure_depart) IN (0,1)
                GROUP BY jour
            """)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return {
                "natural_response": "📊 Nombre de trajets le lundi et mardi :",
                "sql": "SELECT CASE WHEN WEEKDAY(date_heure_depart)=0 THEN 'Lundi' WHEN WEEKDAY(date_heure_depart)=1 THEN 'Mardi' END as jour, COUNT(*) as nb_trajets FROM trajets WHERE WEEKDAY(date_heure_depart) IN (0,1) GROUP BY jour",
                "results": results
            }
    
    # 4. Samedi et dimanche
    if "samedi et dimanche" in q or "dimanche et samedi" in q:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                CASE WHEN WEEKDAY(date_heure_depart)=5 THEN 'Samedi' WHEN WEEKDAY(date_heure_depart)=6 THEN 'Dimanche' END as jour,
                COUNT(*) as nb_trajets,
                COALESCE(SUM(recette),0) as total_recettes
            FROM trajets
            WHERE WEEKDAY(date_heure_depart) IN (5,6)
            GROUP BY jour
        """)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {
            "natural_response": "📊 Nombre de trajets et recettes le samedi et dimanche :",
            "sql": "SELECT CASE WHEN WEEKDAY(date_heure_depart)=5 THEN 'Samedi' WHEN WEEKDAY(date_heure_depart)=6 THEN 'Dimanche' END as jour, COUNT(*) as nb_trajets, SUM(recette) as total_recettes FROM trajets WHERE WEEKDAY(date_heure_depart) IN (5,6) GROUP BY jour",
            "results": results
        }
    
    # 5. Chauffeur avec le plus d'incidents
    if "plus d'incidents" in q or "chauffeur a le plus d'incidents" in q:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.nom, c.prenom, COUNT(i.id) as nb_incidents
            FROM chauffeurs c
            JOIN trajets t ON c.id = t.chauffeur_id
            JOIN incidents i ON t.id = i.trajet_id
            GROUP BY c.id
            ORDER BY nb_incidents DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return {
            "natural_response": f"🚨 Le chauffeur avec le plus d'incidents est {row['prenom']} {row['nom']} avec {row['nb_incidents']} incidents.",
            "sql": "SELECT c.nom, c.prenom, COUNT(i.id) as nb_incidents FROM chauffeurs c JOIN trajets t ON c.id=t.chauffeur_id JOIN incidents i ON t.id=i.trajet_id GROUP BY c.id ORDER BY nb_incidents DESC LIMIT 1",
            "results": [row]
        }
    
    # 6. Recettes et trajets par chauffeur
    if "recettes et trajets par chauffeur" in q:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, 
                   COALESCE(SUM(t.recette),0) as total_recettes,
                   COUNT(t.id) as nb_trajets
            FROM chauffeurs c
            LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine'
            GROUP BY c.id
            ORDER BY total_recettes DESC
        """)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {
            "natural_response": "💰 Recettes et trajets par chauffeur :",
            "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, COALESCE(SUM(t.recette),0) as total_recettes, COUNT(t.id) as nb_trajets FROM chauffeurs c LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC",
            "results": results
        }
    
    # 7. Liste des lignes
    if "liste des lignes" in q:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {
            "natural_response": "🚏 Liste des lignes :",
            "sql": "SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes",
            "results": results
        }
    
    # 8. Nombre de trajets par jour (simple)
    jours_simples = {"lundi":0, "mardi":1, "mercredi":2, "jeudi":3, "vendredi":4, "samedi":5, "dimanche":6}
    for jour, index in jours_simples.items():
        if jour in q and "nombre" in q and "trajet" in q and "et" not in q:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM trajets WHERE WEEKDAY(date_heure_depart) = %s", (index,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return {
                "natural_response": f"Il y a {row['total']} trajets le {jour}.",
                "sql": f"SELECT COUNT(*) FROM trajets WHERE WEEKDAY(date_heure_depart) = {index}",
                "results": [{"total": row['total']}]
            }
    
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
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, immatriculation, marque, modele, statut FROM vehicules")
    return cursor.fetchall()

@app.get("/chauffeurs")
def get_chauffeurs():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nom, prenom, telephone, statut FROM chauffeurs")
    return cursor.fetchall()

@app.get("/lignes")
def get_lignes():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes")
    return cursor.fetchall()

@app.get("/trajets")
def get_trajets(limit: int = 10):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.id, t.date_heure_depart, t.statut, t.recette, CONCAT(c.prenom, ' ', c.nom) as chauffeur
        FROM trajets t JOIN chauffeurs c ON t.chauffeur_id = c.id
        ORDER BY t.date_heure_depart DESC LIMIT %s
    """, (limit,))
    return cursor.fetchall()

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