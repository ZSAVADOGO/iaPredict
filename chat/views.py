# from pyexpat.errors import messages
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
from django.db import connection, transaction, utils

import re

import json

# import datetime
from django.views.decorators.csrf import csrf_exempt

from django.db import router
import logging

# Configuration d'un logger interopérable
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from django.shortcuts import render

from .models import DbSource
from .forms import DataSourceForm

# TEST SWEET ALERT
from django.contrib import messages

from django.http import JsonResponse

import pymysql
import psycopg2


# En mode TEST
def ask_ai_agent(request):
    # Données à envoyer à l'agent IA dans n8n
    payload = {"user_input": "Comment optimiser mon code ?", "user_id": request.user.id}

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
    db_type = request.POST.get("db_type")
    host = request.POST.get("host")
    database_name = request.POST.get("database_name")
    port = request.POST.get("port")
    username = request.POST.get("username")
    password = request.POST.get("password")

    # Instanciation temporaire en mémoire (sans save())
    temp_source = DbSource(
        db_type=db_type,
        host=host,
        database_name=database_name,
        port=port,
        username=username,
        password=password,
    )

    try:
        is_valid, error_msg = temp_source.check_connection()
        if is_valid:
            return JsonResponse({"success": True, "message": "Connexion réussie !"})
        else:
            return JsonResponse(
                {"success": False, "message": f"Échec : {error_msg}"}, status=400
            )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Erreur système : {str(e)}"}, status=500
        )


def de_connect_bdd(request, pk):
    source = get_object_or_404(DbSource, pk=pk)
    source.disconnect()
    print(f"DEBUG: source.status après déconnexion -> {source.status}")
    print(f"DEBUG: source.is_active après déconnexion -> {source.is_active}")
    return JsonResponse({"status": "success", "source_id": source.id})


def is_sql_query(message):
    # sql_keywords = ["select", "insert", "update", "delete"]
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
            cursorclass=pymysql.cursors.Cursor,
        )

    elif source.db_type == "postgres":
        return psycopg2.connect(
            host=source.host,
            user=source.username,
            password=source.password,
            dbname=source.database_name,
            port=source.port,
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
# n'est pas operable
""" def run_query(source, sql):
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

    return cleaned_rows  """

""" def run_query(source, sql):
    if not sql or not sql.strip():
        raise ValueError("La requête SQL fournie est vide.")

    # =======================================================
    # 🧹 NETTOYAGE CHIRURGICAL ET ROBUSTE DES COMMENTAIRES
    # =======================================================
    # 1. Normalisation universelle des sauts de ligne
    sql_normalise = sql.replace('\r\n', '\n').replace('\r', '\n')
    
    lignes_propres = []
    for ligne in sql_normalise.split('\n'):
        # On extrait uniquement la partie située avant le commentaire '--'
        if '--' in ligne:
            ligne_sans_commentaire = ligne.split('--')[0]
            lignes_propres.append(ligne_sans_commentaire)
        else:
            lignes_propres.append(ligne)
            
    # 2. Reconstitution avec des espaces pour préserver la séparation des mots-clés
    sql_nettoye = " ".join(lignes_propres)
    
    # 3. Suppression des blocs de commentaires /* ... */
    sql_nettoye = re.sub(r'/\*.*?\*/', ' ', sql_nettoye, flags=re.DOTALL)
    
    # 4. Nettoyage des espaces multiples et des points-virgules finaux
    sql_nettoye = re.sub(r'\s+', ' ', sql_nettoye).strip()
    sql_nettoye = re.sub(r';+$', '', sql_nettoye).strip()

    # 🟢 DÉBOGUAGE CRUCIAL : Affiche la requête exacte dans votre terminal Django (runserver)
    print("\n[DEBUG REQUÊTE NETTOYÉE ENVOYÉE À MYSQL] :")
    print(f"--> {sql_nettoye} <--\n")
 """
""" def run_query(source, sql):
    if not sql or not sql.strip():
        raise ValueError("La requête SQL fournie est vide.")
    print(f"DAns run_query Le sql --> {sql}")

    # =======================================================
    # 🧹 NETTOYAGE CHIRURGICAL ET ROBUSTE DES COMMENTAIRES
    # =======================================================
    # Normalisation universelle des sauts de ligne
    sql_normalise = sql.replace('\r\n', '\n').replace('\r', '\n')
    
    lignes_propres = []
    for ligne in sql_normalise.split('\n'):
        # 🟢 CORRECTIF STRICT : On extrait UNIQUEMENT la partie de code située AVANT le '--'
        if '--' in ligne:
            code_utile_uniquement = ligne.split('--')[0]
            lignes_propres.append(code_utile_uniquement)
        else:
            lignes_propres.append(ligne)
            
    # Reconstitution linéaire de la requête en injectant un espace pour éviter les fusions de mots-clés
    sql_nettoye = " ".join(lignes_propres)
    
    # Suppression des blocs de commentaires de style /* ... */
    sql_nettoye = re.sub(r'/\*.*?\*/', ' ', sql_nettoye, flags=re.DOTALL)
    
    # Nettoyage des espaces multiples et des points-virgules finaux accumulés
    sql_nettoye = re.sub(r'\s+', ' ', sql_nettoye).strip()
    sql_nettoye = re.sub(r';+$', '', sql_nettoye).strip()

    # DÉBOGUAGE CRUCIAL : Permet de vérifier dans votre console que la requête est ENTIÈRE
    print("\n[DEBUG REQUÊTE NETTOYÉE ENVOYÉE À MYSQL] :")
    print(f"--> {sql_nettoye} <--\n")

    if not sql_nettoye:
        raise ValueError("La requête SQL est devenue vide après le nettoyage.")

    # =======================================================
    # 🚨 BLINDAGE DE SÉCURITÉ INTELLIGENT
    # =======================================================
    sql_clean_lower = sql_nettoye.lower()
    mots_extraits = set(re.findall(r"\b[a-z_]+\b", sql_clean_lower))

    commandes_interdites = {
        "delete", "drop", "truncate", "alter", 
        "insert", "create", "grant", "replace"
    }

    # Validation du faux positif 'update' dans 'timestampdiff'
    contient_commande_update = False
    if "update" in mots_extraits:
        if "timestampdiff" in sql_clean_lower:
            sql_sans_timestampdiff = sql_clean_lower.replace('timestampdiff', '')
            if "update" in set(re.findall(r"\b[a-z_]+\b", sql_sans_timestampdiff)):
                contient_commande_update = True
        else:
            contient_commande_update = True

    premier_mot = sql_clean_lower.lstrip("() ").split()
    premier_mot = premier_mot[0] if premier_mot else ""

    if (
        ";" in sql_nettoye  
        or premier_mot != "select"  
        or mots_extraits.intersection(commandes_interdites)  
        or contient_commande_update  
    ):
        raise PermissionError(
            "Action non autorisée : Cette méthode accepte exclusivement une unique instruction SELECT."
        )

    # =======================================================
    # ⚡ EXÉCUTION DE LA REQUÊTE NETTOYÉE
    # =======================================================
    with open_connection(source) as conn:
        with conn.cursor() as cursor:
            # On exécute la version linéaire nettoyée de tout commentaire destructeur
            cursor.execute(sql_nettoye)  
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

    cleaned_rows = [
        {
            columns[i]: (val.decode("utf-8", errors="ignore") if isinstance(val, bytes) else val)
            for i, val in enumerate(row)
        }
        for row in rows 
    ]

    return cleaned_rows """

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

        return JsonResponse(
            {
                "success": False,
                "error": error_msg,
                "source_id": db_source.id,
                "source_name": db_source.name,
            },
            status=400,
        )  # Code 400 pour indiquer une mauvaise configuration / erreur

    # 3. En cas de succès : On active normalement
    db_source.activate(status="connected")

    # Message de succès pour l'utilisateur
    messages.success(
        request, f"La source '{db_source.name}' a été vérifiée et activée avec succès."
    )

    return JsonResponse(
        {"success": True, "source_id": db_source.id, "source_name": db_source.name}
    )


def add_source(request):
    form = DataSourceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Option 1 (Recommandée) : On récupère l'objet créé par le formulaire
        nouvelle_source = form.save()

        # On accède directement à l'attribut .name de l'instance du modèle
        messages.success(
            request, f'La Source "{nouvelle_source.name}" a été créée avec succès !'
        )
        return redirect("parametre")

    # Si le formulaire n'est pas valide ou en méthode GET
    return render(request, "chat/parametre.html", {"form": form})


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
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "message": f'Source "{source_name}" supprimée avec succès!',
                }
            )

        # SI FORMULAIRE CLASSIQUE : On met le message et on redirige
        messages.success(request, f'Source "{source_name}" supprimée avec succès!')
        return redirect("parametre")

    messages.warning(request, "Méthode non autorisée pour la suppression!")
    return redirect("parametre")


