#from pyexpat.errors import messages
from django.contrib import messages
from django.shortcuts import render
import openpyxl
from django.http import HttpResponse, JsonResponse
import requests
from .models import Agent, Message_Ai, Message_agent_ai
from .responses_ai import generate_response, generate_ai_response

from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import connection, transaction,utils

import re
#import datetime
from django.views.decorators.csrf import csrf_exempt

from django.db import router
import logging
# Configuration d'un logger interopérable
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from django.shortcuts import render

from .models import DbSource
from .forms import DataSourceForm
#TEST SWEET ALERT
from django.contrib import messages

from django.http import JsonResponse

import pymysql
import psycopg2


# En mode TEST
def ask_ai_agent(request):
    # Données à envoyer à l'agent IA dans n8n
    payload = {
        "user_input": "Comment optimiser mon code ?",
        "user_id": request.user.id
    }
    
    # URL du Webhook n8n (Production ou Test)
    n8n_url = "http://host.docker.internal"
    
    try:
        response = requests.post(n8n_url, json=payload)
        response.raise_for_status()
        
        # Récupération de l'output de l'agent IA
        ai_data = response.json()
        
        return JsonResponse({"status": "success", "ai_response": ai_data})
    
    except requests.exceptions.RequestException as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_POST
def test_connect_bdd(request):
    """Teste la connexion d'une source à partir des données transmises par le formulaire."""
    # Récupération des données POST
    db_type = request.POST.get('db_type')
    host = request.POST.get('host')
    database_name = request.POST.get('database_name')
    port = request.POST.get('port')
    username = request.POST.get('username')
    password = request.POST.get('password')

    # Instanciation temporaire en mémoire (sans save())
    temp_source = DbSource(
        db_type=db_type,
        host=host,
        database_name=database_name,
        port=port,
        username=username,
        password=password
    )

    try:
        is_valid, error_msg = temp_source.check_connection()
        if is_valid:
            return JsonResponse({
                "success": True,
                "message": "Connexion réussie !"
            })
        else:
            return JsonResponse({
                "success": False,
                "message": f"Échec : {error_msg}"
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Erreur système : {str(e)}"
        }, status=500)

def de_connect_bdd(request, pk):
    source = get_object_or_404(DbSource, pk=pk)
    source.disconnect()
    print(f"DEBUG: source.status après déconnexion -> {source.status}")
    print(f"DEBUG: source.is_active après déconnexion -> {source.is_active}")
    return JsonResponse({
        "status": "success",
        "source_id": source.id
    })

def is_sql_query(message):
    #sql_keywords = ["select", "insert", "update", "delete"]
    sql_keywords = ["select"]
    msg = message.lower().strip()
    return any(msg.startswith(word) for word in sql_keywords)

""" def validate_query(sql):
    sql = sql.strip().lower()
    if not sql.startswith("select"):
        raise ValueError("Seules les requêtes SELECT sont autorisées.")
    return sql """

def open_connection(source):
    if source.db_type == "mysql":
        return pymysql.connect(
            host=source.host,
            user=source.username,
            password=source.password,
            database=source.database_name,
            port=source.port,
            cursorclass=pymysql.cursors.Cursor
        )

    elif source.db_type == "postgres":
        return psycopg2.connect(
            host=source.host,
            user=source.username,
            password=source.password,
            dbname=source.database_name,
            port=source.port
        )

    else:
        raise ValueError("Type de base non supporté")

