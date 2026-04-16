"""
TranspoBot - Version PostgreSQL avec IA intelligente (GROQ)
Fonctionnalités :
- IA qui répond intelligemment (y compris aux salutations)
- Traitement des questions multi-jours
- Fallback avec GROQ pour les questions complexes
- Compatible Vercel + Aiven PostgreSQL
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
        return {"labels": ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"], "trajets": [0]*7, "recettes": [0]*7}
    finally:
        cursor.close()
        conn.close()


# ============ CHATBOT INTELLIGENT ==========

class ChatRequest(BaseModel):
    question: str


def execute_sql(sql: str):
    sql_clean = re.sub(r'```sql\n?|```\n?', '', sql.strip())
    sql_clean = sql_clean.replace('\n', ' ').replace('\r', ' ')
    sql_clean = ' '.join(sql_clean.split())
    
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Cas avec incidents
        if "incident" in q:
            cursor.execute(f"""
                SELECT 
                    CASE 
                        WHEN EXTRACT(DOW FROM t.date_heure_depart) = {jours_index[0]} THEN '{jours_noms[0].capitalize()}'
                        WHEN EXTRACT(DOW FROM t.date_heure_depart) = {jours_index[1]} THEN '{jours_noms[1].capitalize()}'
                    END as jour,
                    COUNT(DISTINCT t.id) as nb_trajets,
                    COUNT(i.id) as nb_incidents
                FROM trajets t
                LEFT JOIN incidents i ON t.id = i.trajet_id
                WHERE EXTRACT(DOW FROM t.date_heure_depart) IN ({jours_index[0]}, {jours_index[1]})
                GROUP BY jour
            """)
        else:
            # Cas simple : nombre de trajets
            cursor.execute(f"""
                SELECT 
                    CASE 
                        WHEN EXTRACT(DOW FROM date_heure_depart) = {jours_index[0]} THEN '{jours_noms[0].capitalize()}'
                        WHEN EXTRACT(DOW FROM date_heure_depart) = {jours_index[1]} THEN '{jours_noms[1].capitalize()}'
                    END as jour,
                    COUNT(*) as nb_trajets,
                    COALESCE(SUM(recette),0) as total_recettes
                FROM trajets
                WHERE EXTRACT(DOW FROM date_heure_depart) IN ({jours_index[0]}, {jours_index[1]})
                GROUP BY jour
            """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if results:
            if "incident" in q:
                natural = f"📊 Nombre de trajets et incidents les {jours_noms[0]} et {jours_noms[1]} :"
            else:
                natural = f"📊 Nombre de trajets et recettes les {jours_noms[0]} et {jours_noms[1]} :"
            return natural, results
    return None, None


# PROMPT SYSTÈME (version intelligente)
SYSTEM_PROMPT = """Tu es un assistant IA convivial et intelligent pour la gestion de transport.

RÈGLES IMPORTANTES:
1. Si l'utilisateur te dit "bonjour", "salut", "coucou", répond de façon chaleureuse et propose ton aide.
2. Si l'utilisateur te remercie, répond avec politesse.
3. Pour les questions sur les données, génère la requête SQL PostgreSQL.
4. Sois naturel, pas trop technique. Utilise des émojis.

SCHEMA BASE DE DONNÉES:
chauffeurs: id, nom, prenom, telephone, statut
vehicules: id, immatriculation, marque, modele, statut, kilometrage
trajets: id, vehicule_id, chauffeur_id, ligne_id, date_heure_depart, nb_passagers, recette, statut
incidents: id, trajet_id, type_incident, description, date_incident, gravite, resolu
lignes: id, code_ligne, nom, point_depart, point_arrivee, distance_km

VALEURS:
- statut vehicules: 'actif', 'en_maintenance', 'hors_service'
- statut chauffeurs: 'actif', 'en_conge', 'suspendu'
- statut trajets: 'planifie', 'en_cours', 'termine', 'annule'

FONCTIONS:
- EXTRACT(DOW FROM date) pour jour (lundi=0, mardi=1, ..., dimanche=6)
- EXTRACT(MONTH FROM date) pour mois
- EXTRACT(YEAR FROM date) pour année
- CURRENT_TIMESTAMP pour date actuelle

