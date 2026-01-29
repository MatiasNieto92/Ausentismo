from src.database import init_db
from src.importer import import_roster, import_login_logout, import_feedback_csv
from src.rules import process_attendance
from datetime import datetime, timedelta
import os

def populate():
    print("Inicializando Base de Datos...")
    init_db()

    print("Cargando Roster de ejemplo...")
    import_roster("sample_data/roster_sample.xlsx")

    print("Cargando Login/Logout de ejemplo...")
    import_login_logout("sample_data/login_logout_sample.csv")

    print("Cargando Feedback de ejemplo...")
    import_feedback_csv("sample_data/feedback_sample.csv")

    print("Procesando asistencia para los últimos 7 días...")
    today = datetime.now()
    for i in range(7):
        date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        process_attendance(date_str)

    print("Población completada con éxito.")

if __name__ == "__main__":
    populate()
