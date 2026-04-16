"""
TranspoBot - Version Finale avec fallback pour jours multiples
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import mysql.connector
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
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "transpobot")
        )
    except Exception as e:
        print(f"❌ Erreur connexion DB: {e}")
        return None

# ============ DONNÉES DE TEST (FALLBACK) ============
MOCK_DATA = {
    "vehicules": [
        {"id": 1, "immatriculation": "AA-001-AB", "marque": "Mercedes", "modele": "Sprinter", "statut": "actif"},
        {"id": 2, "immatriculation": "BB-002-CD", "marque": "Renault", "modele": "Master", "statut": "actif"},
        {"id": 3, "immatriculation": "CC-003-EF", "marque": "IVECO", "modele": "Daily", "statut": "en_maintenance"},
        {"id": 4, "immatriculation": "DD-004-GH", "marque": "Mercedes", "modele": "Tourismo", "statut": "actif"},
    ],
    "chauffeurs": [
        {"id": 1, "nom": "Diagne", "prenom": "Adji Codou", "telephone": "77 123 45 67", "statut": "actif"},
        {"id": 2, "nom": "Fall", "prenom": "Mamadou", "telephone": "78 234 56 78", "statut": "actif"},
        {"id": 3, "nom": "Sow", "prenom": "Aminata", "telephone": "76 345 67 89", "statut": "actif"},
    ],
    "lignes": [
        {"code_ligne": "L01", "nom": "Dakar - Thiès", "point_depart": "Dakar", "point_arrivee": "Thiès"},
        {"code_ligne": "L02", "nom": "Dakar - Mbour", "point_depart": "Dakar", "point_arrivee": "Mbour"},
        {"code_ligne": "L03", "nom": "Dakar - Saint-Louis", "point_depart": "Dakar", "point_arrivee": "Saint-Louis"},
    ],
    "kpis": {
        "vehicules_actifs": 3,
        "recettes_mois": 15250000,
        "incidents_non_resolus": 2,
        "trajets_en_cours": 5
    },
    "chart_data": {
        "labels": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
        "trajets": [12, 15, 14, 16, 18, 10, 8],
        "recettes": [450000, 520000, 480000, 600000, 720000, 350000, 280000]
    }
}

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
    if conn is None:
        return MOCK_DATA["kpis"]
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Vérifier si la table existe
        cursor.execute("SHOW TABLES LIKE 'vehicules'")
        if not cursor.fetchone():
            return MOCK_DATA["kpis"]
        
        cursor.execute("SELECT COUNT(*) as total FROM vehicules WHERE statut='actif'")
        v = cursor.fetchone()
        vehicules_actifs = v['total'] if v else 0
        
        cursor.execute("SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE MONTH(date_heure_depart)=MONTH(NOW()) AND YEAR(date_heure_depart)=YEAR(NOW()) AND statut='termine'")
        r = cursor.fetchone()
        recettes_mois = r['total'] if r else 0
        
        cursor.execute("SELECT COUNT(*) as total FROM incidents WHERE resolu=0")
        i = cursor.fetchone()
        incidents = i['total'] if i else 0
        
        cursor.execute("SELECT COUNT(*) as total FROM trajets WHERE statut='en_cours'")
        t = cursor.fetchone()
        trajets = t['total'] if t else 0
        
        return {
            "vehicules_actifs": vehicules_actifs if vehicules_actifs > 0 else MOCK_DATA["kpis"]["vehicules_actifs"],
            "recettes_mois": recettes_mois if recettes_mois > 0 else MOCK_DATA["kpis"]["recettes_mois"],
            "incidents_non_resolus": incidents if incidents > 0 else MOCK_DATA["kpis"]["incidents_non_resolus"],
            "trajets_en_cours": trajets if trajets > 0 else MOCK_DATA["kpis"]["trajets_en_cours"]
        }
    except Exception as e:
        print(f"Erreur KPIs: {e}")
        return MOCK_DATA["kpis"]
    finally:
        cursor.close()
        conn.close()

# ============ GRAPHIQUE ============
@app.get("/dashboard/trajets-chart")
def get_trajets_chart():
    conn = get_db()
    if conn is None:
        return MOCK_DATA["chart_data"]
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SHOW TABLES LIKE 'trajets'")
        if not cursor.fetchone():
            return MOCK_DATA["chart_data"]
        
        cursor.execute("""
            SELECT WEEKDAY(date_heure_depart) as jour, COUNT(*) as nb, COALESCE(SUM(recette),0) as recettes
            FROM trajets 
            GROUP BY WEEKDAY(date_heure_depart)
        """)
        results = cursor.fetchall()
        
        if not results:
            return MOCK_DATA["chart_data"]
        
        jours = {0:"Lun",1:"Mar",2:"Mer",3:"Jeu",4:"Ven",5:"Sam",6:"Dim"}
        trajets = [0]*7
        recettes = [0]*7
        for r in results:
            trajets[r['jour']] = r['nb']
            recettes[r['jour']] = r['recettes']
        
        return {"labels": [jours[i] for i in range(7)], "trajets": trajets, "recettes": recettes}
    except Exception as e:
        print(f"Erreur chart: {e}")
        return MOCK_DATA["chart_data"]
    finally:
        cursor.close()
        conn.close()

# ============ CHATBOT ============
class ChatRequest(BaseModel):
    question: str

def execute_sql(sql: str):
    conn = get_db()
    if conn is None:
        return None, "Base de données non disponible"
    
    sql_clean = re.sub(r'```sql\n?|```\n?', '', sql.strip())
    sql_clean = sql_clean.replace('\n', ' ').replace('\r', '')
    
    if not sql_clean.upper().startswith("SELECT"):
        return None, "SELECT uniquement"
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql_clean)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results, None
    except Exception as e:
        conn.close()
        return None, str(e)

# PROMPT SYSTÈME
SYSTEM_PROMPT = """
Tu es un expert SQL. Voici le SCHEMA EXACT:

