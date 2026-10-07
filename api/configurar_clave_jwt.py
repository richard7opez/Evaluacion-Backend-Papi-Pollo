"""Genera una clave local sin imprimir secretos ni cambiar la SECRET_KEY de Django."""
import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key


def main():
    archivo = Path(__file__).resolve().parent.parent / ".env"
    if not archivo.is_file():
        raise SystemExit("Falta .env; configura primero el entorno del proyecto.")
    actual = dotenv_values(archivo).get("JWT_SIGNING_KEY") or ""
    if len(actual.encode()) >= 32:
        print("JWT_SIGNING_KEY ya tiene longitud suficiente; no se ha cambiado.")
        return
    set_key(archivo, "JWT_SIGNING_KEY", secrets.token_urlsafe(64))
    print("Clave JWT segura generada en .env. Los tokens anteriores deben renovarse iniciando sesion.")


if __name__ == "__main__":
    main()
