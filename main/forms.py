from django import forms

from main.models import APIGroup


class APIGroupForm(forms.Form):
    api_group_name = forms.CharField(label="API Group Name", max_length=1024)
    email = forms.EmailField(label="Email", max_length=1024)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["api_group_name"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})


class SignalForm(forms.Form):
    signal = forms.CharField(label="Signal", max_length=1024)
    recipient_group = forms.CharField(
        label="Recipient Group", max_length=1024, required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["signal"].widget.attrs.update({"class": "form-control"})
        self.fields["recipient_group"].widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned_data = super().clean()

        recipient_group = cleaned_data.get("recipient_group", None)
        if (
            recipient_group
            and not APIGroup.objects.filter(name=recipient_group).exists()
        ):
            raise forms.ValidationError("Recipient Group does not exist")


class DhEncryptWhiteflagMessageForm(forms.Form):
    message = forms.CharField(label="Message", max_length=1024)
    shared_secret = forms.CharField(label="Shared Secret", max_length=1024)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs.update({"class": "form-control"})
        self.fields["shared_secret"].widget.attrs.update({"class": "form-control"})


class DhDecryptWhiteflagMessageForm(forms.Form):
    message = forms.CharField(label="Message", max_length=1024)
    shared_secret = forms.CharField(label="Shared Secret", max_length=1024)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs.update({"class": "form-control"})
        self.fields["shared_secret"].widget.attrs.update({"class": "form-control"})


class PrivateMessageForm(forms.Form):
    receiver = forms.CharField(label="Receiver", max_length=1024)
    message = forms.CharField(label="Message", max_length=1024)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["receiver"].widget.attrs.update({"class": "form-control"})
        self.fields["message"].widget.attrs.update({"class": "form-control"})


class WhiteflagDecodeForm(forms.Form):
    message = forms.CharField(label="Message", max_length=1024)
    sender_group = forms.CharField(
        label="Sender Group", max_length=1024, required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs.update({"class": "form-control"})
        self.fields["sender_group"].widget.attrs.update({"class": "form-control"})