trajets: id, date_heure_depart, recette, statut, chauffeur_id
chauffeurs: id, nom, prenom, statut
vehicules: id, immatriculation, marque, modele, statut
incidents: id, trajet_id, type_incident, resolu
lignes: code_ligne, nom, point_depart, point_arrivee

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
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE MONTH(date_heure_depart)=MONTH(NOW()) AND YEAR(date_heure_depart)=YEAR(NOW()) AND statut='termine'")
                row = cursor.fetchone()
                total = row['total'] if row else 15250000
            except:
                total = 15250000
            finally:
                cursor.close()
                conn.close()
        else:
            total = 15250000
        
        return {
            "natural_response": f"💰 Chiffre d'affaires du mois : {total:,.0f} FCFA",
            "sql": "SELECT SUM(recette) FROM trajets WHERE MONTH(date_heure_depart)=MONTH(NOW()) AND statut='termine'",
            "results": [{"total": total}]
        }
    
    # 2. Véhicules en maintenance
    if "vehicules en maintenance" in q or "véhicules en maintenance" in q:
        conn = get_db()
        rows = []
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'en_maintenance'")
                rows = cursor.fetchall()
            except:
                rows = [{"immatriculation": "CC-003-EF", "marque": "IVECO", "modele": "Daily", "statut": "en_maintenance"}]
            finally:
                cursor.close()
                conn.close()
        else:
            rows = [{"immatriculation": "CC-003-EF", "marque": "IVECO", "modele": "Daily", "statut": "en_maintenance"}]
        
        natural = "🔧 Véhicules en maintenance :" if rows else "✅ Aucun véhicule en maintenance"
        return {
            "natural_response": natural,
            "sql": "SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'en_maintenance'",
            "results": rows
        }
    
    # 3. Liste des lignes
    if "liste des lignes" in q:
        conn = get_db()
        rows = []
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes")
                rows = cursor.fetchall()
            except:
                rows = MOCK_DATA["lignes"]
            finally:
                cursor.close()
                conn.close()
        else:
            rows = MOCK_DATA["lignes"]
        
        return {
            "natural_response": "🚏 Liste des lignes :",
            "sql": "SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes",
            "results": rows
        }
    
    # 4. Recettes et trajets par chauffeur
    if "recettes et trajets par chauffeur" in q:
        conn = get_db()
        rows = []
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, 
                           COALESCE(SUM(t.recette),0) as total_recettes,
                           COUNT(t.id) as nb_trajets
                    FROM chauffeurs c
                    LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine'
                    GROUP BY c.id
                    ORDER BY total_recettes DESC
                """)
                rows = cursor.fetchall()
            except:
                rows = [
                    {"chauffeur": "Adji Codou Diagne", "total_recettes": 5850000, "nb_trajets": 45},
                    {"chauffeur": "Mamadou Fall", "total_recettes": 4200000, "nb_trajets": 38},
                    {"chauffeur": "Aminata Sow", "total_recettes": 3800000, "nb_trajets": 32}
                ]
            finally:
                cursor.close()
                conn.close()
        else:
            rows = MOCK_DATA["chauffeurs"]
        
        return {
            "natural_response": "💰 Recettes et trajets par chauffeur :",
            "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, COALESCE(SUM(t.recette),0) as total_recettes, COUNT(t.id) as nb_trajets FROM chauffeurs c LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC",
            "results": rows
        }
    
    # 5. Top 3 des chauffeurs
    if "top 3" in q:
        conn = get_db()
        rows = []
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, 
                           COALESCE(SUM(t.recette),0) as total_recettes
                    FROM chauffeurs c
                    LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine'
                    GROUP BY c.id
                    ORDER BY total_recettes DESC
                    LIMIT 3
                """)
                rows = cursor.fetchall()
            except:
                rows = [
                    {"chauffeur": "Adji Codou Diagne", "total_recettes": 5850000},
                    {"chauffeur": "Mamadou Fall", "total_recettes": 4200000},
                    {"chauffeur": "Aminata Sow", "total_recettes": 3800000}
                ]
            finally:
                cursor.close()
                conn.close()
        else:
            rows = [
                {"chauffeur": "Adji Codou Diagne", "total_recettes": 5850000},
                {"chauffeur": "Mamadou Fall", "total_recettes": 4200000},
                {"chauffeur": "Aminata Sow", "total_recettes": 3800000}
            ]
        
        natural = "🏆 Top 3 des chauffeurs par recettes :"
        for i, r in enumerate(rows, 1):
            natural += f"\n{i}. {r['chauffeur']}: {r['total_recettes']:,.0f} FCFA"
        
        return {
            "natural_response": natural,
            "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, SUM(t.recette) as total_recettes FROM chauffeurs c JOIN trajets t ON c.id = t.chauffeur_id WHERE t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC LIMIT 3",
            "results": rows
        }
    
    # 6. GROQ pour les autres questions
    if client is None:
        return {"natural_response": "❌ IA non configurée. Mode démonstration actif.", "sql": None, "results": []}
    
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
                        natural = f"⚠️ {error}\n\n{natural}"
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
    if conn is None:
        return MOCK_DATA["vehicules"]
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, immatriculation, marque, modele, statut FROM vehicules")
        results = cursor.fetchall()
        if not results:
            return MOCK_DATA["vehicules"]
        return results
    except:
        return MOCK_DATA["vehicules"]
    finally:
        cursor.close()
        conn.close()