""" def run_query(source, sql):
      # 1. Nettoyage initial et retrait du point-virgule final
    sql = sql.strip().rstrip(";")
    sql_clean_lower = sql.lower()

    # =======================================================
    # 🚨 BLINDAGE DE SÉCURITÉ AUTONOME (Scanner de Tokens)
    # =======================================================
    #mots_extraits = set(re.findall(r"\w+", sql_clean_lower))
    mots_extraits = set(re.findall(r'\b[a-z_]+\b', sql_clean_lower))
    commandes_interdites = {
        "delete", "update", "drop", "truncate", "alter", 
        "insert", "create", "grant", "replace"
    }

    sql_pour_premier_mot = sql_clean_lower.lstrip("() ")
    premier_mot = sql_pour_premier_mot.split()[0] if sql_pour_premier_mot.split() else ""

    if (
        ";" in sql
        or premier_mot != "select"
        or mots_extraits.intersection(commandes_interdites)
    ):
        raise PermissionError(
            "Action non autorisée : Cette méthode accepte exclusivement une unique instruction SELECT."
        )

    # =======================================================
    # 📊 BRIDAGE AUTOMATIQUE DU VOLUME (Interopérabilité LIMIT)
    # =======================================================
    # Détection du type de moteur à partir de l'objet source (ex: source.vendor ou source.db_type)
    # On suppose que l'objet 'source' possède un attribut indiquant son moteur de base de données.
    moteur = getattr(source, "db_type", "default").lower()

    if "limit" not in sql_clean_lower and "top " not in sql_clean_lower and "fetch " not in sql_clean_lower:
        if "oracle" in moteur:
            sql += " FETCH FIRST 50 ROWS ONLY"
        elif "mssql" in moteur or "sqlserver" in moteur:
            # Pour SQL Server, l'ajout d'un TOP requiert une modification en début de chaîne
            sql = re.sub(r"^\s*select\s+", "SELECT TOP 50 ", sql, flags=re.IGNORECASE)
        else:
            # Standard pour PostgreSQL, MySQL, SQLite
            sql += " LIMIT 50"

    # =======================================================
    # ⚡ EXÉCUTION ET SÉRIALISATION UNIVERSELLE
    # =======================================================
    logger.info(f"Exécution SQL sur la source '{source.name}' ({moteur})")
    
    # open_connection doit être capable de lire la structure de votre objet source
    with open_connection(source) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            
            # Gestion universelle de la description des colonnes
            if cursor.description:
                columns = [col[0] for col in cursor.description]
            else:
                return []
                
            rows = cursor.fetchall()

    cleaned_rows = []

    # Sérialisation robuste : décode les octets (bytes) et gère les formats selon les moteurs
    for row in rows:
        cleaned_row = []
        for value in row:
            if isinstance(value, bytes):
                cleaned_row.append(value.decode("utf-8", errors="ignore"))
            else:
                cleaned_row.append(value)
        cleaned_rows.append(dict(zip(columns, cleaned_row)))

    return cleaned_rows """
#n'est pas operable
def run_query(source, sql):
    # 1. Nettoyage initial et retrait du point-virgule final
    sql = sql.strip().rstrip(";")

    # =======================================================
    # 🚨 BLINDAGE DE SÉCURITÉ AUTONOME (Scanner de Tokens)
    # =======================================================
    sql_clean_lower = sql.lower()

    # Extraction de chaque mot de manière isolée
    mots_extraits = set(re.findall(r"\w+", sql_clean_lower))

    # Liste noire absolue des commandes d'altération
    commandes_interdites = {
        "delete", "update", "drop", "truncate", "alter", 
        "insert", "create", "grant"
    }

    # 🟢 CORRECTION SYNTAXE UNION : On nettoie les parenthèses à gauche avant d'isoler le premier mot
    sql_pour_premier_mot = sql_clean_lower.lstrip("() ")
    premier_mot = sql_pour_premier_mot.split()[0] if sql_pour_premier_mot.split() else ""

    # Détection des points-virgules internes (tentative d'empilage)
    if (
        ";" in sql
        or premier_mot != "select"
        or mots_extraits.intersection(commandes_interdites)
    ):
        raise PermissionError(
            "Action non autorisée : Cette méthode accepte exclusivement une unique instruction SELECT."
        )

    # =======================================================
    # 📊 BRIDAGE AUTOMATIQUE DU VOLUME (LIMIT)
    # =======================================================
    # On applique le LIMIT uniquement s'il n'est pas déjà défini dans la requête globale
    if "limit" not in sql_clean_lower:
        sql += " LIMIT 50"

    # =======================================================
    # ⚡ EXÉCUTION ET SÉRIALISATION OPTIMISÉE
    # =======================================================
    with open_connection(source) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

    cleaned_rows = []

    # Optimisation de la boucle de conversion (Performances accrues)
    for row in rows:
        cleaned_row = []
        for value in row:
            if isinstance(value, bytes):
                cleaned_row.append(value.decode("utf-8", errors="ignore"))
            else:
                cleaned_row.append(value)
        cleaned_rows.append(dict(zip(columns, cleaned_row)))

    return cleaned_rows 
    

# BON MAI VEUT OPTIMISER

def activ_source(request, db_source_id):
    # 1. Récupération sécurisée de la source cible
    db_source = get_object_or_404(DbSource, id=db_source_id)
    
    # 2. Test de connexion physique
    is_valid, error_msg = db_source.check_connection()
    
    if not is_valid:
        # En cas d'échec : on n'active pas l'élément mais on marque son statut en erreur
        db_source.activate(status="error")
        
        # Envoi d'un message d'erreur (sera affiché par alertError)
        messages.error(request, f"Connexion refusée à '{db_source.name}' : {error_msg}")
        
        return JsonResponse({
            "success": False,
            "error": error_msg,
            "source_id": db_source.id,
            "source_name": db_source.name
        }, status=400) # Code 400 pour indiquer une mauvaise configuration / erreur

    # 3. En cas de succès : On active normalement
    db_source.activate(status="connected")
    
    # Message de succès pour l'utilisateur
    messages.success(request, f"La source '{db_source.name}' a été vérifiée et activée avec succès.")

    return JsonResponse({
        "success": True,
        "source_id": db_source.id,
        "source_name": db_source.name
    })


