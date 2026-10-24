"""Cuentas de propietarios y sus departamentos, guardados en SQLite.

Prototipo: las contraseñas se guardan con PBKDF2-SHA256 y sal propia, y los tokens de sesión solo
como hash. La base vive en data/deparent.sqlite (no se sube a GitHub); DEPARENT_DB permite cambiarla.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path

from modelo import ROOT

BASE = Path(os.environ.get("DEPARENT_DB", ROOT / "data/deparent.sqlite"))
ITERACIONES = 200_000
DURACION_SESION_S = 7 * 24 * 3600
PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
    sal BLOB NOT NULL, hash BLOB NOT NULL, creado REAL NOT NULL);
CREATE TABLE IF NOT EXISTS sesiones (
    token_hash TEXT PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    expira REAL NOT NULL);
CREATE TABLE IF NOT EXISTS departamentos (
    id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL, vivienda TEXT NOT NULL, latitud REAL, longitud REAL, resumen TEXT,
    precio_publicado REAL, escenario_publicado TEXT, publicado_en REAL,
    creado REAL NOT NULL, actualizado REAL NOT NULL);
CREATE TABLE IF NOT EXISTS interesados (
    id INTEGER PRIMARY KEY, departamento_id INTEGER NOT NULL REFERENCES departamentos(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL, email TEXT NOT NULL, mensaje TEXT NOT NULL, creado REAL NOT NULL);
"""


class DatosInvalidos(ValueError):
    pass


class NoAutorizado(Exception):
    pass


class NoEncontrado(Exception):
    pass


def conectar(base=None):
    ruta = Path(base or BASE)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # Cada petición abre y cierra su propia conexión, pero FastAPI puede crearla y usarla en hilos distintos.
    conexion = sqlite3.connect(ruta, check_same_thread=False)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.executescript(ESQUEMA)
    return conexion


def _hash_password(password, sal):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, ITERACIONES)


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _usuario(fila):
    return {"id": fila["id"], "nombre": fila["nombre"], "email": fila["email"]}


def registrar(conexion, nombre, email, password):
    nombre, email = (nombre or "").strip(), (email or "").strip().lower()
    if not 2 <= len(nombre) <= 80:
        raise DatosInvalidos("Escribe tu nombre (entre 2 y 80 caracteres).")
    if not PATRON_EMAIL.match(email) or len(email) > 120:
        raise DatosInvalidos("Escribe un correo válido.")
    if len(password or "") < 8:
        raise DatosInvalidos("La contraseña debe tener al menos 8 caracteres.")
    sal = secrets.token_bytes(16)
    try:
        with conexion:
            cursor = conexion.execute("INSERT INTO usuarios (nombre, email, sal, hash, creado) VALUES (?, ?, ?, ?, ?)",
                                      (nombre, email, sal, _hash_password(password, sal), time.time()))
    except sqlite3.IntegrityError:
        raise DatosInvalidos("Ya existe una cuenta con ese correo.")
    return {"id": cursor.lastrowid, "nombre": nombre, "email": email}


def ingresar(conexion, email, password):
    fila = conexion.execute("SELECT * FROM usuarios WHERE email = ?", ((email or "").strip().lower(),)).fetchone()
    # Se calcula el hash aunque el correo no exista, para no revelar qué correos están registrados.
    sal = fila["sal"] if fila else b"\0" * 16
    calculado = _hash_password(password or "", sal)
    if fila is None or not hmac.compare_digest(calculado, fila["hash"]):
        raise NoAutorizado("Correo o contraseña incorrectos.")
    return _usuario(fila)


def crear_sesion(conexion, usuario_id):
    token = secrets.token_urlsafe(32)
    with conexion:
        conexion.execute("DELETE FROM sesiones WHERE expira < ?", (time.time(),))
        conexion.execute("INSERT INTO sesiones VALUES (?, ?, ?)", (_hash_token(token), usuario_id, time.time() + DURACION_SESION_S))
    return token


def usuario_de_token(conexion, token):
    if not token:
        raise NoAutorizado("Inicia sesión para continuar.")
    fila = conexion.execute("SELECT u.* FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id "
                            "WHERE s.token_hash = ? AND s.expira > ?", (_hash_token(token), time.time())).fetchone()
    if fila is None:
        raise NoAutorizado("Tu sesión expiró. Inicia sesión de nuevo.")
    return _usuario(fila)


def cerrar_sesion(conexion, token):
    with conexion:
        conexion.execute("DELETE FROM sesiones WHERE token_hash = ?", (_hash_token(token or ""),))


def _departamento(fila):
    return {"id": fila["id"], "nombre": fila["nombre"], "vivienda": json.loads(fila["vivienda"]),
            "ubicacion": ({"latitud": fila["latitud"], "longitud": fila["longitud"]} if fila["latitud"] is not None else None),
            "resumen": json.loads(fila["resumen"]) if fila["resumen"] else None,
            "publicacion": ({"precio_soles": fila["precio_publicado"], "escenario": fila["escenario_publicado"],
                             "desde": fila["publicado_en"]} if fila["precio_publicado"] is not None else None),
            "creado": fila["creado"], "actualizado": fila["actualizado"]}


def _validar_nombre_departamento(nombre):
    nombre = (nombre or "").strip()
    if not 2 <= len(nombre) <= 80:
        raise DatosInvalidos("Ponle un nombre al departamento (entre 2 y 80 caracteres), por ejemplo «Depa de Lince».")
    return nombre