EXEMPLES DE RÉPONSES:

Question: "bonjour"
{"sql": null, "natural": "👋 Bonjour ! Comment puis-je vous aider aujourd'hui ? Je peux vous donner des informations sur vos véhicules, chauffeurs, trajets, recettes ou incidents."}

Question: "merci"
{"sql": null, "natural": "😊 Avec plaisir ! N'hésitez pas si vous avez d'autres questions sur votre flotte de transport."}

Question: "chiffre d'affaires du mois"
{"sql": "SELECT COALESCE(SUM(recette),0) as total FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) AND statut='termine'", "natural": "💰 Voici le chiffre d'affaires du mois :"}

Question: "Véhicules en maintenance"
{"sql": "SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut='en_maintenance'", "natural": "🔧 Voici les véhicules actuellement en maintenance :"}

Réponds UNIQUEMENT au format JSON. Pour les salutations et remerciements, mets "sql": null.
"""


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question
    q = question.lower().strip()
    
    print(f"📨 Question reçue: {question}")
    
    # ========== TRAITEMENT DES JOURS MULTIPLES ==========
    natural_multi, results_multi = traiter_jours_multiple(question)
    if natural_multi and results_multi:
        return {
            "natural_response": natural_multi,
            "sql": None,
            "results": results_multi
        }
    
    # ========== TRAITEMENT DIRECT PRIORITAIRE ==========
    
    # 1. Chiffre d'affaires
    if "chiffre d affaires" in q or "ca du mois" in q or "chiffre d'affaires" in q:
        print("🔍 Traitement: Chiffre d'affaires")
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
                "sql": "SELECT COALESCE(SUM(recette),0) FROM trajets WHERE EXTRACT(MONTH FROM date_heure_depart)=EXTRACT(MONTH FROM CURRENT_TIMESTAMP) AND statut='termine'",
                "results": [{"total": row['total']}]
            }
        finally:
            cursor.close()
            conn.close()
    
    # 2. Véhicules en maintenance
    if "vehicules en maintenance" in q or "véhicules en maintenance" in q or "maintenance" in q:
        print("🔍 Traitement: Véhicules en maintenance")
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT immatriculation, marque, modele, statut, kilometrage FROM vehicules WHERE statut = 'en_maintenance'")
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
    
    # 3. Liste des chauffeurs
    if "liste des chauffeurs" in q or ("chauffeurs" in q and "liste" in q):
        print("🔍 Traitement: Liste des chauffeurs")
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT nom, prenom, telephone, statut FROM chauffeurs")
            rows = cursor.fetchall()
            return {
                "natural_response": "👨‍✈️ Voici la liste des chauffeurs :",
                "sql": "SELECT nom, prenom, telephone, statut FROM chauffeurs",
                "results": rows
            }
        finally:
            cursor.close()
            conn.close()
    
    # 4. Véhicules actifs
    if "vehicules actifs" in q or "véhicules actifs" in q:
        print("🔍 Traitement: Véhicules actifs")
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'actif'")
            rows = cursor.fetchall()
            return {
                "natural_response": "🚍 Véhicules actifs actuellement :",
                "sql": "SELECT immatriculation, marque, modele, statut FROM vehicules WHERE statut = 'actif'",
                "results": rows
            }
        finally:
            cursor.close()
            conn.close()
    
    # 5. Liste des lignes
    if "liste des lignes" in q or ("lignes" in q and "liste" in q):
        print("🔍 Traitement: Liste des lignes")
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee, distance_km FROM lignes")
            rows = cursor.fetchall()
            return {
                "natural_response": "🚏 Voici les lignes de transport :",
                "sql": "SELECT code_ligne, nom, point_depart, point_arrivee, distance_km FROM lignes",
                "results": rows
            }
        finally:
            cursor.close()
            conn.close()
    
    # 6. Chauffeur avec le plus d'incidents
    if "plus d'incidents" in q or "chauffeur a le plus d'incidents" in q:
        print("🔍 Traitement: Chauffeur plus d'incidents")
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
            return {"natural_response": "Aucun incident trouvé dans la base.", "sql": None, "results": []}
        finally:
            cursor.close()
            conn.close()
    
    # 7. Recettes et trajets par chauffeur
    if "recettes et trajets par chauffeur" in q:
        print("🔍 Traitement: Recettes par chauffeur")
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
                "natural_response": "💰 Voici les recettes et trajets par chauffeur :",
                "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, COALESCE(SUM(t.recette),0) as total_recettes, COUNT(t.id) as nb_trajets FROM chauffeurs c LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC",
                "results": results
            }
        finally:
            cursor.close()
            conn.close()
    
    # 8. Top 3 des chauffeurs par recette
    if "top 3" in q and "chauffeur" in q and "recette" in q:
        print("🔍 Traitement: Top 3 chauffeurs")
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, 
                       COALESCE(SUM(t.recette),0) as total_recettes
                FROM chauffeurs c
                LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine'
                GROUP BY c.id, c.prenom, c.nom
                ORDER BY total_recettes DESC
                LIMIT 3
            """)
            results = cursor.fetchall()
            return {
                "natural_response": "🏆 Top 3 des chauffeurs par recette :",
                "sql": "SELECT CONCAT(c.prenom, ' ', c.nom) as chauffeur, COALESCE(SUM(t.recette),0) as total_recettes FROM chauffeurs c LEFT JOIN trajets t ON c.id = t.chauffeur_id AND t.statut='termine' GROUP BY c.id ORDER BY total_recettes DESC LIMIT 3",
                "results": results
            }
        finally:
            cursor.close()
            conn.close()
    
    # 9. Nombre de trajets par jour (simple)
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
    
    # ========== GROQ POUR LES AUTRES QUESTIONS (IA INTELLIGENTE) ==========
    if client is None:
        return {"natural_response": "❌ L'IA n'est pas configurée. Veuillez ajouter GROQ_API_KEY dans les variables d'environnement.", "sql": None, "results": []}
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=500
        )
        response_text = response.choices[0].message.content
        print(f"🤖 Groq répond: {response_text[:200]}")
        
        # Extraction du JSON
        match = re.search(r'\{[^{}]*"sql"[^{}]*"natural"[^{}]*\}', response_text, re.DOTALL)
        
        if match:
            try:
                json_str = match.group()
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                data = json.loads(json_str)
                sql = data.get("sql", "").strip()
                natural = data.get("natural", "").strip()
                
                # Si c'est une réponse sans SQL (salutation, remerciement)
                if sql is None or sql == "" or sql == "null":
                    return {"natural_response": natural, "sql": None, "results": []}
                
                # Vérifier que c'est une vraie requête
                if sql and "SELECT" in sql.upper():
                    results, error = execute_sql(sql)
                    if error:
                        return {"natural_response": f"❌ Désolé, une erreur s'est produite : {error}", "sql": sql, "results": []}
                    return {"natural_response": natural if natural else "Voici les résultats :", "sql": sql, "results": results}
                else:
                    return {"natural_response": natural, "sql": None, "results": []}
            except json.JSONDecodeError as e:
                print(f"Erreur JSON: {e}")
                pass
        
        return {"natural_response": response_text[:500], "sql": None, "results": []}
        
    except Exception as e:
        print(f"❌ Erreur GROQ: {e}")
        return {"natural_response": f"❌ Désolé, je n'ai pas pu traiter votre demande. Erreur: {str(e)}", "sql": None, "results": []}


# ============ ENDPOINTS ============

@app.get("/vehicules")
def get_vehicules():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id, immatriculation, marque, modele, statut, kilometrage FROM vehicules")
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
        cursor.execute("SELECT code_ligne, nom, point_depart, point_arrivee, distance_km FROM lignes")
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
            SELECT t.id, t.date_heure_depart, t.statut, t.recette, t.nb_passagers,
                   CONCAT(c.prenom, ' ', c.nom) as chauffeur,
                   v.immatriculation as vehicule
            FROM trajets t 
            LEFT JOIN chauffeurs c ON t.chauffeur_id = c.id
            LEFT JOIN vehicules v ON t.vehicule_id = v.id
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