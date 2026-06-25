import pymysql
import psycopg2
from django.db import models, transaction



class Agent(models.Model):
    """MODEL_CHOICES = [
        ('gemini-2.5-flash', 'Gemini 2.5 Flash (Rapide)'),
        ('gemini-2.5-pro', 'Gemini 2.5 Pro (Avancé)'),
    ] """

    name = models.CharField(max_length=50, verbose_name="Nom de l'Agent")
    model_name = models.CharField(max_length=50, default='gemini-2.5-flash')
    api_key = models.TextField(max_length=1000, help_text="La clée de l'API", default="")
    system_instruction = models.TextField(blank=True,  help_text="Instructions de rôle (ex: Tu es un expert en Python)")
    is_active = models.BooleanField(default=False, help_text="Cochez pour définir comme agent par défaut")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Optionnel : Méthode pour récupérer la date directement formatée en FR
    def date_creation_fr(self):
        return self.date_creation.strftime('%d/%m/%Y à %H:%M:%S')
        

    def save(self, *args, **kwargs):
        # Si cet agent est activé, on désactive automatiquement tous les autres
        if self.is_active:
            Agent.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.model_name})"
    


# Create your models here.
class Message_agent_ai(models.Model):
    sender_choices = [('user', 'Utilisateur'), ('system', 'Système')]
    
    sender = models.CharField(max_length=10, choices=sender_choices)
    content = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"



class Message_Ai(models.Model):
    sender_choices = [('user', 'Utilisateur'), ('system', 'Système')]
    
    sender = models.CharField(max_length=10, choices=sender_choices)
    content = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"


class Response_Ai(models.Model):
    keyword = models.CharField(max_length=100, unique=True)
    reply = models.TextField()

    def __str__(self):
        return f"{self.keyword} -> {self.reply}"

class DbSource(models.Model):

    STATUS_CHOICES = [
        ('connected', 'Connectée'),
        ('error', 'Erreur'),
        ('disconnected', 'Non connectée'),
    ]
  
    DB_TYPES = [
        ('mysql', 'MySQL'),
        ('postgres', 'PostgreSQL'),
    ]

    name = models.CharField(max_length=100)
    db_type = models.CharField(max_length=20, choices=DB_TYPES)

    host = models.CharField(max_length=100)
    port = models.IntegerField()
    database_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,  
        choices=STATUS_CHOICES, 
        default="disconnected")  # connected / error
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.date_creation.strftime('%d/%m/%Y à %H:%M:%S')}] {self.name.upper()} - {self.db_type.upper()} ({self.host})"


    def masked_password(self):
        return "•" * 8
    

    def disconnect(self):
        self.status = "disconnected"
        self.is_active = False
        self.save()


    def check_connection(self):
        """Tente une connexion réelle à la base de données selon son type."""
        try:
            if self.db_type == 'mysql':
                conn = pymysql.connect(
                    host=self.host,
                    port=int(self.port),
                    user=self.username,
                    password=self.password,
                    database=self.database_name,
                    connect_timeout=5
                )
                conn.close()
            elif self.db_type == 'postgres':
                conn = psycopg2.connect(
                    host=self.host,
                    port=int(self.port),
                    user=self.username,
                    password=self.password,
                    dbname=self.database_name,
                    connect_timeout=5
                )
                conn.close()
            return True, "Connexion réussie"
        except Exception as e:
            return False, str(e)

    # 🟢 NOUVELLE MÉTHODE pour avoir la stuctures de la bdd
    def get_db_schema(self): 
        """Se connecte à cette source et extrait son schéma formaté pour l'IA."""
        schema_text = f"--- SCHEMA BASE DE DONNEES : {self.name} ({self.db_type.upper()}) ---\n\n"
        
        try:
            if self.db_type == 'mysql':
                conn = pymysql.connect(
                    host=self.host, port=int(self.port), user=self.username,
                    password=self.password, database=self.database_name, connect_timeout=5
                )
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                # Extraction ultra-rapide via Information Schema
                query = """
                    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME, ORDINAL_POSITION;
                """
                cursor.execute(query, (self.database_name,))
                rows = cursor.fetchall()
                cursor.close()
                conn.close()

            elif self.db_type == 'postgres':
                conn = psycopg2.connect(
                    host=self.host, port=int(self.port), user=self.username,
                    password=self.password, dbname=self.database_name, connect_timeout=5
                )
                cursor = conn.cursor()
                query = """
                    SELECT table_name, column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position;
                """
                cursor.execute(query)
                # Standardisation du format des lignes
                rows = [{"TABLE_NAME": r[0], "COLUMN_NAME": r[1], "DATA_TYPE": r[2]} for r in cursor.fetchall()]
                cursor.close()
                conn.close()
            else:
                return "Type de base de données inconnu."

            if not rows:
                return f"La base de données '{self.database_name}' est vide."

            # Structuration par table
            tables_dict = {}
            for row in rows:
                t_name = row.get("TABLE_NAME") or row.get("table_name")
                c_name = row.get("COLUMN_NAME") or row.get("column_name")
                d_type = row.get("DATA_TYPE") or row.get("data_type")
                
                if t_name not in tables_dict:
                    tables_dict[t_name] = []
                tables_dict[t_name].append(f"{c_name} ({d_type})")

            # Génération du texte final
            for table_name, columns in tables_dict.items():
                schema_text += f"- Table: \"{table_name}\"\n"
                schema_text += "  Champs: (" + ", ".join(columns) + ")\n\n"

            return schema_text

        except Exception as e:
            return f"Impossible de lire le schéma pour {self.name} : {str(e)}"

    def toggle_activation(self, status="connected"):
        """Active ou change le statut de cette source sans impacter les autres."""
        self.is_active = (status == "connected")
        self.status = status
        self.save(update_fields=["is_active", "status"])

class AiApiLog(models.Model):
    # Choix des fournisseurs pour forcer la cohérence des données
    PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI'),
        ('claude', 'Anthropic Claude'),
        ('system', 'Système Interne'),
    ]

    # Choix de l'état final de la requête
    STATUS_CHOICES = [
        ('success', 'Succès'),
        ('error', 'Erreur'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, verbose_name="Fournisseur")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Statut")
    
    # Stockage du code HTTP (ex: 200, 429, 503) ou du code d'erreur textuel (ex: RESOURCE_EXHAUSTED)
    status_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Code d'erreur/Retour")
    
    # Données échangées (Utile pour le débogage)
    prompt_sent = models.TextField(verbose_name="Prompt envoyé")
    response_received = models.TextField(blank=True, null=True, verbose_name="Réponse brute ou JSON d'erreur")
    
    # Métriques (Optionnel, mais très utile pour suivre vos coûts et performances)
    tokens_used = models.IntegerField(default=0, verbose_name="Tokens totaux")
    execution_time = models.FloatField(default=0.0, verbose_name="Temps d'exécution (secondes)")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'appel")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Log API IA"
        verbose_name_plural = "Logs API IA"

    def __str__(self):
        return f"[{self.created_at.strftime('%d/%m/%Y à %H:%M:%S')}] {self.provider.upper()} - {self.status.upper()} ({self.status_code})"
    



"""     def activate(self, status="connected"):
        #Désactive les autres et active celle-ci avec le statut choisi.
        with transaction.atomic():
            # Désactiver toutes les autres sources
            DbSource.objects.exclude(pk=self.pk).update(
                is_active=False,
                status="disconnected"
            )

            # Activer celle-ci avec le statut résultant du test
            self.is_active = (status == "connected")
            self.status = status
            self.save(update_fields=["is_active", "status"]) """