@require_POST
def clear_messages(request):
    Message_Ai.objects.all().delete()
    return redirect(request.META.get("HTTP_REFERER", "/"))


def chat_view(request):
    # 1. Préparation des dates pour les badges de l'historique
    aujourdhui = datetime.now()
    hier = aujourdhui - timedelta(days=1)

    # 2. Récupérer TOUS les messages pour la zone de chat principale
    all_messages = Message_Ai.objects.all().order_by("date_creation")

    # 🟢 OPTIMISATION APPLIQUÉE : Qualification en amont de chaque message pour le template
    for msg in all_messages:
        msg.is_json = False
        msg.is_sql_direct = False

        # Cas A : Recherche d'un Dashboard Analytique structuré (Payload JSON)
        if msg.sender == "system" and msg.content.strip().startswith("{"):
            try:
                parsed_data = json.loads(msg.content)
                if parsed_data.get("type") == "sql_dashboard":
                    msg.is_json = True
            except json.JSONDecodeError:
                pass

        # Cas B : Recherche d'un retour d'exécution SQL direct saisi par l'utilisateur
        elif msg.sender == "system" and msg.content.strip().startswith("SQL Direct"):
            msg.is_sql_direct = True

    # 3. Récupérer tous les data sources triés par statut actif
    data_sources = DbSource.objects.order_by("-is_active")

    # 4. Récupérer tous les agents IA et celui actif
    agents = Agent.objects.all().order_by("-date_creation")
    active_agent = Agent.objects.filter(is_active=True).first()

    # 5. Récupérer uniquement les messages utilisateur pour l'historique (les plus récents d'abord)
    user_messages = Message_Ai.objects.filter(sender="user").order_by("-date_creation")

    # 6. Construction du contexte (Inclusion des variables qualifiées)
    context = {
        "messages": all_messages,  # Contient désormais les attributs dynamiques .is_json et .is_sql_direct
        "user_messages": user_messages,
        "data_sources": data_sources,
        "agents_list": agents,
        "active_agent": active_agent,
        "date_aujourdhui": aujourdhui.strftime("%Y-%m-%d"),
        "date_hier": hier.strftime("%Y-%m-%d"),
    }

    return render(request, "chat/chat.html", context)


""" Optimiser pour tenir compte des 3 types
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
    
    return render(request, 'chat/chat.html', context) """


def agent_ia_view(request):
    messages = Message_agent_ai.objects.all().order_by("date_creation")
    return render(request, "chat/agent_ia.html", {"messages": messages})


def index(request):
    # articles = Article.objects.order_by('-date_publication','-id')
    return render(request, "chat/chat.html")


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

    # print(f"Structure bdd -> {full_schema_text}")

    return render(
        request,
        "chat/parametre.html",
        {"data_sources": data_sources, "agents": agents, "active_agent": active_agent},
    )


# GErer les agents IA
# 2. Ajouter ou Modifier un agent
def save_agent(request, agent_id=None):
    agent = get_object_or_404(Agent, pk=agent_id) if agent_id else None

    if request.method == "POST":
        name = request.POST.get("name")
        model_name = request.POST.get("model_name")
        api_key = request.POST.get("api_key")
        system_instruction = request.POST.get("system_instruction")
        is_active = request.POST.get("is_active") == "on"

        # Création de l'agent en base de données
        new_agent = Agent.objects.create(
            name=name,
            model_name=model_name,
            api_key=api_key,
            system_instruction=system_instruction,
            is_active=is_active,
        )

        # SÉCURITÉ AJAX : Si la requête vient du script JavaScript (Fetch), on renvoie du JSON
        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest" or "application/json" in request.META.get(
            "HTTP_ACCEPT", ""
        ):
            return JsonResponse(
                {
                    "success": True,
                    "message": "Agent créé avec succès !",
                    "agent_id": new_agent.id,
                    "agent_name": new_agent.name,
                }
            )

        messages.success(request, "Agent créé avec succès")
        # return redirect('agent_manager')
        return redirect("parametre")

    return render(request, "chat/parametre.html", {"agent": agent})


