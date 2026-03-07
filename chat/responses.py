#------------------- Configuration de l'API OpenAI ------------------#
import os

from openai import OpenAI

from dotenv import load_dotenv

# 1. On charge le fichier .env
load_dotenv() 
# 2. On récupère la clé manuellement
api_key_env = os.getenv("OPENAI_API_KEY")
# 3. On passe la clé explicitement au client
# Initialisation du client (Assurez-vous que votre clé est dans vos variables d'environnement)
client = OpenAI(api_key=api_key_env)

#------------------- Fin de la configuration de l'API OpenAI ------------------#



RESPONSES = {
    "bonjour": "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
    "aide": "Vous pouvez me poser des questions sur votre compte ou vos tâches.",
    "merci": "Avec plaisir !",
}

def generate_response(message):
    msg = message.lower()
    for key in RESPONSES:
        if key in msg:
            return RESPONSES[key]
     # 2. Appel à l'IA
    try:
        ai_reply = generate_ai_response(message)
        return ai_reply # Retourne la réponse de l'IA en cas de succès
        
    except Exception as e:
        # On extrait le message d'erreur (ex: "You exceeded your current quota")
        error_message = str(e)
        #print(f"Erreur service IA: {error_message}")
        
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
        
        return ai_response
