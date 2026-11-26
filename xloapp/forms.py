from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import Compra, Item, Utilizador


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['nome', 'preco', 'descricao', 'categoria_sub']

    fotos = forms.CharField(label='Fotos (URLs separated by commas)', required=False)

    def clean_fotos(self):
        data = self.cleaned_data['fotos']
        # Split the comma-separated URLs into a list, ignoring empty entries
        return [url.strip() for url in data.split(',') if url.strip()] if data else []


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Utilizador
        fields = ['username', 'iban', 'password', 'foto', 'cidade', 'pais']

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password

    def save(self, commit=True):
        # Store a hashed password, never the raw text
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = []
