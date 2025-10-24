from django.contrib import admin

from .models import (
    APIGroup,
    ConfirmationRecord,
    Signal,
    Transaction,
    UserKeys,
    WhiteflagAuthentication,
)


@admin.register(WhiteflagAuthentication)
class WhiteflagAuthenticationAdmin(admin.ModelAdmin):
    """
    Django admin interface for Whiteflag A(0) authentication records.
    
    Per Whiteflag spec 5.1.1: "Each account should be identified by sending 
    an A(0) initial authentication message, before sending any other message."
    """
    list_display = [
        'user',
        'verification_method',
        'verification_data_preview',
        'timestamp',
        'is_active',
        'has_transaction_hash',
    ]
    list_filter = [
        'verification_method',
        'is_active',
        'timestamp',
    ]
    search_fields = [
        'user__username',
        'user__email',
        'verification_data',
        'transaction_hash',
    ]
    readonly_fields = [
        'user',
        'verification_method',
        'verification_data',
        'transaction_hash',
        'timestamp',
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Authentication Details', {
            'fields': (
                'verification_method',
                'verification_data',
                'transaction_hash',
            ),
            'description': 'Method 1 = URL Validation, Method 2 = Shared Token'
        }),
        ('Status', {
            'fields': ('is_active', 'timestamp'),
            'description': 'is_active is set to False when A(4) discontinuation is sent'
        }),
    )
    
    def verification_data_preview(self, obj):
        """Show shortened verification data in list view"""
        if len(obj.verification_data) > 50:
            return obj.verification_data[:47] + "..."
        return obj.verification_data
    verification_data_preview.short_description = "Verification Data"
    
    def has_transaction_hash(self, obj):
        """Show if transaction hash exists"""
        return bool(obj.transaction_hash)
    has_transaction_hash.boolean = True
    has_transaction_hash.short_description = "TX Hash"
    
    def has_add_permission(self, request):
        """Prevent manual creation - should only be created via API"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - keep for audit trail"""
        return False


admin.site.register(APIGroup)
admin.site.register(ConfirmationRecord)
admin.site.register(Signal)
admin.site.register(Transaction)
admin.site.register(UserKeys)