def add_source(request):
    form = DataSourceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Option 1 (Recommandée) : On récupère l'objet créé par le formulaire
        nouvelle_source = form.save()
        
        # On accède directement à l'attribut .name de l'instance du modèle
        messages.success(request, f'La Source "{nouvelle_source.name}" a été créée avec succès !')
        return redirect('parametre')
        
    # Si le formulaire n'est pas valide ou en méthode GET
    return render(request, 'chat/parametre.html', {'form': form})

""" def edit_source(request, pk):
    source = get_object_or_404(DbSource, pk=pk)
    form = DataSourceForm(request.POST or None, instance=source)
    if form.is_valid():
        form.save()
        messages.success(request, f'La source "{source.name}" a été modifiée avec succès !')
        return redirect('parametre') # Redirige vers vos paramètres
        
    # Si la requête vient du script JS (AJAX), on peut renvoyer un template partiel ou le même
    return render(request, "chat/add_source.html", {"form": form}) """



def edit_source(request, pk):
    # Récupération de la source existante via la clé primaire (pk)
    source = get_object_or_404(DbSource, pk=pk)

    if request.method == "POST":
        # Extraction des données du formulaire (identiques aux attributs 'name' du HTML)
        name = request.POST.get("name")
        db_type = request.POST.get("db_type")
        host = request.POST.get("host")
        port = request.POST.get("port")
        database_name = request.POST.get("database_name")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Mise à jour des champs de l'objet
        source.name = name
        source.db_type = db_type
        source.host = host
        source.port = port
        source.database_name = database_name
        source.username = username

        # Sécurité : On ne modifie le mot de passe que si l'utilisateur en a saisi un nouveau
        if password and password.strip() != "":
            source.password = password

        # Sauvegarde en base de données
        source.save()

        # Message de succès et redirection
        messages.success(
            request, f'La source "{source.name}" a été modifiée avec succès !'
        )
        return redirect("parametre")

    # Si la requête est en GET (accès direct à l'URL), on redirige ou affiche les paramètres
    return render(request, "chat/parametre.html", {"source": source})


def delete_source(request, pk):
    """Supprimer une source de données"""
    source = get_object_or_404(DbSource, pk=pk)
    
    if request.method == "POST":
        source_name = source.name
        source.delete()
        
        # SI AJAX : On renvoie uniquement le JSON. PAS de messages.success !
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Source "{source_name}" supprimée avec succès!'
            })
        
        # SI FORMULAIRE CLASSIQUE : On met le message et on redirige
        messages.success(request, f'Source "{source_name}" supprimée avec succès!')
        return redirect('parametre')
    
    messages.warning(request, 'Méthode non autorisée pour la suppression!')
    return redirect('parametre')


@require_POST
def clear_messages(request):
    Message_Ai.objects.all().delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))


def chat_view(request):
    # 1. Préparation des dates pour les badges de l'historique
    aujourdhui = datetime.now()
    hier = aujourdhui - timedelta(days=1)

    # 2. Récupérer TOUS les messages pour la zone de chat principale
    all_messages = Message_Ai.objects.all().order_by('date_creation')

    # 3. Récuperer tous les data sources triés par statut actif
    data_sources = DbSource.objects.order_by('-is_active') 

    # 4. Récuperer tous les agents IA et celui actif
    agents = Agent.objects.all().order_by('-date_creation')
    active_agent = Agent.objects.filter(is_active=True).first()
    
    # 5. Récupérer uniquement les messages utilisateur pour l'historique (les plus récents d'abord)
    user_messages = Message_Ai.objects.filter(sender='user').order_by('-date_creation')
    
    # 6. Construction du contexte (Inclusion des dates formatées en chaînes)
    context = {
        'messages': all_messages,  
        'user_messages': user_messages,  
        'data_sources': data_sources,  
        'agents_list': agents,  
        'active_agent': active_agent, # Ajouté au cas où vous en auriez besoin dans le template
        'date_aujourdhui': aujourdhui.strftime('%Y-%m-%d'), # Requis pour le template
        'date_hier': hier.strftime('%Y-%m-%d'),             # Requis pour le template
    }
    
    return render(request, 'chat/chat.html', context)


def agent_ia_view(request):
    messages = Message_agent_ai.objects.all().order_by('date_creation')
    return render(request, 'chat/agent_ia.html', {'messages': messages})

def index(request):
    #articles = Article.objects.order_by('-date_publication','-id')
    return render(request, 'chat/chat.html')

