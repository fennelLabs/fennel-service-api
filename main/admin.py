from django.contrib import admin

from .models import APIGroup, ConfirmationRecord, Signal, Transaction

admin.site.register(APIGroup)
admin.site.register(ConfirmationRecord)
admin.site.register(Signal)
admin.site.register(Transaction)
