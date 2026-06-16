#------------------- Configuration de l'API OpenAI ------------------#
import os

from openai import OpenAI
from google import genai

from google.genai.errors import APIError # Import de l'erreur spécifique du SDK
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from dotenv import load_dotenv

from chat.models import Agent

# 1. On charge le fichier .env
load_dotenv() 
# 2. On récupère la clé manuellement
api_key_env = os.getenv("OPENAI_API_KEY")
# 3. On passe la clé explicitement au client
# Initialisation du client (Assurez-vous que votre clé est dans vos variables d'environnement)
client = OpenAI(api_key=api_key_env)

#------------------- Fin de la configuration de l'API OpenAI ------------------#

# Configuration du mécanisme de tentative automatique
@retry(
    # Recommence uniquement si c'est une erreur d'API (comme la 503)
    retry=retry_if_exception_type(APIError), 
    # S'arrête après 3 essais infructueux
    stop=stop_after_attempt(3), 
    # Attend 2s, puis 4s entre les tentatives (laisse le serveur respirer)
    wait=wait_exponential(multiplier=1, min=2, max=10) 
)

def generate_gemini_response_OLD(user_message):
    # 1. Initialisation du client GenAI
    client = genai.Client()
    
    # 2. Appel au modèle Gemini
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_message,
    )
    print(response.text)
    # 3. Retour du texte brut obtenu
    return response.text 


def generate_gemini_response(user_message):
    client = genai.Client()
    
    # 1. On cherche l'agent actif sélectionné par l'utilisateur
    active_agent = Agent.objects.filter(is_active=True).first()
    
    # Sécurités de secours au cas où aucun agent n'est coché actif
    selected_model = active_agent.model_name if active_agent else 'gemini-2.5-flash'
    system_prompt = active_agent.system_instruction if active_agent else "Tu es un assistant utile."
    
    # 2. Appel au modèle avec la configuration de l'agent
    response = client.models.generate_content(
        model=selected_model,
        contents=user_message,
        # Ajout du rôle de l'agent via la configuration de l'API Gemini
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )
    return response.text

#------------------- Fin de la configuration de l'API Google Gemini ------------------#



RESPONSES = {
    "bonjour": "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
    "aide": "Vous pouvez me poser des questions sur votre compte ou vos tâches.",
    "merci": "Avec plaisir !",
}


def generate_response(message):
    msg = message.lower()
    for key in RESPONSES:
        if key in msg:
            # Retourne un dictionnaire pour garder une structure cohérente
            return {"status": "success", "text": RESPONSES[key], "agent_name": "Système"}
            
    try:
        # Appel à l'IA
        ai_reply, agent_name = generate_ai_response(message)
        return {
            "status": "success", 
            "text": ai_reply, 
            "agent_name": agent_name
        }
        
    except ValueError as e:
        # Capture l'erreur spécifique de l'agent manquant
        return {"status": "no_agent", "message": str(e)}
        
    except Exception as e:
        return {"status": "error", "message": f"Erreur Ai : {str(e)}"}


def generate_ai_response(user_message):
    client = genai.Client()
    
    # 1. On cherche l'agent actif sélectionné par l'utilisateur
    active_agent = Agent.objects.filter(is_active=True).first()
    
    # Force l'erreur si aucun agent n'est coché actif
    if not active_agent:
        raise ValueError("Aucun agent n'est sélectionné. Veuillez en activer un.")
    
    selected_model = active_agent.model_name
    system_prompt = active_agent.system_instruction
    
    # 2. Appel au modèle avec la configuration de l'agent
    response = client.models.generate_content(
        model=selected_model,
        contents=user_message,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )
    # On retourne la réponse ET le nom de l'agent (ex: active_agent.name)
    return response.text, active_agent.name 


# Bon mais veut optimiser
""" def generate_response(message):
    msg = message.lower()
    for key in RESPONSES:
        if key in msg:
            return RESPONSES[key]
     # 2. Appel à l'IA
    try:
        #ai_reply = generate_ai_response(message)
        ai_reply = generate_gemini_response(message)
        return ai_reply # Retourne la réponse de l'IA en cas de succès
        
    except Exception as e:
        # On extrait le message d'erreur (ex: "You exceeded your current quota")
        error_message = str(e)
# Si après 3 essais le serveur est toujours indisponible, on gère l'erreur
        # On retourne l'erreur pour qu'elle soit affichée dans le chat
        return f"Erreur Ai : {error_message}"  
    

def generate_ai_response(user_input):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Utilisation de la méthode standard (chat.completions)
        response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[{"role": "user", "content": user_input}]
            )
        print(f"DEBUG: response de l'API -> {response}")  # Debug pour vérifier la réponse de l'API
        ai_response = response.choices[0].message.content
        print(f"DEBUG: ai_response extrait -> {ai_response}")
        
        return ai_response"""



