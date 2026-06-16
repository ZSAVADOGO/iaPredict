from django.db import models, transaction


class Agent(models.Model):
    MODEL_CHOICES = [
        ('gemini-2.5-flash', 'Gemini 2.5 Flash (Rapide)'),
        ('gemini-2.5-pro', 'Gemini 2.5 Pro (Avancé)'),
    ]

    name = models.CharField(max_length=50, verbose_name="Nom de l'Agent")
    #model_name = models.CharField(max_length=50, choices=MODEL_CHOICES, default='gemini-2.5-flash')
    model_name = models.CharField(max_length=50, default='gemini-2.5-flash')
    api_key = models.TextField(max_length=1000, help_text="La clée de l'API", default="")
    system_instruction = models.TextField(blank=True,  help_text="Instructions de rôle (ex: Tu es un expert en Python)")
    is_active = models.BooleanField(default=False, help_text="Cochez pour définir comme agent par défaut")

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
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"



class Message_Ai(models.Model):
    sender_choices = [('user', 'Utilisateur'), ('system', 'Système')]
    
    sender = models.CharField(max_length=10, choices=sender_choices)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

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

    status = models.CharField(
        max_length=20,  
        choices=STATUS_CHOICES, 
        default="disconnected")  # connected / error
    is_active = models.BooleanField(default=False)

    def masked_password(self):
        return "•" * 8
    

    def disconnect(self):
        self.status = "disconnected"
        self.is_active = False
        self.save()
    
    def activate(self):
        with transaction.atomic():
            # Désactiver toutes les autres
            DbSource.objects.exclude(pk=self.pk).update(
                is_active=False,
                status="disconnected"
            )

            # Activer celle-ci
            self.is_active = True
            self.status = "connected"
            self.save(update_fields=["is_active", "status"])