# Transform - Afficher le module Transform
def parametre(request):
    # Récuperer tous les data sources base de donnée
    data_sources = DbSource.objects.all()
    # Récuperer tous les agents IA et celui actif
    agents = Agent.objects.all()
    active_agent = Agent.objects.filter(is_active=True).first()

    # 1. 🟢 CORRECTION : On récupère TOUTES les bases de données actives (QuerySet)
    active_dbs = DbSource.objects.filter(is_active=True)
    # 2. On extrait et fusionne les schémas de chaque BDD active
    full_schema_text = ""
    for db in active_dbs:
            # On appelle la méthode avec les parenthèses () et on ajoute un séparateur
        full_schema_text += db.get_db_schema() + "\n"

    print(f"Structure bdd -> {full_schema_text}") 

    return render(
        request,
        "chat/parametre.html",
        {"data_sources": data_sources,
        'agents': agents, 'active_agent': active_agent}
    )


# GErer les agents IA
# 2. Ajouter ou Modifier un agent
def save_agent(request, agent_id=None):
    agent = get_object_or_404(Agent, pk=agent_id) if agent_id else None
    
    if request.method == 'POST':
        name = request.POST.get('name')
        model_name = request.POST.get('model_name')
        api_key = request.POST.get('api_key')
        system_instruction = request.POST.get('system_instruction')
        is_active = request.POST.get('is_active') == 'on'
        
        # Création de l'agent en base de données
        new_agent = Agent.objects.create(
            name=name, 
            model_name=model_name, 
            api_key=api_key, 
            system_instruction=system_instruction, 
            is_active=is_active
        )
        
        # SÉCURITÉ AJAX : Si la requête vient du script JavaScript (Fetch), on renvoie du JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                "success": True,
                "message": "Agent créé avec succès !",
                "agent_id": new_agent.id,
                "agent_name": new_agent.name
            })
        
        messages.success(request,"Agent créé avec succès")
        #return redirect('agent_manager')
        return redirect('parametre')
        
    return render(request, 'chat/parametre.html', {'agent': agent})

def edit_agent(request, agent_id=None):
    # Si agent_id est fourni -> Modification, sinon -> Création
    agent = get_object_or_404(Agent, pk=agent_id) if agent_id else None          
    
    if request.method == 'POST':
        name = request.POST.get('name')
        model_name = request.POST.get('model_name')
        api_key = request.POST.get('api_key')
        system_instruction = request.POST.get('system_instruction')
        is_active = request.POST.get('is_active') == 'on'
                  
        if agent: # Modification
            agent.name = name
            agent.model_name = model_name
            agent.api_key = api_key
            agent.system_instruction = system_instruction
            agent.is_active = is_active
            agent.save()
            messages.success(request, "Agent modifié avec succès")
        else: # Création
            Agent.objects.create(
                name=name, model_name=model_name, api_key=api_key, 
                system_instruction=system_instruction, is_active=is_active
            )
            messages.success(request, "Agent créé avec succès")
        return redirect('parametre')
        
    return render(request, 'chat/parametre.html', {'agent': agent})

def active_agent_ai(request, agent_id):
    # 1. Récupération sécurisée de l'agent cible
    agent = get_object_or_404(Agent, id=agent_id)
    # 2. Désactivation de tous les autres agents pour avoir un choix unique
    Agent.objects.filter(is_active=True).update(is_active=False)
    
    # 3. Activation de l'agent sélectionné
    agent.is_active = True
    agent.save()
    
    # 4. Message de succès pour l'utilisateur
    messages.success(request, f"L'agent '{agent.name}' a été activé avec succès.")
    
    # 5. Redirection vers votre vue de configuration
    return redirect('parametre') # Remplacez 'parametre' par le nom réel de votre vue de configuration



# 3. Supprimer un agent
def delete_agent(request, pk):
    """Supprimer un agent de l'I.A."""
    agent = get_object_or_404(Agent, pk=pk)
    
    if request.method == "POST":
        agent_name = agent.name
        agent.delete()  # La suppression physique en BDD se fait ici
        
        # SÉCURITÉ ABSOLUE : On renvoie TOUJOURS du JSON si la requête vient de JavaScript (Fetch)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                'success': True,
                'message': f'L\'agent "{agent_name}" a été supprimé avec succès !'
            })
            
        # Uniquement pour les formulaires HTML standards (si utilisés sans JS)
        return redirect('parametre')
        
    return redirect('parametre')

