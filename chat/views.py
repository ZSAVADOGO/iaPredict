#from pyexpat.errors import messages
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse
import requests
from .models import Message, Message_agent_ai
from .responses import generate_response, generate_ai_response

from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import DataSource
from .forms import DataSourceForm
from .errors import format_openai_error

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
    source = get_object_or_404(DataSource, pk=pk)

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
    source = get_object_or_404(DataSource, pk=pk)
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

def get_response(request):

    if request.method != "POST":
        return JsonResponse({"type": "error", "data": "Requête invalide"}, status=400)

    user_msg = request.POST.get("message", "").strip()
    
    # Équivalent de console.log(user_msg)
    print(f"DEBUG: user_msg reçu -> {user_msg}") 

    if not user_msg:
        return JsonResponse({"type": "error", "data": "Message vide"}, status=400)

    Message.objects.create(sender="user", content=user_msg)

    source = DataSource.objects.filter(is_active=True).first()

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

    Message.objects.create(sender="system", content=str(response))
# Récupérer uniquement les messages utilisateur pour l'historique (les plus récents d'abord)
    #user_messages = Message.objects.filter(sender='user').order_by('-timestamp')
    return JsonResponse(response)

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

    source = get_object_or_404(DataSource, pk=source_id)
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

def edit_source(request, pk):
    source = get_object_or_404(DataSource, pk=pk)
    form = DataSourceForm(request.POST or None, instance=source)
    if form.is_valid():
        form.save()
        return redirect("/")
    return render(request, "chat/add_source.html", {"form": form})

def delete_source(request, pk):
    """Supprimer une source de données"""
    source = get_object_or_404(DataSource, pk=pk)
    
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
    Message.objects.all().delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))


def chat_view(request):
    # Récupérer TOUS les messages pour la conversation principale
    all_messages = Message.objects.all().order_by('timestamp')

    # Récuperer tous les data sources
    data_sources = DataSource.objects.all()
    
    # Récupérer uniquement les messages utilisateur pour l'historique (les plus récents d'abord)
    user_messages = Message.objects.filter(sender='user').order_by('-timestamp')
    
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
   # Récuperer tous les data sources
    data_sources = DataSource.objects.all()
    return render(
        request,
        "chat/parametre.html",
        {"data_sources": data_sources}
    )