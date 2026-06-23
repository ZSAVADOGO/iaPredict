#from pyexpat.errors import messages
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse
import requests
from .models import Agent, Message_Ai, Message_agent_ai
from .responses_ai import generate_response, generate_ai_response

from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import connection, transaction,utils

import re
import datetime
from django.views.decorators.csrf import csrf_exempt

from .models import DbSource
from .forms import DataSourceForm
#TEST SWEET ALERT
from django.contrib import messages

from django.http import JsonResponse

import pymysql
import psycopg2



""" def get_agent_api_response(request):
    if request.method == "POST":
        user_input = request.POST.get('message')
        # On enregistre toujours l'entrée utilisateur
        Message_agent_ai.objects.create(sender="user", content=user_input)
        try:
            ai_response = generate_ai_response(user_input)  
            # Enregistrement du succès
            Message_agent_ai.objects.create(sender="system", content=ai_response)
            return JsonResponse({'content': ai_response}) 
        except Exception as e:
            #error_text = str(e)
            #print(f"ERREUR CAPTURÉE : {error_text}")
            # APPEL AU FICHIER CENTRAL
            error_text = format_openai_error(e)
            print(f"ERREUR CENTRALE: {error_text}")

            # OPTIONNEL : Enregistrer l'erreur en BDD pour savoir que l'IA a échoué
            Message_agent_ai.objects.create(
                sender="system", 
                content=f"Erreur : {error_text}"
            )

            return JsonResponse({'error': error_text}, status=500) """

        
        



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
    
""" def test_connect_bdd(request, pk):
    source = get_object_or_404(DbSource, pk=pk)

    try:
        if source.db_type == "mysql":
            pymysql.connect(
                host=source.host,
                user=source.username,
                password=source.password,
                database=source.database_name,
                port=source.port
            )
        elif source.db_type == "postgres":
            psycopg2.connect(
                host=source.host,
                user=source.username,
                password=source.password,
                dbname=source.database_name,
                port=source.port
            )

        source.status = "connected"
    except Exception:
        source.status = "error"

    print(f"DEBUG: source.status mis à jour -> {source.status}") 
    print(f"DEBUG: source.is_active -> {source.is_active}")
    print(f"DEBUG: source -> {source}")

    source.save()
    return redirect("parametre") """

    

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
    sql_keywords = ["select", "insert", "update", "delete"]
    msg = message.lower().strip()
    return any(msg.startswith(word) for word in sql_keywords)

def validate_query(sql):
    sql = sql.strip().lower()
    if not sql.startswith("select"):
        raise ValueError("Seules les requêtes SELECT sont autorisées.")
    return sql

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

""" def get_response(request):

    if request.method != "POST":
        return JsonResponse({"type": "error", "data": "Requête invalide"}, status=400)

    user_msg = request.POST.get("message", "").strip()
    
    # Équivalent de console.log(user_msg)
    print(f"DEBUG: user_msg reçu -> {user_msg}") 

    if not user_msg:
        return JsonResponse({"type": "error", "data": "Message vide"}, status=400)

    Message_Ai.objects.create(sender="user", content=user_msg)

    source = DbSource.objects.filter(is_active=True).first()

    print(f"DEBUG: 1 Etat source -> {source}")
    print(f"DEBUG: 2 Etat source -> {source.database_name}")
    print(f"DEBUG: 3 Etat source -> {source.db_type}")

    try:
        #if source and is_sql_query(user_msg):
        if is_sql_query(user_msg):
            result = run_query(source, user_msg)

            response = {
                "type": "sql",
                "data": result,
                "count": len(result)
            }

        else:
            response = {
                "type": "chat",
                "data": generate_response(user_msg)
            }

    except Exception as e:
        response = {
            "type": "error",
            "data": str(e)
        }
# Équivalent de console.log(user_msg)
#    print(f"DEBUG: response retouner -> {response}") 

    Message_Ai.objects.create(sender="system", content=str(response))
# Récupérer uniquement les messages utilisateur pour l'historique (les plus récents d'abord)
    #user_messages = Message_Ai.objects.filter(sender='user').order_by('-timestamp')
    return JsonResponse(response) """


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
    

