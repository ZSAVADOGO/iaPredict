from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Message_Ai, Response_Ai

@admin.register(Response_Ai)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'reply')
    search_fields = ('keyword', 'reply')

@admin.register(Message_Ai)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'content', 'timestamp')
    list_filter = ('sender', 'timestamp')