def edit_agent(request, agent_id=None):
    # Si agent_id est fourni -> Modification, sinon -> Création
    agent = get_object_or_404(Agent, pk=agent_id) if agent_id else None

    if request.method == "POST":
        name = request.POST.get("name")
        model_name = request.POST.get("model_name")
        api_key = request.POST.get("api_key")
        system_instruction = request.POST.get("system_instruction")
        is_active = request.POST.get("is_active") == "on"

        if agent:  # Modification
            agent.name = name
            agent.model_name = model_name
            agent.api_key = api_key
            agent.system_instruction = system_instruction
            agent.is_active = is_active
            agent.save()
            messages.success(request, "Agent modifié avec succès")
        else:  # Création
            Agent.objects.create(
                name=name,
                model_name=model_name,
                api_key=api_key,
                system_instruction=system_instruction,
                is_active=is_active,
            )
            messages.success(request, "Agent créé avec succès")
        return redirect("parametre")

    return render(request, "chat/parametre.html", {"agent": agent})


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
    return redirect(
        "parametre"
    )  # Remplacez 'parametre' par le nom réel de votre vue de configuration


# 3. Supprimer un agent
def delete_agent(request, pk):
    """Supprimer un agent de l'I.A."""
    agent = get_object_or_404(Agent, pk=pk)

    if request.method == "POST":
        agent_name = agent.name
        agent.delete()  # La suppression physique en BDD se fait ici

        # SÉCURITÉ ABSOLUE : On renvoie TOUJOURS du JSON si la requête vient de JavaScript (Fetch)
        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest" or "application/json" in request.META.get(
            "HTTP_ACCEPT", ""
        ):
            return JsonResponse(
                {
                    "success": True,
                    "message": f'L\'agent "{agent_name}" a été supprimé avec succès !',
                }
            )

        # Uniquement pour les formulaires HTML standards (si utilisés sans JS)
        return redirect("parametre")

    return redirect("parametre")


# 4. Basculer d'agent actif (Clic rapide)
def toggle_agent(request, agent_id):
    agent = get_object_or_404(Agent, pk=agent_id)
    agent.is_active = True
    agent.save()  # Le save() désactive automatiquement les autres
    # return redirect('agent_manager')
    return redirect("parametre")


def toggle_db_source(request, db_source_id):
    dbSOurce = get_object_or_404(DbSource, pk=db_source_id)
    dbSOurce.is_active = True
    dbSOurce.save()  # Le save() désactive automatiquement les autres
    # return redirect('agent_manager')
    return redirect("parametre")


