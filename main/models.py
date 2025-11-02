from django.db import models

from django.contrib.auth import get_user_model


User = get_user_model()


class WhiteflagAuthentication(models.Model):
    """
    Tracks Whiteflag A(0) initial authentication messages per user.
    Per Whiteflag spec 5.1.1: Each account should send A(0) before other messages.
    
    Note: Changed from OneToOneField to ForeignKey to allow multiple authentications
    per user (e.g., key rotation, re-authentication after A(4) discontinuation).
    """
    user = models.ForeignKey(
        "auth.User",
        related_name="whiteflag_authentications",  # Note: plural
        on_delete=models.CASCADE
    )
    verification_method = models.CharField(
        max_length=1,
        choices=[("1", "URL Validation"), ("2", "Shared Token")],
        help_text="1=URL validation (Method 1), 2=Shared token (Method 2)"
    )
    verification_data = models.CharField(
        max_length=4096,
        help_text="URL for Method 1, or HKDF-derived token for Method 2"
    )
    ecdh_public_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Curve25519 public key (64 hex chars) if using ECDH for Method 2"
    )
    ecdh_counterpart = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Username of ECDH counterpart for peer-to-peer authentication"
    )
    ecdh_counterpart_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Counterpart's public key used in ECDH derivation"
    )
    transaction_hash = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Blockchain transaction hash of A(0) message"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False if A(4) discontinuation sent"
    )
    
    class Meta:
        verbose_name = "Whiteflag Authentication"
        verbose_name_plural = "Whiteflag Authentications"
        ordering = ['-timestamp']  # Most recent first
    
    def __str__(self):
        return f"{self.user.username} - Method {self.verification_method} - {'Active' if self.is_active else 'Discontinued'} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class TokenRequest(models.Model):
    """
    Tracks user requests for tokens to submit A(0) authentications.
    Admins (is_staff=True or is_superuser=True) can view and fulfill these requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('fulfilled', 'Fulfilled'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        "auth.User",
        related_name="token_requests",
        on_delete=models.CASCADE,
        help_text="User requesting tokens"
    )
    blockchain_address = models.CharField(
        max_length=256,
        help_text="User's blockchain address where tokens should be sent"
    )
    requested_amount = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        default=10.0,
        help_text="Amount of tokens requested (default: 10.0)"
    )
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Optional reason for token request"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the request"
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the request was submitted"
    )
    fulfilled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was fulfilled/rejected"
    )
    fulfilled_by = models.ForeignKey(
        "auth.User",
        related_name="fulfilled_token_requests",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Admin who fulfilled/rejected the request"
    )
    transaction_hash = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Blockchain transaction hash of token transfer"
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Admin notes about this request"
    )
    
    class Meta:
        verbose_name = "Token Request"
        verbose_name_plural = "Token Requests"
        ordering = ['-requested_at']  # Most recent first
        indexes = [
            models.Index(fields=['status', '-requested_at']),  # For admin dashboard queries
            models.Index(fields=['user', '-requested_at']),  # For user history
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.requested_amount} tokens - {self.status} ({self.requested_at.strftime('%Y-%m-%d %H:%M')})"


class APIGroup(models.Model):
    name = models.CharField(max_length=1024, unique=True)
    email = models.EmailField(max_length=1024)
    user_list = models.ManyToManyField("auth.User", related_name="api_group_users")
    admin_list = models.ManyToManyField("auth.User", related_name="api_group_admins")
    active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=1024, unique=True, null=True, blank=True)
    api_secret = models.CharField(max_length=1024, unique=True, null=True, blank=True)
    request_counter = models.IntegerField(default=0)
    public_diffie_hellman_key = models.CharField(max_length=1024, null=True, blank=True)
    private_diffie_hellman_key = models.CharField(
        max_length=1024, null=True, blank=True
    )

    def __str__(self):
        return str(self.name)


class APIGroupJoinRequest(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    api_group = models.ForeignKey("APIGroup", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user) + " wants to join " + str(self.api_group)


class Transaction(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    function = models.CharField(max_length=1024)
    payload_size = models.IntegerField(default=0)
    fee = models.CharField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return self.function + " " + str(self.timestamp)


class Signal(models.Model):
    tx_hash = models.CharField(max_length=1024, unique=True, null=True, blank=True)
    signal_text = models.CharField(max_length=1024)
    message_code = models.CharField(max_length=2, null=True, blank=True)
    pseudo_message_code = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        help_text='For test messages (T), stores the original message code being tested'
    )
    subject_code = models.CharField(max_length=2, null=True, blank=True)
    signal_body = models.CharField(max_length=4096, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    mempool_timestamp = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    sender = models.ForeignKey(
        "auth.User",
        related_name="signals",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    synced = models.BooleanField(default=False)
    references = models.ManyToManyField(
        "self", symmetrical=False, related_name="referenced_by", blank=True
    )
    viewers = models.ManyToManyField(
        "APIGroup", related_name="viewable_signals", blank=True
    )
    active = models.BooleanField(default=True)
    
    # Blockchain indexing fields
    block_number = models.BigIntegerField(null=True, blank=True, db_index=True)
    block_hash = models.CharField(max_length=66, null=True, blank=True)
    extrinsic_index = models.IntegerField(null=True, blank=True)
    finalized = models.BooleanField(default=False, db_index=True)
    execution_success = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return str(self.signal_text)


class ConfirmationRecord(models.Model):
    signal = models.ForeignKey(
        "Signal", related_name="confirmations", on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    confirmer = models.ForeignKey(
        "auth.User",
        related_name="confirmations",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("signal", "confirmer")


class UserKeys(models.Model):
    user = models.OneToOneField(
        "auth.User", related_name="keys", on_delete=models.CASCADE
    )
    mnemonic = models.CharField(max_length=1024)
    key_shard = models.CharField(max_length=1024, null=True, blank=True)
    blockchain_public_key = models.CharField(max_length=1024, null=True, blank=True)
    address = models.CharField(max_length=1024, null=True, blank=True, unique=True)
    balance = models.CharField(max_length=1024, null=True, blank=True)
    public_diffie_hellman_key = models.CharField(max_length=1024, null=True, blank=True)
    private_diffie_hellman_key = models.CharField(
        max_length=1024, null=True, blank=True
    )
    # Whiteflag RFC 5639 brainpoolP256r1 ECDH keys for authentication
    public_brainpool_key = models.CharField(max_length=1024, null=True, blank=True)
    private_brainpool_key = models.CharField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return self.user.username


class PrivateMessage(models.Model):
    sender = models.ForeignKey(
        "auth.User",
        related_name="private_messages_sent",
        on_delete=models.CASCADE,
    )
    receiver = models.ForeignKey(
        "auth.User",
        related_name="private_messages_received",
        on_delete=models.CASCADE,
    )
    message = models.CharField(max_length=4096)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return str(self.message)


class TrustConnection(models.Model):
    user = models.ForeignKey(
        "auth.User",
        related_name="trust_connections",
        on_delete=models.CASCADE,
    )
    trusted_user = models.ForeignKey(
        "auth.User",
        related_name="trusted_by",
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user + " trusts " + self.trusted_user


class Confirmation(models.Model):
    """
    Tracks A(6) confirmation messages sent between users.
    Per Whiteflag spec: Users can confirm each other's authentication.
    """
    confirmer = models.ForeignKey(
        "auth.User",
        related_name="confirmations_sent",
        on_delete=models.CASCADE,
        help_text="User who sent the confirmation"
    )
    target_user = models.ForeignKey(
        "auth.User",
        related_name="confirmations_received",
        on_delete=models.CASCADE,
        help_text="User who received the confirmation"
    )
    target_authentication = models.ForeignKey(
        WhiteflagAuthentication,
        related_name="confirmations",
        on_delete=models.CASCADE,
        help_text="The authentication being confirmed"
    )
    confirmation_type = models.CharField(
        max_length=1,
        default="6",
        help_text="Confirmation type (6=Confirm per Whiteflag spec)"
    )
    transaction_hash = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Blockchain transaction hash of A(6) message"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Whiteflag Confirmation"
        verbose_name_plural = "Whiteflag Confirmations"
        ordering = ['-timestamp']
        unique_together = ("confirmer", "target_authentication")
    
    def __str__(self):
        return f"{self.confirmer.username} confirms {self.target_user.username}'s auth"


class TrustRequest(models.Model):
    user = models.ForeignKey(
        "auth.User",
        related_name="trust_requests",
        on_delete=models.CASCADE,
    )
    trusted_user = models.ForeignKey(
        "auth.User",
        related_name="trust_requests_received",
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
