from django import forms


class SignalForm(forms.Form):
    signal = forms.CharField(label="Signal", max_length=256)

    def __init__(self, *args, **kwargs):
        super(SignalForm, self).__init__(*args, **kwargs)
        self.fields["signal"].widget.attrs.update({"class": "form-control"})