""" @csrf_exempt  #vEUT OPTIMSIER CAR n'affiche pas en fonction du type
def recherche_naturelle(request):
    if request.method != "POST":
        return JsonResponse({
            "type": "error", 
            "data": "Méthode non autorisée", 
            "agent_name": "Système"
        }, status=405)

    # 1. Extraction et nettoyage de la phrase utilisateur
    phrase_utilisateur = request.POST.get('message', '').strip() or request.POST.get('q', '').strip()
    if not phrase_utilisateur:
        return JsonResponse({
            "type": "error", 
            "data": "La requête reçue est vide.", 
            "agent_name": "Système"
        }, status=400)

    try:
        # 2. Extraction et fusion des schémas de bases de données actifs
        db_active_target = router.db_for_read(DbSource)
        active_dbs = DbSource.objects.using(db_active_target).filter(is_active=True)

        if not active_dbs.exists():
            return JsonResponse({
                "type": "error", 
                "data": "Aucune base de données active dans les paramètres.", 
                "agent_name": "Système"
            }, status=400)

        db_names_list = []
        full_schema_text = ""
        for db in active_dbs:
            full_schema_text += db.get_db_schema() + "\n"
            db_names_list.append(db.name)

        source = active_dbs.first()

        # 3. Enregistrement sécurisé du message utilisateur en base de données
        db_msg = router.db_for_write(Message_Ai)
        try:
            Message_Ai.objects.using(db_msg).create(sender="user", content=phrase_utilisateur)
        except Exception as e:
            logger.error(f"Impossible d'enregistrer le message utilisateur sur db_msg : {e}")

        # 4. Injection et enrichissement du prompt stratégique (JSON Analytique + Insights)
        db_agent_target = router.db_for_read(Agent)
        agent_config = Agent.objects.using(db_agent_target).filter(is_active=True).first()

        instructions_metier = (
            "\n\n[MISE À JOUR DE LA RÈGLE DE SORTIE - FORMATAGE DASHBOARD C-LEVEL & BIG DATA]\n"
            "Par dérogation à la règle de sortie précédente, tu ne dois plus renvoyer le SQL sous forme de texte brut. "
            "Tu dois générer un rapport décisionnel d'infrastructure Big Data.\n"
            "Renvoie STRICTEMENT un objet JSON valide (sans aucun autre texte, introduction ou bloc markdown) structuré ainsi :\n"
            "{\n"
            "  \"sql\": \"La requête SQL SELECT générée en respectant scrupuleusement toutes les directives de mapping ci-dessus.\",\n"
            "  \"visual_type\": \"line_chart\" (si l'utilisateur parle d'évolution, tendance, courbe, chronologie), \"bar_chart\" (si comparaison ou segmentation), ou \"table\" (par défaut),\n"
            "  \"x_axis\": \"Le nom exact de la colonne sélectionnée pour l'axe des abscisses\",\n"
            "  \"y_axis\": \"Le nom exact de la colonne numérique sélectionnée pour l'axe des ordonnées\",\n"
            "  \"ai_insights\": \"Rédige ici l'analyse textuelle basée sur la logique de la requête. Tu dois obligatoirement utiliser ces séparateurs textuels précis :\n"
            "  **Vision & Interprétation :** (Ton analyse contextuelle du résultat)\n"
            "  **Conseils stratégiques :** (Tes recommandations sous forme de liste numérotée)\n"
            "  **Prédictions :** (Les tendances ou événements futurs)\",\n"
            "  \"data_governance\": \"Analyse ici la qualité et la traçabilité des données (ex: fraîcheur, conformité RGPD, gestion des valeurs nulles). Si non applicable, mets null. INTERDICTION D'INVENTER.\",\n"
            "  \"anomalies_alerts\": \"Signale ici tout écart-type suspect, pic ou signal faible que l'exécution de ce SELECT pourrait lever. Si aucun, mets null. INTERDICTION D'INVENTER.\",\n"
            "  \"financial_impact\": \"Si le schéma contient des tables de coûts, budgets ou montants, traduis ce volume en opportunité financière ou ROI. Si le schéma ne contient aucun champ financier, mets STRICTEMENT null. INTERDICTION D'INVENTER.\",\n"
            "  \"elasticity_analysis\": \"Identifie le levier ou facteur clé (What-If) permettant de modifier la trajectoire de cette courbe. Si non applicable, mets null. INTERDICTION D'INVENTER.\",\n"
            "  \"system_efficiency\": \"Donne un diagnostic technique proactif sur la performance de la requête (ex: utilisation d'index, coût CPU estimé, besoin de partitionnement à grande échelle). Ne mets null que si tu manques d'éléments techniques.\"\n"
            "}\n"
            "Si la demande est impossible selon l'Étape C, génère ce JSON : {\"sql\": \"-- IMPOSSIBLE\", \"visual_type\": \"table\", \"x_axis\": null, \"y_axis\": null, \"ai_insights\": null, \"data_governance\": null, \"anomalies_alerts\": null, \"financial_impact\": null, \"elasticity_analysis\": null, \"system_efficiency\": null}"
        )


        if agent_config and agent_config.system_instruction:
            base_prompt = agent_config.system_instruction
            system_instruction_final = base_prompt.replace("{full_schema_text}", full_schema_text) + instructions_metier
        else:
            system_instruction_final = f"Génère le JSON d'analyse demandé pour ce schéma :\n{full_schema_text}{instructions_metier}"

        # 5. Appel et obtention de la réponse de l'agent IA
        chat_result = generate_response(phrase_utilisateur, system_instruction=system_instruction_final)
        status = chat_result.get('status')

        if status in ['error', 'no_agent']:
            return JsonResponse({
                "type": "error", 
                "data": chat_result.get('message', 'Erreur interne de traitement de l\'agent.'), 
                "agent_name": "Système"
            }, status=400 if status == 'no_agent' else 500)

        # Interception des flux de discussion simples (ex: "Bonjour", "Aide-moi")
        if chat_result.get('type') == 'chat':
            return JsonResponse({
                "type": "chat", 
                "data": chat_result.get('text'), 
                "agent_name": chat_result.get('agent_name', 'Assistant')
            })

        # 6. Extraction et parsing sécurisé du JSON de l'agent
        texte_brut = chat_result.get('text', '').strip()
        requete_sql = ""
        visual_type = "table"
        x_axis = None
        y_axis = None
        ai_insights = ""

        try:
            # Nettoyage des backticks markdown accidentels générés par le LLM
            json_propre = re.sub(r'```json\s*|\s*```', '', texte_brut).strip()
            meta_data = json.loads(json_propre)
            
            requete_sql = meta_data.get('sql', '').strip()
            visual_type = meta_data.get('visual_type', 'table')
            x_axis = meta_data.get('x_axis')
            y_axis = meta_data.get('y_axis')
            ai_insights = meta_data.get('ai_insights', '')
        except Exception:
            # Fallback de secours si l'IA enfreint la règle et renvoie du SQL brut textuel
            requete_sql = re.sub(r'```sql\s*|\s*```', '', texte_brut).strip()
            if "impossible" in requete_sql.lower() or "--" in requete_sql:
                requete_sql = "-- IMPOSSIBLE"

        # 7. SÉCURITÉ SQL AVANCÉE (ANTI FAUX POSITIFS & SÉCURISATION INJECTIONS)
        sql_nettoye = requete_sql.strip()

        # Suppression des commentaires (Mono-ligne '--' et Multi-lignes '/* */') pour éviter les faux blocages
        sql_nettoye = re.sub(r'--.*$', '', sql_nettoye, flags=re.MULTILINE)
        sql_nettoye = re.sub(r'/\*.*?\*/', '', sql_nettoye, flags=re.DOTALL)
        sql_nettoye = sql_nettoye.strip()

        # Tolérance du point-virgule final unique généré par l'IA
        if sql_nettoye.endswith(';'):
            sql_nettoye = sql_nettoye[:-1].strip()

        sql_clean_lower = sql_nettoye.lower()

        # Interception immédiate si l'alignement à l'Étape C a échoué (Champs introuvables)
        if "impossible" in sql_clean_lower or not sql_nettoye:
            return JsonResponse({
                "type": "error", 
                "data": "Cette demande est impossible à traduire avec les tables et champs actuels de votre catalogue de données.", 
                "agent_name": "Sécurité"
            }, status=400)

        # Extraction stricte des mots isolés (\b) pour ne pas bloquer les colonnes composites (ex: user_id)
        mots_extraits = set(re.findall(r'\b[a-z_]+\b', sql_clean_lower))
        commandes_interdites = {
            'delete', 'drop', 'truncate', 'alter', 'grant', 
            'insert', 'update', 'create', 'replace'
        }

        # Validation du premier mot de la requête
        mots_de_la_requete = sql_clean_lower.split()
        premier_mot = mots_de_la_requete[0] if mots_de_la_requete else ""

        # Déclenchement de la barrière de sécurité
        if (
            ";" in sql_nettoye  # S'il reste un point-virgule au milieu du texte -> Injection de commandes multiples
            or premier_mot != "select"  # Obligation stricte de lecture seule (SELECT)
            or mots_extraits.intersection(commandes_interdites)  # Présence de commandes destructrices
        ):
            logger.warning(f"Blocage Sécurité - Requête suspecte interceptée : {requete_sql}")
            return JsonResponse({
                "type": "error", 
                "data": "Action non autorisée : Cette méthode accepte exclusivement une unique instruction SELECT.", 
                "agent_name": "Sécurité"
            }, status=403)

        # 8. EXÉCUTION DE LA REQUÊTE SQL SUR LA BASE DISTANTE
        try:
            result = run_query(source, requete_sql)
            limited_result = result[:1000]  # Limite étendue pour les graphiques annuels et exports complets

            # Sérialisation et normalisation des formats complexes pour l'interopérabilité JS
            for row in limited_result:
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):  # Format standard pour les objets Dates/Heures
                        row[key] = value.isoformat()
                    elif hasattr(value, 'to_eng_string'):  # Format float pour les objets Décimaux / Prix
                        row[key] = float(value)

            # Assemblage de la réponse de Dashboard unifiée
            
            # Extraction des indicateurs Big Data avancés
            response_data = {
                "type": "sql_dashboard",
                "visual_type": visual_type,
                "chart_config": {"x_axis": x_axis, "y_axis": y_axis},
                "ai_insights": ai_insights,
                # 🟢 NOUVELLES CLÉS INJECTÉES POUR LE JAVASCRIPT
                "data_governance": meta_data.get('data_governance'),
                "anomalies_alerts": meta_data.get('anomalies_alerts'),
                "financial_impact": meta_data.get('financial_impact'),
                "elasticity_analysis": meta_data.get('elasticity_analysis'),
                "system_efficiency": meta_data.get('system_efficiency'),
                "data": limited_result,
                "count": len(result),
                "sql_genere": requete_sql,
                "dbs_utilisees": ", ".join(db_names_list),
                "agent_name": chat_result.get('agent_name', 'Moteur Décisionnel')
            }
            
            # Enregistrement final du journal d'exécution dans l'historique
            # 2. 🟢 SAUVEGARDE STRUCTURÉE : On convertit tout l'objet en chaîne JSON dans la base
            try:
                with transaction.atomic(using=db_msg):
                    Message_Ai.objects.using(db_msg).create(
                        sender="system", 
                        content=json.dumps(response_data) # Convertit le dictionnaire en texte JSON instanciable
                    )
            except Exception as e:
                logger.error(f"Erreur enregistrement historique SQL complet sur db_msg : {e}")

            return JsonResponse(response_data)

        except utils.OperationalError as e:
            logger.error(f"Erreur d'exécution SQL distante : {str(e)} | Requête concernée : {requete_sql}", exc_info=True)
            return JsonResponse({
                "type": "error",
                "data": f"Erreur de syntaxe ou d'exécution sur le serveur SQL distant. Détail : {str(e)}",
                "sql_genere": requete_sql,
                "agent_name": "Système"
            }, status=400)

    except Exception as e:
        logger.error(f"EXCEPTION GLOBALE CAPTURÉE : {str(e)}", exc_info=True)
        return JsonResponse({
            "type": "error",
            "data": "Une erreur interne imprévue est survenue lors de l'exécution de la recherche.",
            "agent_name": "Système"
        }, status=500) """


