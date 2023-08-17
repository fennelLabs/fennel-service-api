from django import forms


class APIGroupForm(forms.Form):
    api_group_name = forms.CharField(label="API Group Name", max_length=1024)
    email = forms.EmailField(label="Email", max_length=1024)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["api_group_name"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})


class SignalForm(forms.Form):
    signal = forms.CharField(label="Signal", max_length=1024)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["signal"].widget.attrs.update({"class": "form-control"})


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
