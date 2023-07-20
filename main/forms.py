from django import forms


class SignalForm(forms.Form):
    signal = forms.CharField(label="Signal", max_length=256)

    def __init__(self, *args, **kwargs):
        super(SignalForm, self).__init__(*args, **kwargs)
        self.fields["signal"].widget.attrs.update({"class": "form-control"})


class DhDecryptWhiteflagMessageForm(forms.Form):
    message = forms.CharField(label="Message", max_length=256)
    shared_secret = forms.CharField(label="Shared Secret", max_length=256)

    def __init__(self, *args, **kwargs):
        super(DhDecryptWhiteflagMessageForm, self).__init__(*args, **kwargs)
        self.fields["message"].widget.attrs.update({"class": "form-control"})
        self.fields["shared_secret"].widget.attrs.update({"class": "form-control"})
