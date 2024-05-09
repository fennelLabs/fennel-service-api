from django import forms

from dashboard.models import APIGroup, User


class RegistrationForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    password = forms.CharField(
        label="Password", max_length=100, widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm Password", max_length=100, widget=forms.PasswordInput
    )
    email = forms.EmailField(label="Email", max_length=100)
    first_name = forms.CharField(label="First Name", max_length=100)
    last_name = forms.CharField(label="Last Name", max_length=100)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password != password2:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")

        return email

    def save(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        email = self.cleaned_data.get("email")
        first_name = self.cleaned_data.get("first_name")
        last_name = self.cleaned_data.get("last_name")

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.save()

        return user


class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    password = forms.CharField(
        label="Password", max_length=100, widget=forms.PasswordInput
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username does not exist")

        user = User.objects.get(username=username)

        if not user.check_password(password):
            raise forms.ValidationError("Incorrect password")

        return cleaned_data


class TransferTokenForm(forms.Form):
    amount = forms.IntegerField(label="Amount")

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")

        if amount is None:
            raise forms.ValidationError("Amount is required")

        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")

        return cleaned_data


class TransferTokenToAddressForm(forms.Form):
    recipient = forms.CharField(label="Recipient", max_length=100)
    amount = forms.IntegerField(label="Amount")

    def clean(self):
        cleaned_data = super().clean()
        recipient = cleaned_data.get("recipient")
        amount = cleaned_data.get("amount")

        if recipient is None:
            raise forms.ValidationError("Recipient is required")

        if amount is None:
            raise forms.ValidationError("Amount is required")

        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")

        return cleaned_data


class CreateApiGroupForm(forms.Form):
    group_name = forms.CharField(label="Group Name", max_length=100)

    def clean(self):
        cleaned_data = super().clean()
        group_name = cleaned_data.get("group_name")

        if group_name is None:
            raise forms.ValidationError("Group name is required")

        if APIGroup.objects.filter(name=group_name).exists():
            raise forms.ValidationError("Group name already exists")

        return cleaned_data


class SendAPIGroupRequestForm(forms.Form):
    group_name = forms.ModelChoiceField(
        label="Group Name",
        queryset=APIGroup.objects.all(),
        to_field_name="name",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        group_name = cleaned_data.get("group_name")

        if group_name is None:
            raise forms.ValidationError("Group name is required")

        if not APIGroup.objects.filter(name=group_name).exists():
            raise forms.ValidationError("Group name does not exist")

        return cleaned_data


class ImportWalletForm(forms.Form):
    mnemonic = forms.CharField(label="Mnemonic", max_length=250)

    def clean(self):
        cleaned_data = super().clean()
        mnemonic = cleaned_data.get("mnemonic")

        if mnemonic is None:
            raise forms.ValidationError("Mnemonic is required")

        return cleaned_data