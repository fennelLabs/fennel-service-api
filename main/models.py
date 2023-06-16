from django.db import models

class Signal(models.Model):
    signal_text = models.CharField(max_length=256)
    timestamp = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey('auth.User', related_name='signals', on_delete=models.CASCADE, null=True, blank=True)
    synced = models.BooleanField(default=False)

    def __str__(self):
        return self.signal_text


class UserKeys(models.Model):
    user = models.ForeignKey('auth.User', related_name='keys', on_delete=models.CASCADE)
    mnemonic = models.CharField(max_length=256)

    def __str__(self):
        return self.user