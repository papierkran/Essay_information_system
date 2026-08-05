import os
import json
from cryptography.fernet import Fernet

_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".crypto.key")


def _load_key() -> bytes:
    """获取用于 API 密钥加密的 Fernet 密钥。
    优先级：ESSAY_CRYPTO_SECRET > ESSAY_JWT_SECRET > 本地持久化随机密钥文件。
    """
    secret = os.environ.get("ESSAY_CRYPTO_SECRET") or os.environ.get("ESSAY_JWT_SECRET")
    if secret:
        return _derive_key(secret)
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            return f.read().strip()
    key = Fernet.generate_key()
    try:
        with open(_KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(_KEY_FILE, 0o600)
    except OSError:
        pass
    return key
_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_key())
    return _fernet


def _derive_key(secret: str) -> bytes:
    import hashlib
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    import base64
    return base64.urlsafe_b64encode(digest)


def encrypt_text(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_text(token: str) -> str:
    try:
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return token


_SENSITIVE_KEYS = (
    "api_key", "apikey", "secret", "secret_key", "access_key",
    "accesskey", "password", "token",
)


def _is_secret_key(key: str) -> bool:
    k = key.lower()
    return any(k == s or k.endswith("_" + s) or s in k for s in _SENSITIVE_KEYS)


def encrypt_secrets(data: dict) -> dict:
    out = {}
    for k, v in data.items():
        if isinstance(v, dict):
            out[k] = encrypt_secrets(v)
        elif isinstance(v, str) and v and _is_secret_key(k):
            out[k] = "enc:" + encrypt_text(v)
        else:
            out[k] = v
    return out


def decrypt_secrets(data: dict) -> dict:
    out = {}
    for k, v in data.items():
        if isinstance(v, dict):
            out[k] = decrypt_secrets(v)
        elif isinstance(v, str) and v.startswith("enc:"):
            out[k] = decrypt_text(v[4:])
        else:
            out[k] = v
    return out


def load_config_row_value(config_value: str) -> dict:
    try:
        data = json.loads(config_value)
    except (json.JSONDecodeError, TypeError):
        return {}
    return decrypt_secrets(data) if isinstance(data, dict) else data


def dump_config_value(data: dict) -> str:
    return json.dumps(encrypt_secrets(data), ensure_ascii=False)