@csrf_exempt
def recherche_naturelle(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "type": "error",
                "data": "Méthode non autorisée.",
                "agent_name": "Système",
            },
            status=405,
        )

    # Récupération et assainissement du message
    phrase_utilisateur = (
        request.POST.get("message", "").strip() or request.POST.get("q", "").strip()
    )
    if not phrase_utilisateur:
        return JsonResponse(
            {
                "type": "error",
                "data": "La requête est vide.",
                "agent_name": "Système",
            },
            status=400,
        )

    try:
        # Configuration des bases de données actives
        db_active_target = router.db_for_read(DbSource)
        active_dbs = DbSource.objects.using(db_active_target).filter(is_active=True)

        if not active_dbs.exists():
            return JsonResponse(
                {
                    "type": "error",
                    "data": "Aucune base de données active.",
                    "agent_name": "Système",
                },
                status=400,
            )

        db_names_list = [db.name for db in active_dbs]
        full_schema_text = "".join([db.get_db_schema() + "\n" for db in active_dbs])
        source = active_dbs.first()

        # Enregistrement du message utilisateur
        db_msg = router.db_for_write(Message_Ai)
        try:
            Message_Ai.objects.using(db_msg).create(
                sender="user", content=phrase_utilisateur
            )
        except Exception as e:
            logger.error(f"Erreur écriture message utilisateur : {e}")

        # =========================================================================
        # 🟢 CAS 1 : L'UTILISATEUR A ENVOYÉ UNE REQUÊTE SQL DIRECTE (SANS IA)
        # =========================================================================
        if source and is_sql_query(phrase_utilisateur):
            try:
                # On délègue l'intégralité du nettoyage lourd directement à run_query
                result = run_query(source, phrase_utilisateur)
                print(f"SQL DIRECT Le result --> {result}")
                limited_result = result[:1000]
                print(f"SQL DIRECT Le limited_result --> {limited_result}")

                for row in limited_result:
                    for key, value in row.items():
                        if hasattr(value, "isoformat"):
                            row[key] = value.isoformat()
                        elif hasattr(value, "to_eng_string"):
                            row[key] = float(value)

                response_data = {
                    "type": "sql",
                    "data": limited_result,
                    "count": len(result),
                    "sql_genere": phrase_utilisateur,  # Conserve la saisie pour l'affichage de l'interface
                    "dbs_utilisees": source.name,
                    "agent_name": "Base de données",
                }

                try:
                    Message_Ai.objects.using(db_msg).create(
                        sender="system",
                        content=f"SQL Direct - Exécuté avec succès : {len(limited_result)} lignes trouvées.",
                    )
                except Exception as e:
                    logger.error(f"Erreur journalisation SQL manuel : {e}")

                return JsonResponse(response_data)

            except Exception as e:
                # Capture les PermissionError et OperationalError de run_query
                return JsonResponse(
                    {
                        "type": "error",
                        "data": f"Erreur SQL direct : {str(e)}",
                        "agent_name": "Sécurité",
                    },
                    status=400,
                )
        # =========================================================================
        # CAS 2 & 3 : APPEL ROUTER GENERATE_RESPONSE (PRÉDÉFINIS VS INTELLIGENCE ARTIFICIELLE)
        # =========================================================================
        else:
            # Préparation des instructions analytiques
            instructions_metier = (
                "\n\n[MISE À JOUR CRITIQUE DE LA RÈGLE DE SORTIE - FORMAT JSON AVANCÉ C-LEVEL]\n"
                "Annule et remplace la règle précédente concernant la sortie en texte brut SQL. "
                "Tu dois impérativement analyser la demande de l'utilisateur et renvoyer UNIQUEMENT un objet JSON valide. "
                "Interdiction stricte d'inclure du texte avant ou après, ou d'utiliser des blocs de code markdown (pas de ```json).\n"
                "Structure exacte du JSON à renvoyer :\n"
                "{\n"
                '  "sql": "La requête SQL SELECT générée en respectant scrupuleusement toutes les directives de mapping ci-dessus. Écris-la sur une seule ligne.",\n'
                '  "visual_type": "line_chart",\n'
                '  "x_axis": "nom_colonne_x",\n'
                '  "y_axis": "nom_colonne_y",\n'
                '  "ai_insights": "Rédige une analyse générale de ce que cette requête permet d\'observer. Utilise ces marqueurs : **Vision & Interprétation :** ... **Conseils stratégiques :** ... **Prédictions :** ... Note : Ne simule pas de faux résultats numériques.",\n'
                '  "data_governance": "Note sur la fraîcheur ou la nullabilité des colonnes ciblées, ou null.",\n'
                '  "anomalies_alerts": "Règles métiers à surveiller lors de la lecture des résultats (ex: attention aux doublons), ou null.",\n'
                '  "financial_impact": "Opportunité financière théorique liée à cette analyse, ou null.",\n'
                '  "elasticity_analysis": "Le levier (What-If) théorique modifiable, ou null.",\n'
                '  "system_efficiency": "Diagnostic technique proactif (ex: index requis sur la clé de jointure).",\n'
                '  "divers": {\n'
                '    "analyse_ecart_formule": "Rédige ici la formule logique exacte à appliquer sur l\'application frontend pour calculer le pourcentage de variation entre le mois actuel et le mois précédent (ex: ((CA_M - CA_M_1) / CA_M_1) * 100). Explique les seuils d\'investigation profonde (saisonnalité, marketing).",\n'
                '    "objectifs_mensuels_kpi": "Méthodologie pour comparer le résultat de cette requête SQL face aux objectifs prévisionnels. Indique les critères d\'évaluation des actions correctives si l\'objectif est manqué.",\n'
                '    "benchmarking_sales": "Définition de la règle d\'évaluation (KPI) basée sur cette requête pour juger de la performance brute des équipes de vente et de marketing."\n'
                "  }\n"
                "}\n"
                "Si la demande est impossible (Étape C), génère exactement ce JSON : "
                '{"sql": "-- IMPOSSIBLE", "visual_type": "table", "x_axis": null, "y_axis": null, "ai_insights": null, "data_governance": null, "anomalies_alerts": null, "financial_impact": null, "elasticity_analysis": null, "system_efficiency": null, "divers": {"analyse_ecart_formule": null, "objectifs_mensuels_kpi": null, "benchmarking_sales": null}}'
            )

            db_agent_target = router.db_for_read(Agent)
            agent_config = (
                Agent.objects.using(db_agent_target).filter(is_active=True).first()
            )

            if agent_config and agent_config.system_instruction:
                system_instruction_final = (
                    agent_config.system_instruction.replace(
                        "{full_schema_text}", full_schema_text
                    )
                    + instructions_metier
                )
            else:
                system_instruction_final = f"Génère le JSON d'analyse demandé pour ce schéma :\n{full_schema_text}{instructions_metier}"

            # Appel de votre routeur de réponse unifié
            chat_result = generate_response(
                phrase_utilisateur, system_instruction=system_instruction_final
            )
            print(f"AGENT AI Le chat_result --> {chat_result}")

            status = chat_result.get("status")

            if status in ["error", "no_agent"]:
                return JsonResponse(
                    {
                        "type": "error",
                        "data": chat_result.get(
                            "message", "Erreur de communication de l'agent."
                        ),
                        "agent_name": "Système",
                    },
                    status=400 if status == "no_agent" else 500,
                )

            # 🟢 CAS 2 : LA RÉPONSE DU CHAT EST ISSUE DE LA LISTE "RESPONSES" (TEXTE PRÉDÉFINI)
            if chat_result.get("type") == "chat":
                response_data = {
                    "type": "chat",
                    "data": chat_result.get("text"),
                    "agent_name": chat_result.get("agent_name", "Assistant"),
                }

                # Sauvegarde brute en texte pour l'historique
                try:
                    Message_Ai.objects.using(db_msg).create(
                        sender="system", content=response_data["data"]
                    )
                except Exception as e:
                    logger.error(f"Erreur d'enregistrement historique du chat : {e}")

                return JsonResponse(response_data)

            # 🟢 CAS 3 : L'IA A APPORTÉ UNE RÉPONSE REQUÉRANT UN DASHBOARD ANALYTIQUE COMPLET
            texte_brut = chat_result.get("text", "").strip()
            print(f"CAS 3 LE texte_brut {texte_brut} ")

            try:
                json_propre = re.sub(r"```json\s*|\s*```", "", texte_brut).strip()
                print(f"CAS 3 LE json_propre {json_propre} ")
                meta_data = json.loads(json_propre)
                #requete_sql = meta_data.get("sql", "").strip()
                # 🎯 CORRECTION 1 : Nettoyage immédiat lors de l'extraction JSON
                requete_sql = meta_data.get("sql", "").strip().replace("\\'", "'")
                print(f"1. LE requete_sql {requete_sql} ")
            except Exception:
                # Fallback si l'IA s'est trompée et a écrit du SQL hors JSON
                requete_sql = re.sub(r"```sql\s*|\s*```", "", texte_brut).strip()
                meta_data = {"visual_type": "table"}
            # =========================================================================
            # 🛡️ SÉCURISATION ET EXTRACTION DU BLOC "DIVERS" (ÉVITE LE CRASH PYTHON)
            # =========================================================================
            # On vérifie si la clé 'divers' existe dans meta_data et s'il s'agit bien d'un dictionnaire
            if isinstance(meta_data.get("divers"), dict):
                meta_divers = meta_data.get("divers")
            else:
                meta_divers = {}

            # Nettoyage de sécurité et élimination des faux positifs (commentaires et point-virgule final)
            sql_nettoye = re.sub(r"--.*$", "", requete_sql.strip(), flags=re.MULTILINE)
            sql_nettoye = re.sub(r"/\*.*?\*/", "", sql_nettoye, flags=re.DOTALL).strip()
            print(f"2. LE sql_nettoye {sql_nettoye} ")
            if sql_nettoye.endswith(";"):
                sql_nettoye = sql_nettoye[:-1].strip()

            sql_clean_lower = sql_nettoye.lower()
            print(f"3. LE sql_clean_lower {sql_clean_lower} ")

            if "impossible" in sql_clean_lower or not sql_nettoye:
                return JsonResponse(
                    {
                        "type": "sql_dashboard",
                        "is_impossible": True,
                        "data": "Cette demande fait référence à des tables ou des colonnes absentes du catalogue actif.",
                        "agent_name": "Sécurité",
                    }, #Demande de données impossible à mapper vers le catalogue actif.
                    status=400,
                )


            mots_extraits = set(re.findall(r"\b[a-z_]+\b", sql_clean_lower))
            print(f"4. Les mots extraits sont: {mots_extraits} ")
            commandes_interdites = {
                "delete",
                "drop",
                "truncate",
                "alter",
                "grant",
                "insert",
                "update",
                "create",
                "replace",
            }
            premier_mot = sql_clean_lower.split()[0] if sql_clean_lower.split() else ""

            # 🎯 CORRECTION 1 : Autoriser 'select' OU 'with' comme premier mot
            if premier_mot not in ["select", "with"]:
                return JsonResponse(
                    {
                        "type": "error",
                        "data": "Action bloquée : Seules les requêtes SELECT ou WITH de consultation sont autorisées.",
                        "agent_name": "Sécurité",
                    },
                    status=403,
                )

            # 🎯 CORRECTION 2 : Sécuriser la détection des requêtes multiples (;)
            # On compte les points-virgules restants après avoir retiré le dernier. 
            # S'il en reste un au milieu, c'est une tentative de multi-requête (ex: SELECT... ; DROP...)
            if ";" in sql_nettoye:
                return JsonResponse(
                    {
                        "type": "error",
                        "data": "Action bloquée : L'exécution de requêtes multiples (;) est strictement interdite.",
                        "agent_name": "Sécurité",
                    },
                    status=403,
                )


            # Exécution SQL et construction du Dashboard final
            try:
                # 🎯 CORRECTION 1 : On applique le remplacement forcé des antislashes d'échappement
                sql_final_execution = sql_nettoye.replace("\\'", "'")
                print(f"5. LE sql_final_execution avant run_query --> {sql_final_execution} ")

                #result = run_query(source, requete_sql)
                result = run_query(source, sql_final_execution)
                limited_result = result[:1000]
                print(f"Apres run_query # Le result --> {result}")
                print(f"Apres run_query # Le limited_result --> {limited_result}")
                for row in limited_result:
                    for key, value in row.items():
                        if hasattr(value, "isoformat"):
                            row[key] = value.isoformat()
                        elif hasattr(value, "to_eng_string"):
                            row[key] = float(value)

                response_data = {
                    "type": "sql_dashboard",
                    "visual_type": meta_data.get("visual_type", "table"),
                    "chart_config": {
                        "x_axis": meta_data.get("x_axis"),
                        "y_axis": meta_data.get("y_axis"),
                    },
                    "ai_insights": meta_data.get("ai_insights", ""),
                    "data_governance": meta_data.get("data_governance"),
                    "anomalies_alerts": meta_data.get("anomalies_alerts"),
                    "financial_impact": meta_data.get("financial_impact"),
                    "elasticity_analysis": meta_data.get("elasticity_analysis"),
                    "system_efficiency": meta_data.get("system_efficiency"),
                    
                    # 🆕 Intégration du bloc "divers" nettoyé pour le composant JS
                    "divers": {
                        "analyse_ecart_formule": meta_divers.get(
                            "analyse_ecart_formule"
                        ),
                        "objectifs_mensuels_kpi": meta_divers.get(
                            "objectifs_mensuels_kpi"
                        ),
                        "benchmarking_sales": meta_divers.get("benchmarking_sales"),
                    },
                    "data": limited_result,
                    "count": len(result),
                    "sql_genere": requete_sql,
                    "dbs_utilisees": ", ".join(db_names_list),
                    "agent_name": chat_result.get("agent_name", "Moteur Décisionnel"),
                }
                print(f"AGENT AI Le response_data --> {response_data}")
                print(
                    f"AGENT AI Le response_data --> {json.dumps(response_data, indent=4, ensure_ascii=False)}"
                )
                # Persistance complète du Dashboard structuré sous forme de chaîne JSON
                try:
                    with transaction.atomic(using=db_msg):
                        Message_Ai.objects.using(db_msg).create(
                            sender="system", content=json.dumps(response_data)
                        )
                except Exception as e:
                    logger.error(
                        f"Erreur d'enregistrement historique du Dashboard JSON : {e}"
                    )

                return JsonResponse(response_data)

            except utils.OperationalError as e:
                return JsonResponse(
                    {
                        "type": "error",
                        "data": f"Erreur d'exécution de la requête : {str(e)}",
                        "sql_genere": requete_sql,
                    },
                    status=400,
                )

    except Exception as e:
        logger.error(f"Exception globale capturée : {str(e)}", exc_info=True)
        return JsonResponse(
            {
                "type": "error",
                "data": "Une erreur interne est survenue sur le serveur analytique.",
            },
            status=500,
        )


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
                "agent_name": "Base de données",
            }
            # Sauvegarde du résultat en texte propre
            Message_Ai.objects.create(
                sender="system", content=f"SQL Result: {len(result)} lignes."
            )

        else:
            # generate_response retourne désormais : {"status": "...", "text": "...", "agent_name": "..."}
            chat_result = generate_response(user_msg)

            if chat_result.get("status") == "no_agent":
                response_data = {
                    "type": "no_agent",
                    "data": chat_result.get("message"),
                    "agent_name": "Système",
                }
            elif chat_result.get("status") == "error":
                response_data = {
                    "type": "error",
                    "data": chat_result.get("message"),
                    "agent_name": "Système",
                }
            else:
                response_data = {
                    "type": "chat",
                    "data": chat_result.get(
                        "text"
                    ),  # Extraction du texte brut pour le JS
                    "agent_name": chat_result.get(
                        "agent_name", "Inconnu"
                    ),  # Transmission du nom de l'agent
                }

            # Sauvegarde du texte brut de l'IA en base de données
            Message_Ai.objects.create(sender="system", content=response_data["data"])

        return JsonResponse(response_data)

    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        error_msg = f"Erreur système : {str(e)}"
        Message_Ai.objects.create(sender="system", content=error_msg)

        return JsonResponse(
            {"type": "error", "data": error_msg, "agent_name": "Système"}, status=500
        )
    

