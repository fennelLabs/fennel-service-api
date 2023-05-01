from django.db import models

class Signal(models.Model):
    signal_text = models.CharField(max_length=256)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.signal_text