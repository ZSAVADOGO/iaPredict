from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Message, Response

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'reply')
    search_fields = ('keyword', 'reply')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'content', 'timestamp')
    list_filter = ('sender', 'timestamp')
