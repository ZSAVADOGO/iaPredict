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
from django.db import transaction

from .models import DbSource
from .forms import DataSourceForm
from .errors import format_openai_error

#TEST SWEET ALERT
from django.contrib import messages

import pymysql
import psycopg2



def get_agent_api_response(request):
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

            return JsonResponse({'error': error_text}, status=500)

        
        



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

def test_connect_bdd(request, pk):
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
    return redirect("parametre")

    

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

from django.http import JsonResponse

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
    


def run_query(source, sql):
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
            if isinstance(value, bytes):
                cleaned_row.append(value.decode("utf-8", errors="ignore"))
            else:
                cleaned_row.append(value)
        cleaned_rows.append(dict(zip(columns, cleaned_row)))

    return cleaned_rows


def activ_source(request):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    source_id = request.POST.get("active_source")

    if not source_id:
        return JsonResponse({"error": "Aucune source sélectionnée"}, status=400)

    source = get_object_or_404(DbSource, pk=source_id)
    source.activate()

    return JsonResponse({
        "success": True,
        "source_id": source.id,
        "source_name": source.name
    })


def add_source(request):
    form = DataSourceForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("/")
    return render(request, "chat/add_source.html", {"form": form})

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
        messages.success(request, f'Source "{source_name}" supprimée avec succès!')
        
        # Si c'est une requête AJAX, retourner JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Source "{source_name}" supprimée avec succès!'
            })
        
        #return redirect("sources")
        return redirect('parametre')
    
    # Si GET, rediriger vers la liste
    messages.warning(request, 'Méthode non autorisée pour la suppression!')
    #return redirect("sources")
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
    
    # Récupérer uniquement les messages utilisateur pour l'historique (les plus récents d'abord)
    user_messages = Message_Ai.objects.filter(sender='user').order_by('-timestamp')
    
    context = {
        'messages': all_messages,  # Pour la zone de chat
        'user_messages': user_messages,  # Pour l'historique
        'data_sources': data_sources,  # Pour la gestion des sources

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
    choices2 = Agent.MODEL_CHOICES
    print(f"DEBUG: choices2 -> {choices2}") 
    return render(
        request,
        "chat/parametre.html",
        {"data_sources": data_sources,
        'agents': agents, 'active_agent': active_agent,
        "choices2": choices2,}
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
def delete_agent(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    agent.delete()
    #return redirect('agent_manager')
    return redirect('parametre')

# 4. Basculer d'agent actif (Clic rapide)
def toggle_agent(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    agent.is_active = True
    agent.save() # Le save() désactive automatiquement les autres
    #return redirect('agent_manager')
    return redirect('parametre')