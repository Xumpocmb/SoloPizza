from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _


class ConsentUserCreationForm(UserCreationForm):
    """Регистрация с согласием на обработку персональных данных."""

    consent = forms.BooleanField(
        required=True,
        label=_("Согласие на обработку персональных данных"),
    )

    def clean_consent(self):
        """Согласие на обработку персональных данных обязательно для регистрации."""
        consent = self.cleaned_data.get("consent")
        if not consent:
            raise forms.ValidationError(_("Необходимо дать согласие на обработку персональных данных"))
        return consent