# 4. Basculer d'agent actif (Clic rapide)
def toggle_agent(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    agent.is_active = True
    agent.save() # Le save() désactive automatiquement les autres
    #return redirect('agent_manager')
    return redirect('parametre')

def toggle_db_source(request, db_source_id):
    dbSOurce = get_object_or_404(DbSource, pk=db_source_id)
    dbSOurce.is_active = True
    dbSOurce.save() # Le save() désactive automatiquement les autres
    #return redirect('agent_manager')
    return redirect('parametre')

@csrf_exempt
def recherche_naturelle(request):
    # =========================================================================
    # 🔒 INTERCEPTION PRIORITAIRE EXPORT EXCEL VIA SESSION (ZÉRO SQL DANS L'URL)
    # =========================================================================
    if request.method == "GET" and request.GET.get("export") == "excel":
        result_cache = request.session.get("last_sql_result")
        if not result_cache:
            return JsonResponse({"type": "error", "data": "Session expirée ou aucun résultat à exporter."}, status=400)
            
        try:
            import openpyxl
            from django.http import HttpResponse
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Résultats Export"
            
            if result_cache and len(result_cache) > 0:
                ws.append(list(result_cache[0].keys()))
                for row in result_cache:
                    ws.append(list(row.values()))
            
            response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = 'attachment; filename="export_ia.xlsx"'
            wb.save(response)
            return response
        except Exception as e:
            return JsonResponse({"type": "error", "data": f"Erreur exportation : {str(e)}"}, status=500)


    if request.method != "POST":
        return JsonResponse({"type": "error", "data": "Méthode non autorisée"}, status=405)
    
    user_msg = request.POST.get("message", "").strip()
    phrase_utilisateur = request.POST.get('message', '').strip() or request.POST.get('q', '').strip()


    try:
        # ==========================================
        # 🟢 EXTRACTION ET FUSION DES SCHÉMAS ACTIFS
        # ==========================================
        db_active_target = router.db_for_read(DbSource)
        active_dbs = DbSource.objects.using(db_active_target).filter(is_active=True)
        db_names_list = []
            
        if not active_dbs.exists():
            return JsonResponse({"type": "error", "data": "Aucune base de données active dans les paramètres.", "agent_name": "Système"}, status=400)

        full_schema_text = ""
        for db in active_dbs:
            full_schema_text += db.get_db_schema() + "\n"
            db_names_list.append(db.name)
        source = active_dbs.first() 

        # Sécurité : On vérifie qu'une source existe AVANT de tester si c'est une requête SQL
        if source and is_sql_query(user_msg):
            result = run_query(source, user_msg)
            response_data = {
                "type": "sql",
                "data": result,
                "count": len(result),
                "agent_name": "Base de données"
            }
            # Sauvegarde du résultat en texte propre
            Message_Ai.objects.create(sender="system", content=f"SQL Result: {len(result)} lignes.")

        else:
    
    
            logger.info(f"Requête reçue | Phrase utilisateur : {phrase_utilisateur}")

            if not phrase_utilisateur:
                return JsonResponse({"type": "error", "data": "Requête vide", "agent_name": "Système"}, status=400)

            # 1. Écriture sécurisée et interopérable du message utilisateur
            db_msg = router.db_for_write(Message_Ai)
            try:
                Message_Ai.objects.using(db_msg).create(sender="user", content=phrase_utilisateur)
            except Exception as e:
                logger.error(f"Impossible d'enregistrer le message utilisateur sur {db_msg} : {e}")

            # ==========================================
            # 🟢 RÉCUPÉRATION ET INJECTION DU LONG PROMPT
            # ==========================================
            db_agent_target = router.db_for_read(Agent)
            agent_config = Agent.objects.using(db_agent_target).filter(is_active=True).first()
            
            if agent_config and agent_config.system_instruction:
                base_prompt = agent_config.system_instruction
                system_instruction_final = base_prompt.replace("{full_schema_text}", full_schema_text)
            else:
                system_instruction_final = f"Génère du SQL uniquement pour ce schéma :\n{full_schema_text}"

            # ==========================================
            # 1. OBTENIR LA RÉPONSE DE L'AGENT
            # ==========================================
            chat_result = generate_response(phrase_utilisateur, system_instruction=system_instruction_final)
            status = chat_result.get("status")

            if status in ["no_agent", "error"]:
                return JsonResponse({
                    "type": "error" if status == "error" else "no_agent",
                    "data": chat_result.get("message"),
                    "agent_name": "Système"
                }, status=400 if status == "no_agent" else 500)
            
            # =========================================================================
            # 🟢 INTERCEPTION DES RÉPONSES DE DISCUSSION (Bonjour, Aide, etc.)
            # =========================================================================
            if chat_result.get("type") == "chat":
                return JsonResponse({
                    "type": "chat", 
                    "data": chat_result.get("text"),
                    "agent_name": chat_result.get("agent_name", "Assistant")
                })
            
            # ==========================================
            # 2. EXTRACTION ET SÉCURISATION DU SQL
            # ==========================================
            requete_raw = chat_result.get("text", "").strip()
            requete_sql = re.sub(r'```sql\s*|```\s*', '', requete_raw).strip()
            
            sql_clean_lower = requete_sql.strip().lower()
            
            if "-- impossible" in sql_clean_lower:
                return JsonResponse({"type": "error", "data": "Cette demande est impossible à traduire ou non autorisée.", "agent_name": "Sécurité"}, status=400)

            #mots_extraits = set(re.findall(r'\w+', sql_clean_lower))
            mots_extraits = set(re.findall(r'\b[a-z_]+\b', sql_clean_lower))
            
            commandes_interdites = {
                "delete", "update", "drop", "truncate", "alter", "insert", "create", "grant"
            }
            #  "user", "users", "utilisateur", "utilisateurs", "password", "agent", "agents"
            
            sql_pour_premier_mot = sql_clean_lower.lstrip("() ")
            premier_mot = sql_pour_premier_mot.split()[0] if sql_pour_premier_mot.split() else ""
            #contient_multi_requetes = ";" in requete_sql

            if (premier_mot != "select" or 
                #contient_multi_requetes or 
                mots_extraits.intersection(commandes_interdites)):
                
                logger.warning(f"Blocage Sécurité (Requête non autorisée) : {requete_sql}")
                return JsonResponse({
                    "type": "error", 
                    "data": "Action non autorisée : 🚨 ACTION SUSPECTE REJETÉE.", 
                    "agent_name": "Sécurité"
                }, status=403)
                

            # --- OPTIMISATION CRITIQUE INTEROPÉRABLE Anti-Lock ---
            try:
                with transaction.atomic(using=db_msg):
                    Message_Ai.objects.using(db_msg).create(
                        sender="system", 
                        content=f"Requête SQL exécutée pour : {phrase_utilisateur}"
                    )
            except Exception as e:
                logger.error(f"Erreur écriture préventive sur la base '{db_msg}' : {e}")

            # ==========================================
            # 3. EXÉCUTION DE LA REQUÊTE SQL DISTANTE
            # ==========================================
            try:
                result = run_query(source, requete_sql)
                request.session["last_sql_result"] = result
                
                limited_result = result[:100] 
                
                for row in limited_result:
                    for key, value in row.items():
                        if hasattr(value, 'isoformat'): 
                            row[key] = value.isoformat()

                response_data = {
                    "type": "sql",
                    "data": limited_result,
                    "count": len(result),
                    "sql_genere": requete_sql, 
                    "dbs_utilisees": ", ".join(db_names_list), 
                    "agent_name": chat_result.get("agent_name", "Base de données")
                }
                
                # Sauvegarde finale sur la base gérée par le routeur
                try:
                    Message_Ai.objects.using(db_msg).create(
                        sender="system", 
                        content=f"SQL: {response_data.get('sql_genere','')}"
                    )
                except Exception as e:
                    logger.error(f"Erreur enregistrement log SQL final sur {db_msg} : {e}")

                return JsonResponse(response_data)

            except utils.OperationalError as e:
                logger.error(f"SQL ERROR: {str(e)} | Requête en cause : {requete_sql}", exc_info=True)
                return JsonResponse({
                    "type": "error",
                    "data": f"Erreur SQL distant (Détail : {str(e)})",
                    "sql_genere": requete_sql,
                    "agent_name": "Système"
                }, status=400)
        return JsonResponse(response_data)
            
    except Exception as e:
        logger.error(f"🚨 EXCEPTION CAPTURÉE LORS DE L'EXÉCUTION : {str(e)} | Requête : {requete_sql}", exc_info=True)
        return JsonResponse({
                    "type": "error",
                    "data": f"Erreur de syntaxe ou d'exécution SQL sur le serveur distant. (Détail : {str(e)})",
                    "sql_genere": requete_sql,
                    "agent_name": "Système"
        }, status=400)


def get_response(request):
    if request.method != "POST":
        return JsonResponse({"type": "error", "data": "Requête invalide"}, status=400)

    user_msg = request.POST.get("message", "").strip()
    print(f"DEBUG: user_msg reçu -> {user_msg}") 

    if not user_msg:
        return JsonResponse({"type": "error", "data": "Message vide"}, status=400)

    # Sauvegarde du message de l'utilisateur
    Message_Ai.objects.create(sender="user", content=user_msg)

    source = DbSource.objects.filter(is_active=True).first()
    print(f"DEBUG: Etat source -> {source}")

    try:
        # Sécurité : On vérifie qu'une source existe AVANT de tester si c'est une requête SQL
        if source and is_sql_query(user_msg):
            result = run_query(source, user_msg)
            response_data = {
                "type": "sql",
                "data": result,
                "count": len(result),
                "agent_name": "Base de données"
            }
            # Sauvegarde du résultat en texte propre
            Message_Ai.objects.create(sender="system", content=f"SQL Result: {len(result)} lignes.")

        else:
            # generate_response retourne désormais : {"status": "...", "text": "...", "agent_name": "..."}
            chat_result = generate_response(user_msg)
            
            if chat_result.get("status") == "no_agent":
                response_data = {
                    "type": "no_agent",
                    "data": chat_result.get("message"),
                    "agent_name": "Système"
                }
            elif chat_result.get("status") == "error":
                response_data = {
                    "type": "error",
                    "data": chat_result.get("message"),
                    "agent_name": "Système"
                }
            else:
                response_data = {
                    "type": "chat",
                    "data": chat_result.get("text"), # Extraction du texte brut pour le JS
                    "agent_name": chat_result.get("agent_name", "Inconnu") # Transmission du nom de l'agent
                }
            
            # Sauvegarde du texte brut de l'IA en base de données
            Message_Ai.objects.create(sender="system", content=response_data["data"])

        return JsonResponse(response_data)

    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        error_msg = f"Erreur système : {str(e)}"
        Message_Ai.objects.create(sender="system", content=error_msg)
        
        return JsonResponse({
            "type": "error",
            "data": error_msg,
            "agent_name": "Système"
        }, status=500)

#N'autorise pas l'interoperabilité
""" @csrf_exempt
def recherche_naturelle(request):
    # =========================================================================
    # 🔒 INTERCEPTION PRIORITAIRE EXPORT EXCEL VIA SESSION (ZÉRO SQL DANS L'URL)
    # =========================================================================
    if request.method == "GET" and request.GET.get("export") == "excel":
        result_cache = request.session.get("last_sql_result")
        if not result_cache:
            return JsonResponse({"type": "error", "data": "Session expirée ou aucun résultat à exporter."}, status=400)
            
        try:
            import openpyxl
            from django.http import HttpResponse
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Résultats Export"
            
            if result_cache and len(result_cache) > 0:
                ws.append(list(result_cache[0].keys()))
                for row in result_cache:
                    ws.append(list(row.values()))
            
            response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = 'attachment; filename="export_ia.xlsx"'
            wb.save(response)
            return response
        except Exception as e:
            return JsonResponse({"type": "error", "data": f"Erreur exportation : {str(e)}"}, status=500)

    # =========================================================================
    # 📥 TRAITEMENT DU POST DU CHAT STANDARD
    # =========================================================================
    if request.method != "POST":
        return JsonResponse({"type": "error", "data": "Méthode non autorisée"}, status=405)

    phrase_utilisateur = request.POST.get('message', '').strip() or request.POST.get('q', '').strip()
    
    print(f"le request ==>  {request}")
    print(f"La phrase utilisateur ==> {phrase_utilisateur}")

    if not phrase_utilisateur:
        return JsonResponse({"type": "error", "data": "Requête vide", "agent_name": "Système"}, status=400)

    # Sauvegarde sécurisée du message de l'utilisateur
    Message_Ai.objects.create(sender="user", content=phrase_utilisateur)

    # ==========================================
    # 🟢 EXTRACTION ET FUSION DES SCHÉMAS ACTIFS
    # ==========================================
    active_dbs = DbSource.objects.filter(is_active=True)
    db_names_list = [] # Tableau pour stocker les noms des BDD actives
    
    if not active_dbs.exists():
        return JsonResponse({"type": "error", "data": "Aucune base de données active dans les paramètres.", "agent_name": "Système"}, status=400)

    full_schema_text = ""
    for db in active_dbs:
        full_schema_text += db.get_db_schema() + "\n"
        db_names_list.append(db.name)

    # ==========================================
    # 🟢 RÉCUPÉRATION ET INJECTION DU LONG PROMPT
    # ==========================================
    agent_config = Agent.objects.filter(is_active=True).first()
    
    if agent_config and agent_config.system_instruction:
        base_prompt = agent_config.system_instruction
        system_instruction_final = base_prompt.replace("{full_schema_text}", full_schema_text)
    else:
        system_instruction_final = f"Génère du SQL uniquement pour ce schéma :\n{full_schema_text}"

    # ==========================================
    # 1. OBTENIR LA RÉPONSE DE L'AGENT
    # ==========================================
    chat_result = generate_response(phrase_utilisateur, system_instruction=system_instruction_final)
    status = chat_result.get("status")

    print(f"Le chat_result ==> {chat_result}")
    print(f"Le status ==> {status}")

    if status in ["no_agent", "error"]:
        return JsonResponse({
            "type": "error" if status == "error" else "no_agent",
            "data": chat_result.get("message"),
            "agent_name": "Système"
        }, status=400 if status == "no_agent" else 500)
    
    # =========================================================================
    # 🟢 INTERCEPTION DES RÉPONSES DE DISCUSSION (Bonjour, Aide, etc.)
    # =========================================================================
    if chat_result.get("type") == "chat":
        return JsonResponse({
            "type": "chat", 
            "data": chat_result.get("text"),
            "agent_name": chat_result.get("agent_name", "Assistant")
        })
    
    # ==========================================
    # 2. EXTRACTION ET SÉCURISATION DU SQL (Scanner de Tokens)
    # ==========================================
    requete_raw = chat_result.get("text", "").strip()
    requete_sql = re.sub(r'```sql\s*|```\s*', '', requete_raw).strip()

    print(f"Le requete_sql généré ==> {requete_sql}")
    
    # 🚨 BLINDAGE DE SÉCURITÉ : Isolation et validation de chaque composant du script SQL
    sql_clean_lower = requete_sql.strip().lower()
    
    # Si l'IA a renvoyé l'instruction d'impossibilité suite à une demande illicite
    if "-- impossible" in sql_clean_lower:
        return JsonResponse({"type": "error", "data": "Cette demande est impossible à traduire ou non autorisée.", "agent_name": "Sécurité"}, status=400)

    # Découpage du texte en mots uniques complets (élimine les ruses de concaténation)
    mots_extraits = set(re.findall(r'\w+', sql_clean_lower))
    
    # Liste noire des commandes d'altération et de modification d'écriture
    commandes_interdites = {
        "delete", "update", "drop", "truncate", "alter", "insert", "create", "grant",
        "user", "users", "utilisateur", "utilisateurs", "password", "agent", "agents"
    }
    
    # 🟢 CORRECTION SYNTAXE UNION : On nettoie les parenthèses à gauche avant d'isoler le premier mot
    sql_pour_premier_mot = sql_clean_lower.lstrip("() ")
    premier_mot = sql_pour_premier_mot.split()[0] if sql_pour_premier_mot.split() else ""
    
    # Détection de l'empilage multi-requêtes
    contient_multi_requetes = ";" in requete_sql

    # Analyse et blocage immédiat si une anomalie ou une tentative d'injection est détectée
    if (premier_mot != "select" or 
        contient_multi_requetes or 
        mots_extraits.intersection(commandes_interdites)):
        
        print(f"Le système accepte uniquement les instructions de consultation (SELECT) : {requete_sql}")
        return JsonResponse({
            "type": "error", 
            "data": "Action non autorisée : 🚨 ACTION SUSPECTE REJETÉE.", 
            "agent_name": "Sécurité"
        }, status=403)
        
    # Choix de la première source pour l'exécution physique
    source = active_dbs.first() 
    print(f"La source d'exécution ==> {source}")

    # --- OPTIMISATION CRITIQUE Anti-Lock ---
      try:
        with transaction.atomic():
            Message_Ai.objects.create(
                sender="system", 
                content=f"Requête SQL exécutée pour : {phrase_utilisateur}"
            )
    except Exception as e:
        print(f"Erreur écriture préventive : {e}")

    # ==========================================
    # 3. EXÉCUTION DE LA REQUÊTE SQL DISTANTE (Unique Try Block)
    # ==========================================
    try:
        result = run_query(source, requete_sql)
        
        # 🟢 OPTIMISATION : On stocke le résultat propre dans la session pour l'export Excel sécurisé
        request.session["last_sql_result"] = result
        
        limited_result = result[:100] 
        
        for row in limited_result:
            for key, value in row.items():
                if hasattr(value, 'isoformat'): 
                    row[key] = value.isoformat()

        response_data = {
            "type": "sql",
            "data": limited_result,
            "count": len(result),
            "sql_genere": requete_sql, 
            "dbs_utilisees": ", ".join(db_names_list), 
            "agent_name": chat_result.get("agent_name", "Base de données")
        }
        print(f"Le response_data ==> {response_data}")
        
        # Sécurisation de la conversion de type pour éviter le crash du logger de base de données
        Message_Ai.objects.create(
            sender="system", 
            content=f"SQL: {response_data.get('sql_genere','')}"
        )

        return JsonResponse(response_data)

    except utils.OperationalError as e:
        print(f"SQL ERROR: {str(e)} | Requête en cause : {requete_sql}")
        return JsonResponse({
            "type": "error",
            "data": f"Erreur SQL distant (Détail : {str(e)})",
            "sql_genere": requete_sql,
            "agent_name": "Système"
        }, status=400)
    
    # 🟢 FUSION UNIQUE : Captures groupées au sein du même bloc d'exécution
    except Exception as e:
        print(f"🚨 EXCEPTION CAPTURÉE LORS DE L'EXÉCUTION : {str(e)} | Requête : {requete_sql}")
        return JsonResponse({
            "type": "error",
            "data": f"Erreur de syntaxe ou d'exécution SQL sur le serveur distant. (Détail : {str(e)})",
            "sql_genere": requete_sql,
            "agent_name": "Système"
        }, status=400)
 """