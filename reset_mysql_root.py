import mysql.connector
from mysql.connector import Error

try:
    # Première tentative de connexion sans mot de passe
    connection = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        port='3306'
    )
    
    if connection.is_connected():
        cursor = connection.cursor()
        
        # Réinitialiser le mot de passe root et le plugin d'authentification
        cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY ''")
        cursor.execute("FLUSH PRIVILEGES")
        print("Configuration de root réussie")
        
        # Créer la base de données si elle n'existe pas
        cursor.execute("CREATE DATABASE IF NOT EXISTS ediligence_db")
        print("Base de données ediligence_db créée ou vérifiée")
        
except Error as e:
    print("Erreur MySQL:", e)
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("Connexion MySQL fermée")
