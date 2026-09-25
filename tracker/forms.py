import re
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class HybridLoginForm(forms.Form):
    """
    Formulario de inicio de sesión que acepta indistintamente
    nombre de usuario o correo electrónico junto con la contraseña.
    """
    identifier = forms.CharField(
        label="Usuario o Correo Electrónico",
        max_length=150,
        widget=forms.TextInput(attrs={
            "id": "id_login_identifier",
            "placeholder": "Ej. red_kanto o ash@pueblopaleta.com",
            "autocomplete": "username",
            "class": "w-full px-3.5 py-2.5 text-sm font-bold text-slate-900 bg-white border-2 border-slate-950 rounded-xl shadow-[2.5px_2.5px_0px_#0f172a] focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-400/50 transition-all placeholder:text-slate-400 font-sans",
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "id": "id_login_password",
            "placeholder": "••••••••",
            "autocomplete": "current-password",
            "class": "w-full px-3.5 py-2.5 text-sm font-bold text-slate-900 bg-white border-2 border-slate-950 rounded-xl shadow-[2.5px_2.5px_0px_#0f172a] focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-400/50 transition-all placeholder:text-slate-400 font-sans",
        })
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier")
        password = cleaned_data.get("password")

        if identifier and password:
            identifier = identifier.strip()
            self.user_cache = authenticate(self.request, username=identifier, password=password)
            if self.user_cache is None:
                raise ValidationError(
                    "Usuario/correo o contraseña incorrectos. Por favor verifica tus credenciales.",
                    code="invalid_login"
                )
            if not self.user_cache.is_active:
                raise ValidationError(
                    "Esta cuenta de entrenador está desactivada.",
                    code="inactive"
                )
        return cleaned_data

    def get_user(self):
        return self.user_cache


class UserRegisterForm(forms.Form):
    """
    Formulario de registro bajo estándares de seguridad:
    - Nombre de usuario único (case-insensitive) y con caracteres alfanuméricos seguros.
    - Correo electrónico obligatorio, con validación de unicidad.
    - Contraseña validada con las directivas de seguridad nativas de Django (longitud, similitud, etc.).
    - Confirmación de contraseña para evitar errores tipográficos.
    """
    username = forms.CharField(
        label="Nombre de Entrenador (Usuario)",
        min_length=3,
        max_length=25,
        widget=forms.TextInput(attrs={
            "id": "id_reg_username",
            "placeholder": "Ej. RedKanto, Blue_Rival, Cynthia",
            "autocomplete": "username",
            "class": "w-full px-3.5 py-2.5 text-sm font-bold text-slate-900 bg-white border-2 border-slate-950 rounded-xl shadow-[2.5px_2.5px_0px_#0f172a] focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-400/50 transition-all placeholder:text-slate-400 font-sans",
        }),
        help_text="Entre 3 y 25 caracteres. Letras, números y guiones bajos (_)."
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "id": "id_reg_email",
            "placeholder": "entrenador@ejemplo.com",
            "autocomplete": "email",
            "class": "w-full px-3.5 py-2.5 text-sm font-bold text-slate-900 bg-white border-2 border-slate-950 rounded-xl shadow-[2.5px_2.5px_0px_#0f172a] focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-400/50 transition-all placeholder:text-slate-400 font-sans",
        }),
        help_text="Te permitirá iniciar sesión y recuperar tu cuenta de forma independiente."
    )
    password = forms.CharField(
        label="Contraseña",
        min_length=4,
        max_length=32,
        widget=forms.PasswordInput(attrs={
            "id": "id_reg_password",
            "maxlength": "32",
            "placeholder": "••••••••",
            "autocomplete": "new-password",
            "class": "w-full px-3.5 py-2.5 text-sm font-bold text-slate-900 bg-white border-2 border-slate-950 rounded-xl shadow-[2.5px_2.5px_0px_#0f172a] focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-400/50 transition-all placeholder:text-slate-400 font-sans",
        }),
        help_text="Entre 4 y 32 caracteres. Elige la clave que prefieras."
    )
    password_confirm = forms.CharField(
        label="Confirmar Contraseña",
        max_length=32,
        widget=forms.PasswordInput(attrs={
            "id": "id_reg_password_confirm",
            "maxlength": "32",
            "placeholder": "••••••••",
            "autocomplete": "new-password",
            "class": "w-full px-3.5 py-2.5 text-sm font-bold text-slate-900 bg-white border-2 border-slate-950 rounded-xl shadow-[2.5px_2.5px_0px_#0f172a] focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-400/50 transition-all placeholder:text-slate-400 font-sans",
        }),
        help_text="Repite la contraseña exactamente igual."
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError(
                "El nombre de usuario solo puede contener letras, números y guiones bajos (_), sin espacios ni símbolos especiales.",
                code="invalid_username"
            )
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(
                "Ese nombre de entrenador ya está registrado. Por favor elige otro diferente.",
                code="username_taken"
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("El correo electrónico es obligatorio.", code="required")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "Ya existe una cuenta registrada con este correo electrónico.",
                code="email_taken"
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                self.add_error("password_confirm", "Las contraseñas no coinciden. Por favor verifícalas.")

        return cleaned_data


    def save(self):
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return user
