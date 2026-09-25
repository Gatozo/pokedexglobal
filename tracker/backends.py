from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend de autenticación que permite iniciar sesión usando indistintamente
    el nombre de usuario (username) o la dirección de correo electrónico (email).
    Es insensible a mayúsculas y minúsculas (case-insensitive) y respeta las
    políticas de usuario activo y contraseñas hasheadas de Django.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        if username is None:
            username = kwargs.get(user_model.USERNAME_FIELD)

        if not username or not password:
            return None

        # Búsqueda case-insensitive por username o por email
        user = None
        if '@' in username:
            user = user_model.objects.filter(email__iexact=username).first()

        if user is None:
            user = user_model.objects.filter(username__iexact=username).first()

        # Si aún no lo encuentra y no tenía '@', intentar buscar por email por si acaso
        if user is None:
            user = user_model.objects.filter(email__iexact=username).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
