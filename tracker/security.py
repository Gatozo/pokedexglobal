import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 600  # 10 minutos
CHECK_USERNAME_LIMIT = 20
CHECK_USERNAME_WINDOW = 60  # 60 segundos


def get_client_ip(request) -> str:
    """Extrae la IP real del cliente considerando cabeceras de proxy inverso."""
    if not request:
        return "127.0.0.1"
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
    return ip


def is_login_locked_out(request, identifier: str) -> bool:
    """Comprueba si la IP o la cuenta han sido bloqueadas por exceso de intentos fallidos."""
    ip = get_client_ip(request)
    ident_slug = (identifier or "").strip().lower()

    if cache.get(f"lockout:ip:{ip}"):
        return True
    if ident_slug and cache.get(f"lockout:user:{ident_slug}"):
        return True
    return False


def record_failed_login(request, identifier: str):
    """
    Incrementa el contador de intentos fallidos de login por IP e identificador.
    Si se alcanzan 5 intentos fallidos, activa un bloqueo temporal de 10 minutos.
    """
    ip = get_client_ip(request)
    ident_slug = (identifier or "").strip().lower()

    # Rastrear por IP
    ip_key = f"attempts:ip:{ip}"
    ip_attempts = (cache.get(ip_key) or 0) + 1
    cache.set(ip_key, ip_attempts, timeout=LOGIN_LOCKOUT_SECONDS)
    if ip_attempts >= LOGIN_MAX_ATTEMPTS:
        cache.set(f"lockout:ip:{ip}", True, timeout=LOGIN_LOCKOUT_SECONDS)
        logger.warning("Bloqueo de login activado por IP tras %d intentos: %s", ip_attempts, ip)

    # Rastrear por usuario/correo si se proporcionó
    if ident_slug:
        user_key = f"attempts:user:{ident_slug}"
        user_attempts = (cache.get(user_key) or 0) + 1
        cache.set(user_key, user_attempts, timeout=LOGIN_LOCKOUT_SECONDS)
        if user_attempts >= LOGIN_MAX_ATTEMPTS:
            cache.set(f"lockout:user:{ident_slug}", True, timeout=LOGIN_LOCKOUT_SECONDS)
            logger.warning("Bloqueo de login activado para cuenta tras %d intentos: %s", user_attempts, ident_slug)


def reset_login_attempts(request, identifier: str):
    """Restablece los contadores de fallos y bloqueos tras un inicio de sesión exitoso."""
    ip = get_client_ip(request)
    ident_slug = (identifier or "").strip().lower()

    cache.delete(f"attempts:ip:{ip}")
    cache.delete(f"lockout:ip:{ip}")
    if ident_slug:
        cache.delete(f"attempts:user:{ident_slug}")
        cache.delete(f"lockout:user:{ident_slug}")


def check_username_rate_limit(request) -> bool:
    """
    Limita las consultas de disponibilidad de nombres de usuario a un máximo
    de 20 consultas por minuto por dirección IP.
    Retorna True si la petición es permitida, False si se superó el límite.
    """
    ip = get_client_ip(request)
    key = f"rate:check_user:{ip}"
    count = cache.get(key) or 0
    if count >= CHECK_USERNAME_LIMIT:
        return False
    cache.set(key, count + 1, timeout=CHECK_USERNAME_WINDOW)
    return True
