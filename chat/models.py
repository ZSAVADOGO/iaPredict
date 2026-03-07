from django.db import models, transaction

# Create your models here.
class Message_agent_ai(models.Model):
    sender_choices = [('user', 'Utilisateur'), ('system', 'Système')]
    
    sender = models.CharField(max_length=10, choices=sender_choices)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"


""" class Response_agent_aI(models.Model):
    keyword = models.CharField(max_length=100, unique=True)
    reply = models.TextField()

    def __str__(self):
        return f"{self.keyword} -> {self.reply}" """



class Message(models.Model):
    sender_choices = [('user', 'Utilisateur'), ('system', 'Système')]
    
    sender = models.CharField(max_length=10, choices=sender_choices)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"


class Response(models.Model):
    keyword = models.CharField(max_length=100, unique=True)
    reply = models.TextField()

    def __str__(self):
        return f"{self.keyword} -> {self.reply}"

class DataSource(models.Model):

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
            DataSource.objects.exclude(pk=self.pk).update(
                is_active=False,
                status="disconnected"
            )

            # Activer celle-ci
            self.is_active = True
            self.status = "connected"
            self.save(update_fields=["is_active", "status"])