
import psycopg2
from werkzeug.security import generate_password_hash
from getpass import getpass
from urllib.parse import urlparse

print("=== CREAR ADMINISTRADOR ZUQARA TOURS ===")

url = getpass("Pega la External Database URL (no se mostrará): ")

correo = input("Correo del administrador: ").strip().lower()
nombre = input("Nombre del administrador: ").strip()
password = getpass("Nueva contraseña: ")
confirmacion = getpass("Confirma la contraseña: ")

if not correo or not nombre:
    raise SystemExit("El correo y el nombre son obligatorios.")

if len(password) < 12:
    raise SystemExit("La contraseña debe tener al menos 12 caracteres.")

if password != confirmacion:
    raise SystemExit("Las contraseñas no coinciden.")

try:
    hash_password = generate_password_hash(password)
    conexion = psycopg2.connect(url)
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT id FROM administradores
        WHERE correo = %s
        """,
        (correo,)
    )

    existente = cursor.fetchone()

    if existente:
        cursor.execute(
            """
            UPDATE administradores
            SET nombre = %s, "contraseña" = %s
            WHERE id = %s
            """,
            (nombre, hash_password, existente[0])
        )
        mensaje = "Administrador actualizado."
    else:
        cursor.execute(
            """
            INSERT INTO administradores
            (nombre, correo, "contraseña")
            VALUES (%s, %s, %s)
            """,
            (nombre, correo, hash_password)
        )
        mensaje = "Administrador creado."

    conexion.commit()
    print(mensaje)

except Exception as error:
    if 'conexion' in locals():
        conexion.rollback()
    print("Error:", error)

finally:
    if 'conexion' in locals():
        conexion.close()