# BON MAIS VEUT OPTIMISER
""" def get_response(request):
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
        }, status=500) """


def run_query(source, sql):
    """
    Exécute de manière autonome et sécurisée une requête SELECT sur une base distante.
    Nettoie et sérialise les types complexes (bytes, dates) pour compatibilité JSON.
    """
    # 1. Nettoyage initial et retrait du point-virgule final
    sql = sql.strip().rstrip(";")

    # =======================================================
    # 🚨 BLINDAGE DE SÉCURITÉ AUTONOME (Scanner de Tokens)
    # =======================================================
    sql_clean_lower = sql.lower()
    
    # Extraction de chaque mot de manière isolée
    mots_extraits = set(re.findall(r'\w+', sql_clean_lower))
    
    # Liste noire absolue des commandes d'altération
    commandes_interdites = {"delete", "update", "drop", "truncate", "alter", "insert", "create", "grant"}
    
    # Extraction du premier mot
    premier_mot = sql_clean_lower.split()[0] if sql_clean_lower.split() else ""
    
    # Détection des points-virgules internes (tentative d'empilage)
    if ";" in sql or premier_mot != "select" or mots_extraits.intersection(commandes_interdites):
        raise PermissionError("Action non autorisée : Cette méthode accepte exclusivement une unique instruction SELECT.")

    # =======================================================
    # 📊 BRIDAGE AUTOMATIQUE DU VOLUME (LIMIT)
    # =======================================================
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
        cleaned_row = {}
        for col_name, value in zip(columns, row):
            # 1. Gestion des chaînes de octets (BLOB / Binary)
            if isinstance(value, bytes):
                cleaned_row[col_name] = value.decode("utf-8", errors="ignore")
            
            # 2. Conversion automatique des types Temporels (Évite les crashs JSON)
            elif isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
                cleaned_row[col_name] = value.isoformat()
                
            # 3. Gestion des autres types standards (int, float, str, None)
            else:
                cleaned_row[col_name] = value
                
        cleaned_rows.append(cleaned_row)

    return cleaned_rows