def run_query(source, sql):
    print(f"Le SQL recu dans run_query avant tout debut --> {sql}")
    if not sql or not sql.strip():
        raise ValueError("La requête SQL fournie est vide.")

    # =========================================================================
    # 🧹 NETTOYAGE COGNITIF MONO-LIGNE
    # =========================================================================
    sql = sql.replace(r"\'", "'").replace(r'\"', '"')
    
    sql_nettoye = sql
    sql_nettoye = re.sub(r"/\*.*?\*/", " ", sql_nettoye, flags=re.DOTALL)

    tokens_mysql = (
        r"when|else|if|between|and|or|case|then|end|order|group|by|select|"
        r"from|where|asc|desc|in|like|not|null|is|join|on|having|limit|as"
    )
    pattern_mono_ligne = r"--.*?(?=\b(" + tokens_mysql + r")\b|$)"
    sql_nettoye = re.sub(pattern_mono_ligne, " ", sql_nettoye, flags=re.IGNORECASE)
    sql_nettoye = re.sub(r"\s+", " ", sql_nettoye).strip()
    sql_nettoye = re.sub(r";+$", "", sql_nettoye).strip()

    print("\n[DEBUG REQUÊTE NETTOYÉE ENVOYÉE À MYSQL] :")
    print(f"--> {sql_nettoye} <--\n")

    if not sql_nettoye:
        raise ValueError("La requête SQL est devenue vide après le nettoyage.")

    # =========================================================================
    # 🚨 BLINDAGE DE SÉCURITÉ OPTIMISÉ (Gestion des CTE et Sous-requêtes)
    # =========================================================================
    sql_clean_lower = sql_nettoye.lower()
    mots_extraits = set(re.findall(r"\b[a-z_]+\b", sql_clean_lower))

    # Suppression de 'create' et 'replace' de la liste noire s'ils sont dans le corps du texte
    commandes_interdites = {"delete", "drop", "truncate", "alter", "insert", "grant"}

    contient_commande_update = False
    if "update" in mots_extraits:
        # Ignore la fonction native timestampdiff
        sql_sans_timestampdiff = sql_clean_lower.replace("timestampdiff", "")
        if "update" in set(re.findall(r"\b[a-z_]+\b", sql_sans_timestampdiff)):
            contient_commande_update = True

    # Détection fine du premier mot utile (Autorise SELECT et WITH pour les CTE)
    mots_pivots = sql_clean_lower.lstrip("() ").split()
    premier_mot = mots_pivots[0] if mots_pivots else ""
    if premier_mot not in ["select", "with"]:
        raise PermissionError("Action non autorisée : La requête doit débuter par SELECT ou WITH.")

    # Protection contre l'injection de requêtes multiples (Multi-Query Injection) via le point-virgule
    # On valide qu'il n'y a pas d'instruction destructive après un point-virgule interne
    if ";" in sql_nettoye:
        blocs = sql_nettoye.split(";")
        for bloc in blocs[1:]:
            if re.search(r"\b(delete|drop|truncate|alter|insert|update)\b", bloc, re.IGNORECASE):
                raise PermissionError("Action non autorisée : Multi-requêtes malveillantes détectées.")

    if mots_extraits.intersection(commandes_interdites) or contient_commande_update:
        raise PermissionError("Action non autorisée : Seules les requêtes de lecture (SELECT/WITH) sont permises.")

    print(f"Le sql_nettoye --> {sql_nettoye}")
    print(f"Le sql_clean_lower --> {sql_clean_lower}")

    # =========================================================================
    # ⚡ EXÉCUTION DE LA REQUÊTE NATIVE ET SÉRIALISATION PREMIUM
    # =========================================================================
    with open_connection(source) as conn:
        with conn.cursor() as cursor:
            # Sécurité contextuelle : Désactive ONLY_FULL_GROUP_BY pour éviter le crash 1055 sur l'agent
            cursor.execute("SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));")
            
            cursor.execute(sql_nettoye)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

    cleaned_rows = [
        {
            columns[i]: (val.decode("utf-8", errors="ignore") if isinstance(val, bytes) else val)
            for i, val in enumerate(row)
        }
        for row in rows
    ]

    return cleaned_rows


