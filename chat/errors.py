# votre_app/utils.py
import openai

def format_openai_error(e):
    """
    Centralise l'extraction des messages d'erreur OpenAI.
    """
    if isinstance(e, openai.OpenAIError):
        # Récupère le dictionnaire d'erreur s'il existe
        error_details = getattr(e, 'body', {}).get('error', {})
        message = error_details.get('message', str(e))
        code = error_details.get('code', 'api_error')
        
        # Personnalisation des messages courants
        if code == 'insufficient_quota':
            return "⚠️ Quota épuisé. Veuillez recharger votre compte OpenAI."
        if code == 'invalid_api_key':
            return "🔑 Clé API invalide ou expirée."
            
        return f"Erreur OpenAI ({code}): {message}"
    
    # Pour toutes les autres erreurs Python (réseau, base de données)
    return f"Erreur système : {str(e)}"