# BON MAI VEUT OPTIMISER
""" def run_query(source, sql):
    sql = sql.strip().rstrip(";")

    if not sql.lower().startswith("select"):
        raise ValueError("Seules les requêtes SELECT sont autorisées.")

    if "limit" not in sql.lower():
        sql += " LIMIT 50"

    with open_connection(source) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

    cleaned_rows = []

    for row in rows:
        cleaned_row = []
        for value in row:
            # 1. Gestion des chaînes de octets (votre code existant)
            if isinstance(value, bytes):
                cleaned_row.append(value.decode("utf-8", errors="ignore"))
            
            # 2. OPTIMISATION CRITIQUE : Conversion des types Date/Datetime pour éviter le crash JSON
            elif isinstance(value, (datetime.datetime, datetime.date)):
                cleaned_row.append(value.isoformat())
                
            else:
                cleaned_row.append(value)
                
        # Assemblage de la ligne sous forme de dictionnaire propre
        cleaned_rows.append(dict(zip(columns, cleaned_row)))

    return cleaned_rows """


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
        return redirect("/")
    return render(request, "chat/add_source.html", {"form": form}) """

def edit_source(request, pk):
    source = get_object_or_404(DbSource, pk=pk)
    form = DataSourceForm(request.POST or None, instance=source)
    if form.is_valid():
        form.save()
        messages.success(request, f'La source "{source.name}" a été modifiée avec succès !')
        return redirect('parametre') # Redirige vers vos paramètres
        
    # Si la requête vient du script JS (AJAX), on peut renvoyer un template partiel ou le même
    return render(request, "chat/add_source.html", {"form": form})


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
    # Récupérer TOUS les messages pour la conversation principale
    all_messages = Message_Ai.objects.all().order_by('timestamp')

    # Récuperer tous les data sources
    data_sources = DbSource.objects.all()

    # Récuperer tous les agents IA et celui actif
    #agents = Agent.objects.all()
    agents = Agent.objects.all().order_by('-date_creation')
    active_agent = Agent.objects.filter(is_active=True).first()
    data_sources = DbSource.objects.order_by('-is_active') #.order_by('-date_creation') if DbSource.objects.filter(is_active=True).exists() else None
    
    # Récupérer uniquement les messages utilisateur pour l'historique (les plus récents d'abord)
    user_messages = Message_Ai.objects.filter(sender='user').order_by('-timestamp')
    
    context = {
        'messages': all_messages,  # Pour la zone de chat
        'user_messages': user_messages,  # Pour l'historique
        'data_sources': data_sources,  # Pour la gestion des sources
        'agents_list': agents,  # Pour la gestion des agents IA

    }
    return render(request, 'chat/chat.html', context)

def agent_ia_view(request):
    messages = Message_agent_ai.objects.all().order_by('timestamp')
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

# 1. Liste des agents & Gestion
""" def agent_manager(request):
    agents = Agent.objects.all()
    active_agent = Agent.objects.filter(is_active=True).first()
    print(f"DEBUG: liste des agents ia -> {agents}") 
    print(f"DEBUG: Agents Actifs -> {active_agent}") 
    return render(request, 'chat/parametre.html', {'agents': agents, 'active_agent': active_agent}) """

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

# 1. Modifier un agent
""" def edit_agent(request, agent_id=None):
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
            # Envoi du message à afficher sur la page suivante SWEET ALERT
            messages.success(request, "Agent modifié avec succès")

        else: # Création
            Agent.objects.create(
                name=name, model_name=model_name, api_key=api_key, 
                system_instruction=system_instruction, is_active=is_active
                )
            messages.success(request,"Agent créé avec succès")
        #return redirect('agent_manager')
        return redirect('parametre')
        
    #return render(request, 'chat/agent_form.html', {'agent': agent, 'choices': Agent.MODEL_CHOICES})
    return render(request, 'chat/parametre.html', {'agent': agent}) """

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

""" def delete_agent(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    agent.delete()
    #return redirect('agent_manager')
    return redirect('parametre') """

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

""" @csrf_exempt
def recherche_naturelle(request):
    if request.method != "POST":
        return JsonResponse({"type": "error", "data": "Méthode non autorisée"}, status=405)

    phrase_utilisateur = request.POST.get('message', '').strip() or request.POST.get('q', '').strip()
    
    print(f"le request ==>  {request}")
    print(f"La phrase utilisateur ==> {phrase_utilisateur}")

    if not phrase_utilisateur:
        return JsonResponse({"type": "error", "data": "Requête vide", "agent_name": "Système"}, status=400)

    # ==========================================
    # 🟢 EXTRACTION ET FUSION DES SCHÉMAS ACTIFS
    # ==========================================
    active_dbs = DbSource.objects.filter(is_active=True)
    db_names_list = [] # 🟢 On crée un petit tableau vide pour stocker les noms
    if not active_dbs.exists():
        return JsonResponse({"type": "error", "data": "Aucune base de données active dans les paramètres.", "agent_name": "Système"}, status=400)

    full_schema_text = ""
    for db in active_dbs:
        # Utilisation de get_db_schema() comme demandé dans votre schéma
        full_schema_text += db.get_db_schema() + "\n"
        db_names_list.append(db.name) # 🟢 On ajoute le nom de la BDD à chaque passage de boucle
    # ==========================================
    # 🟢 RÉCUPÉRATION ET INJECTION DU LONG PROMPT
    # ==========================================
    # On récupère le premier agent actif qui contient le modèle de prompt dans SQLite
    agent_config = Agent.objects.filter(is_active=True).first()
    
    if agent_config and agent_config.system_instruction:
        # On remplace dynamiquement la balise par la structure réelle de vos BDD
        base_prompt = agent_config.system_instruction
        system_instruction_final = base_prompt.replace("{full_schema_text}", full_schema_text)
    else:
        # Prompt de secours au cas où SQLite est vide
        system_instruction_final = f"Génère du SQL uniquement pour ce schéma :\n{full_schema_text}"

    # ==========================================
    # 1. OBTIENIR LA RÉPONSE DE L'AGENT
    # ==========================================
    # ⚠️ IMPORTANT : Modifiez votre fonction 'generate_response' pour qu'elle accepte l'instruction système
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
            
    # 2. Extraction et nettoyage du SQL
    requete_raw = chat_result.get("text", "").strip()
    requete_sql = re.sub(r'```sql\s*|```\s*', '', requete_raw).strip()

    print(f"Le requete_sql ==> {requete_sql}")
    
    if not requete_sql.lower().startswith("select"):
        return JsonResponse({"type": "error", "data": "Action non autorisée", "agent_name": "Sécurité"}, status=403)
        
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

    # Étape 4 : Exécution de la requête SQL externe
    try:
        result = run_query(source, requete_sql)
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

        return JsonResponse(response_data)

    except utils.OperationalError as e:
        print(f"SQL ERROR: {str(e)} | Requête en cause : {requete_sql}")
        return JsonResponse({
            "type": "error",
            "data": f"Erreur SQL distant (Détail : {str(e)})",
            "sql_genere": requete_sql,
            "agent_name": "Système"
        }, status=400) """


@csrf_exempt
def recherche_naturelle(request):
    if request.method != "POST":
        return JsonResponse({"type": "error", "data": "Méthode non autorisée"}, status=405)

    phrase_utilisateur = request.POST.get('message', '').strip() or request.POST.get('q', '').strip()
    
    print(f"le request ==>  {request}")
    print(f"La phrase utilisateur ==> {phrase_utilisateur}")

    if not phrase_utilisateur:
        return JsonResponse({"type": "error", "data": "Requête vide", "agent_name": "Système"}, status=400)

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
            
    # ==========================================
    # 2. EXTRACTION ET SÉCURISATION DU SQL (Scanner de Tokens)
    # ==========================================
    requete_raw = chat_result.get("text", "").strip()
    requete_sql = re.sub(r'```sql\s*|```\s*', '', requete_raw).strip()

    print(f"Le requete_sql généré ==> {requete_sql}")
    
    # 🚨 BLINDAGE DE SÉCURITÉ : Isolation et validation de chaque composant du script SQL
    sql_clean_lower = requete_sql.strip().lower()
    
    # Découpage du texte en mots uniques complets (élimine les ruses de concaténation)
    mots_extraits = set(re.findall(r'\w+', sql_clean_lower))
    
    # Liste noire des commandes d'altération et de modification d'écriture
    commandes_interdites = {"delete", "update", "drop", "truncate", "alter", "insert", "create", "grant"}
    
    # Extraction stricte du premier mot d'instruction
    premier_mot = sql_clean_lower.split()[0] if sql_clean_lower.split() else ""
    
    # Détection de l'empilage multi-requêtes
    contient_multi_requetes = ";" in requete_sql

    # Analyse et blocage immédiat si une anomalie ou une tentative d'injection est détectée
    if (premier_mot != "select" or 
        contient_multi_requetes or 
        mots_extraits.intersection(commandes_interdites)):
        
        print(f"🚨 ACTION SUSPECTE INTERCEPTÉE : {requete_sql}")
        return JsonResponse({
            "type": "error", 
            "data": "Action non autorisée : Le système accepte uniquement les instructions de consultation (SELECT).", 
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
    # 3. EXÉCUTION DE LA REQUÊTE SQL DISTANTE
    # ==========================================
    try:
        result = run_query(source, requete_sql)
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

        return JsonResponse(response_data)

    except utils.OperationalError as e:
        print(f"SQL ERROR: {str(e)} | Requête en cause : {requete_sql}")
        return JsonResponse({
            "type": "error",
            "data": f"Erreur SQL distant (Détail : {str(e)})",
            "sql_genere": requete_sql,
            "agent_name": "Système"
        }, status=400)
    
    # --- INTERCEPTION ET NETTOYAGE DES ERREURS D'I.A. (Quotas, pannes Google...) ---
    except Exception as e:
        # Appel de notre service de nettoyage des erreurs
        error_info = get_clean_ai_error(e, provider_name='gemini')
        
        print(f"AI ERROR TRAITÉE : Status {error_info['status']} | {error_info['message']}")
        
        return JsonResponse({
            "type": "error",
            "data": error_info["message"],
            "agent_name": "Système"
        }, status=error_info["status"])