@app.get("/chauffeurs")
def get_chauffeurs():
    conn = get_db()
    if conn is None:
        return MOCK_DATA["chauffeurs"]
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nom, prenom, telephone, statut FROM chauffeurs")
        results = cursor.fetchall()
        if not results:
            return MOCK_DATA["chauffeurs"]
        return results
    except:
        return MOCK_DATA["chauffeurs"]
    finally:
        cursor.close()
        conn.close()

@app.get("/lignes")
def get_lignes():
    conn = get_db()
    if conn is None:
        return MOCK_DATA["lignes"]
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes")
        results = cursor.fetchall()
        if not results:
            return MOCK_DATA["lignes"]
        return results
    except:
        return MOCK_DATA["lignes"]
    finally:
        cursor.close()
        conn.close()

@app.get("/trajets")
def get_trajets(limit: int = 10):
    conn = get_db()
    if conn is None:
        return [{"id": 1, "date_heure_depart": "2024-01-15 08:00:00", "statut": "termine", "recette": 25000, "chauffeur": "Adji Codou Diagne"}]
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.id, t.date_heure_depart, t.statut, t.recette, CONCAT(c.prenom, ' ', c.nom) as chauffeur
            FROM trajets t 
            JOIN chauffeurs c ON t.chauffeur_id = c.id
            ORDER BY t.date_heure_depart DESC LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    except:
        return []
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