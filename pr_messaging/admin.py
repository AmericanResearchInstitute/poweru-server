from django.contrib import admin
from .models import *

class MessageFormatAdmin(admin.ModelAdmin):
    pass

admin.site.register(MessageFormat, MessageFormatAdmin)

class MessageTemplateInline(admin.TabularInline):
    model = MessageTemplate

class MessageTypeAdmin(admin.ModelAdmin):
    inlines = [MessageTemplateInline]

admin.site.register(MessageType, MessageTypeAdmin)

class MessageTemplateAdmin(admin.ModelAdmin):
    pass

admin.site.register(MessageTemplate, MessageTemplateAdmin)
