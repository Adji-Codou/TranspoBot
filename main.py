"""
TranspoBot - Version Finale pour PostgreSQL (Render)
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
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT COUNT(*) as vehicules_actifs FROM vehicules WHERE statut='actif'")
        v = cursor.fetchone()
        cursor.execute("SELECT COALESCE(SUM(recette),0) as recettes_mois FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM NOW()) AND EXTRACT(YEAR FROM date_heure_depart)=EXTRACT(YEAR FROM NOW()) AND statut='termine'")
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
        return {"error": str(e), "vehicules_actifs": 0, "recettes_mois": 0, "incidents_non_resolus": 0, "trajets_en_cours": 0}
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
            SELECT EXTRACT(DOW FROM date_heure_depart) as jour, COUNT(*) as nb, COALESCE(SUM(recette),0) as recettes
            FROM trajets GROUP BY EXTRACT(DOW FROM date_heure_depart)
        """)
        results = cursor.fetchall()
        jours = {0:"Lun",1:"Mar",2:"Mer",3:"Jeu",4:"Ven",5:"Sam",6:"Dim"}
        trajets = [0]*7
        recettes = [0]*7
        for r in results:
            jour_index = int(r['jour'])
            trajets[jour_index] = r['nb']
            recettes[jour_index] = float(r['recettes'])
        return {"labels": [jours[i] for i in range(7)], "trajets": trajets, "recettes": recettes}
    except Exception as e:
        return {"error": str(e), "labels": ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"], "trajets": [0]*7, "recettes": [0]*7}
    finally:
        cursor.close()
        conn.close()

# ============ CHATBOT ============
class ChatRequest(BaseModel):
    question: str

def execute_sql(sql: str):
    sql_clean = re.sub(r'```sql\n?|```\n?', '', sql.strip())
    sql_clean = sql_clean.replace('\n', ' ').replace('\r', '')
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) AND EXTRACT(YEAR FROM date_heure_depart)=EXTRACT(YEAR FROM CURRENT_TIMESTAMP) AND statut='termine'")
            row = cursor.fetchone()
            total = row['total'] if row else 0
        except:
            total = 0
        finally:
            cursor.close()
            conn.close()
        return {
            "natural_response": f"💰 Chiffre d'affaires du mois : {total:,.0f} FCFA",
            "sql": "SELECT SUM(recette) FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_DATE) AND statut='termine'",
            "results": [{"total": total}]
        }
    
    # 2. TOP 3 des chauffeurs par recette
    if "top 3" in q or "top trois" in q:
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
                LIMIT 3
            """)
            results = cursor.fetchall()
        except Exception as e:
            results = []
        finally:
            cursor.close()
            conn.close()
        
        if results:
            natural = "🏆 Top 3 des chauffeurs par recettes :\n"
            for i, r in enumerate(results, 1):
                natural += f"{i}. {r['chauffeur']}: {r['total_recettes']:,.0f} FCFA ({r['nb_trajets']} trajets)\n"
        else:
            natural = "🏆 Aucune donnée disponible pour le top 3 des chauffeurs."
        
        return {
            "natural_response": natural,
            "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, SUM(t.recette) as total_recettes FROM chauffeurs c JOIN trajets t ON c.id = t.chauffeur_id WHERE t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC LIMIT 3",
            "results": results
        }
    
    # 3. Véhicules en maintenance
    if "vehicules en maintenance" in q or "véhicules en maintenance" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'en_maintenance'")
            rows = cursor.fetchall()
        except:
            rows = []
        finally:
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
    
    # 4. Recettes et trajets par chauffeur
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
        except:
            results = []
        finally:
            cursor.close()
            conn.close()
        
        return {
            "natural_response": "💰 Recettes et trajets par chauffeur :",
            "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, COALESCE(SUM(t.recette),0) as total_recettes, COUNT(t.id) as nb_trajets FROM chauffeurs c LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC",
            "results": results
        }
    
    # 5. Liste des lignes
    if "liste des lignes" in q:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes")
            results = cursor.fetchall()
        except:
            results = []
        finally:
            cursor.close()
            conn.close()
        
        return {
            "natural_response": "🚏 Liste des lignes :",
            "sql": "SELECT code_ligne, nom, point_depart, point_arrivee FROM lignes",
            "results": results
        }
    
    # 6. Chauffeur avec le plus d'incidents
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
        except:
            row = None
        finally:
            cursor.close()
            conn.close()
        
        if row:
            natural = f"🚨 Le chauffeur avec le plus d'incidents est {row['prenom']} {row['nom']} avec {row['nb_incidents']} incidents."
        else:
            natural = "🚨 Aucun incident enregistré."
        
        return {
            "natural_response": natural,
            "sql": "SELECT c.nom, c.prenom, COUNT(i.id) as nb_incidents FROM chauffeurs c JOIN trajets t ON c.id=t.chauffeur_id JOIN incidents i ON t.id=i.trajet_id GROUP BY c.id ORDER BY nb_incidents DESC LIMIT 1",
            "results": [row] if row else []
        }
    
    # ========== GROQ POUR LES AUTRES QUESTIONS ==========
    if client is None:
        return {"natural_response": "❌ IA non configurée. Mode démo actif.", "sql": None, "results": []}
    
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, immatriculation, marque, modele, statut FROM vehicules")
        return cursor.fetchall()
    except:
        return []
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
    except:
        return []
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
    except:
        return []
    finally:
        cursor.close()
        conn.close()

@app.get("/trajets")
def get_trajets(limit: int = 10):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
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