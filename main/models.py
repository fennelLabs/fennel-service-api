from django.db import models


class APIGroup(models.Model):
    name = models.CharField(max_length=1024, unique=True)
    user_list = models.ManyToManyField("auth.User", related_name="api_group_users")
    admin_list = models.ManyToManyField("auth.User", related_name="api_group_admins")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    function = models.CharField(max_length=1024)
    payload_size = models.IntegerField(default=0)
    fee = models.IntegerField(default=0)

    def __str__(self):
        return self.tx_hash


class Signal(models.Model):
    tx_hash = models.CharField(max_length=1024, unique=True, null=True, blank=True)
    signal_text = models.CharField(max_length=1024)
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

    def __str__(self):
        return self.signal_text


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
    address = models.CharField(max_length=1024, null=True, blank=True, unique=True)
    balance = models.IntegerField(default=0)
    public_diffie_hellman_key = models.CharField(max_length=1024, null=True, blank=True)
    private_diffie_hellman_key = models.CharField(
        max_length=1024, null=True, blank=True
    )

    def __str__(self):
        return self.user