# BON mai refuse les requetes complexes
""" def run_query(source, sql):
    print(f"Le SQL recu dans run_query avant tout debut --> {sql}")
    if not sql or not sql.strip():
        raise ValueError("La requête SQL fournie est vide.")

    # =========================================================================
    # 🧹 NETTOYAGE COGNITIF MONO-LIGNE (DICTIONNAIRE DE MOTS-CLÉS MYSQL ENRICHI)
    # =========================================================================
    sql_nettoye = sql

    # 1. Suppression des blocs de commentaires de style /* ... */
    sql_nettoye = re.sub(r"/\*.*?\*/", " ", sql_nettoye, flags=re.DOTALL)

    # 2. LISTE DES TOKENS ET MOTS-CLÉS SÉCURITÉS MYSQL
    # On intègre absolument tous les pivots syntaxiques qui structurent vos requêtes complexes
    tokens_mysql = (
        r"when|else|if|between|and|or|case|then|end|order|group|by|select|"
        r"from|where|asc|desc|in|like|not|null|is|join|on|having|limit|as"
    )

    # 🟢 REGEX STRATÉGIQUE : Supprime le commentaire '--' mais s'arrête net
    # dès qu'il croise un mot-clé MySQL de la liste ou la fin du message ($)
    pattern_mono_ligne = r"--.*?(?=\b(" + tokens_mysql + r")\b|$)"
    sql_nettoye = re.sub(pattern_mono_ligne, " ", sql_nettoye, flags=re.IGNORECASE)

    # 3. Remplacement des espaces multiples et sauts de lignes par un espace simple
    sql_nettoye = re.sub(r"\s+", " ", sql_nettoye).strip()

    # 4. Nettoyage strict des points-virgules finaux accumulés
    sql_nettoye = re.sub(r";+$", "", sql_nettoye).strip()

    # DÉBOGUAGE EN CONSOLE : Pour valider l'intégrité totale du script compilé
    print("\n[DEBUG REQUÊTE NETTOYÉE ENVOYÉE À MYSQL] :")
    print(f"--> {sql_nettoye} <--\n")

    if not sql_nettoye:
        raise ValueError("La requête SQL est devenue vide après le nettoyage.")

    # =========================================================================
    # 🚨 BLINDAGE DE SÉCURITÉ INTELLIGENT (Tokenization Réelle)
    # =========================================================================
    sql_clean_lower = sql_nettoye.lower()
    mots_extraits = set(re.findall(r"\b[a-z_]+\b", sql_clean_lower))

    commandes_interdites = {
        "delete",
        "drop",
        "truncate",
        "alter",
        "insert",
        "create",
        "grant",
        "replace",
    }

    # Validation du faux positif 'update' dans 'timestampdiff' ou 'datediff'
    contient_commande_update = False
    if "update" in mots_extraits:
        if "timestampdiff" in sql_clean_lower:
            sql_sans_timestampdiff = sql_clean_lower.replace("timestampdiff", "")
            if "update" in set(re.findall(r"\b[a-z_]+\b", sql_sans_timestampdiff)):
                contient_commande_update = True
        else:
            contient_commande_update = True

    premier_mot = sql_clean_lower.lstrip("() ").split()
    premier_mot = premier_mot[0] if premier_mot else ""

    if (
        ";" in sql_nettoye
        or premier_mot != "select"
        or mots_extraits.intersection(commandes_interdites)
        or contient_commande_update
    ):
        raise PermissionError(
            "Action non autorisée : Cette méthode accepte exclusivement une unique instruction SELECT."
        )
    print(f"Le sql_nettoye --> {sql_nettoye}")
    print(f"Le sql_clean_lower --> {sql_clean_lower}")
    # =========================================================================
    # ⚡ EXÉCUTION DE LA REQUÊTE NATIVE ET SÉRIALISATION PREMIUM
    # =========================================================================
    with open_connection(source) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_nettoye)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

    cleaned_rows = [
        {
            columns[i]: (
                val.decode("utf-8", errors="ignore") if isinstance(val, bytes) else val
            )
            for i, val in enumerate(row)
        }
        for row in rows
    ]

    return cleaned_rows """