def listar_departamentos(conexion, usuario_id):
    filas = conexion.execute("SELECT * FROM departamentos WHERE usuario_id = ? ORDER BY actualizado DESC", (usuario_id,))
    return [_departamento(f) for f in filas]


def obtener_departamento(conexion, usuario_id, departamento_id):
    fila = conexion.execute("SELECT * FROM departamentos WHERE id = ? AND usuario_id = ?", (departamento_id, usuario_id)).fetchone()
    if fila is None:
        raise NoEncontrado("No encontramos ese departamento en tu cuenta.")
    return _departamento(fila)


def guardar_departamento(conexion, usuario_id, nombre, vivienda, ubicacion, resumen, departamento_id=None):
    """Crea o actualiza. Cambiar las características retira la publicación, porque su precio ya no aplica."""
    nombre = _validar_nombre_departamento(nombre)
    lat, lon = (ubicacion["latitud"], ubicacion["longitud"]) if ubicacion else (None, None)
    ahora = time.time()
    with conexion:
        if departamento_id is None:
            cursor = conexion.execute(
                "INSERT INTO departamentos (usuario_id, nombre, vivienda, latitud, longitud, resumen, creado, actualizado) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (usuario_id, nombre, json.dumps(vivienda), lat, lon, json.dumps(resumen), ahora, ahora))
            departamento_id = cursor.lastrowid
        else:
            anterior = obtener_departamento(conexion, usuario_id, departamento_id)
            cambio = anterior["vivienda"] != vivienda
            conexion.execute(
                "UPDATE departamentos SET nombre = ?, vivienda = ?, latitud = ?, longitud = ?, resumen = ?, actualizado = ?"
                + (", precio_publicado = NULL, escenario_publicado = NULL, publicado_en = NULL" if cambio else "")
                + " WHERE id = ? AND usuario_id = ?",
                (nombre, json.dumps(vivienda), lat, lon, json.dumps(resumen), ahora, departamento_id, usuario_id))
    return obtener_departamento(conexion, usuario_id, departamento_id)


def eliminar_departamento(conexion, usuario_id, departamento_id):
    obtener_departamento(conexion, usuario_id, departamento_id)
    with conexion:
        conexion.execute("DELETE FROM departamentos WHERE id = ? AND usuario_id = ?", (departamento_id, usuario_id))


def publicar(conexion, usuario_id, departamento_id, precio, escenario):
    obtener_departamento(conexion, usuario_id, departamento_id)
    if precio is None:
        with conexion:
            conexion.execute("UPDATE departamentos SET precio_publicado = NULL, escenario_publicado = NULL, publicado_en = NULL "
                             "WHERE id = ? AND usuario_id = ?", (departamento_id, usuario_id))
    else:
        if not 300 <= float(precio) <= 50000:
            raise DatosInvalidos("El precio de publicación debe estar entre S/ 300 y S/ 50,000.")
        with conexion:
            conexion.execute("UPDATE departamentos SET precio_publicado = ?, escenario_publicado = ?, publicado_en = ? "
                             "WHERE id = ? AND usuario_id = ?",
                             (round(float(precio), 2), (escenario or "Personalizado")[:40], time.time(), departamento_id, usuario_id))
    return obtener_departamento(conexion, usuario_id, departamento_id)


def publicados(conexion):
    """Departamentos publicados por cualquier propietario, sin datos de contacto del dueño."""
    filas = conexion.execute("SELECT * FROM departamentos WHERE precio_publicado IS NOT NULL ORDER BY publicado_en DESC")
    return [_departamento(f) for f in filas]


def publicado(conexion, departamento_id):
    """Un departamento publicado tal como lo ve un inquilino: con el nombre de pila del propietario, sin su correo."""
    fila = conexion.execute("SELECT d.*, u.nombre AS propietario FROM departamentos d JOIN usuarios u ON u.id = d.usuario_id "
                            "WHERE d.id = ? AND d.precio_publicado IS NOT NULL", (departamento_id,)).fetchone()
    if fila is None:
        raise NoEncontrado("Ese departamento no está publicado.")
    return {**_departamento(fila), "propietario": fila["propietario"].split()[0]}


def registrar_interes(conexion, departamento_id, nombre, email, mensaje):
    publicado(conexion, departamento_id)
    nombre, email, mensaje = (nombre or "").strip(), (email or "").strip().lower(), (mensaje or "").strip()
    if not 2 <= len(nombre) <= 80:
        raise DatosInvalidos("Escribe tu nombre (entre 2 y 80 caracteres).")
    if not PATRON_EMAIL.match(email) or len(email) > 120:
        raise DatosInvalidos("Escribe un correo válido para que el propietario pueda responderte.")
    if not 5 <= len(mensaje) <= 600:
        raise DatosInvalidos("Escribe un mensaje de entre 5 y 600 caracteres.")
    with conexion:
        conexion.execute("INSERT INTO interesados (departamento_id, nombre, email, mensaje, creado) VALUES (?, ?, ?, ?, ?)",
                         (departamento_id, nombre, email, mensaje, time.time()))


def listar_interesados(conexion, usuario_id, departamento_id):
    obtener_departamento(conexion, usuario_id, departamento_id)
    filas = conexion.execute("SELECT nombre, email, mensaje, creado FROM interesados WHERE departamento_id = ? ORDER BY creado DESC",
                             (departamento_id,))
    return [dict(f) for f in filas]
