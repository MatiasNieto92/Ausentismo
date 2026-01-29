import pandas as pd
import json
from datetime import datetime
from .database import get_connection
from .utils import load_config

def get_day_abbr(date_str):
    """Devuelve la abreviatura del día (Mon, Tue, etc.)."""
    date_obj = pd.to_datetime(date_str)
    return date_obj.strftime("%a")

def get_day_full(date_str):
    """Devuelve el nombre completo del día (Monday, etc.)."""
    date_obj = pd.to_datetime(date_str)
    return date_obj.strftime("%A")

def parse_schedule_times(schedule_text):
    """Parsea '09:00 - 19:00' en (datetime.time, datetime.time)."""
    try:
        parts = schedule_text.split("-")
        if len(parts) == 2:
            start_str = parts[0].strip()
            end_str = parts[1].strip()
            start_t = datetime.strptime(start_str, "%H:%M").time()
            end_t = datetime.strptime(end_str, "%H:%M").time()
            return start_t, end_t
    except:
        pass
    return None, None

def process_attendance(date_str):
    """Procesa la asistencia para una fecha específica."""
    config = load_config()
    threshold = config.get("presence_threshold_minutes", 30)
    cols = config.get("roster_columns", {})

    day_abbr = get_day_abbr(date_str)
    day_full = get_day_full(date_str)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Obtener todos los agentes
        cursor.execute("SELECT agent_id, acdid, payroll_number, last_name, first_name, scheduled_hours, raw_row_json FROM agents")
        agents = cursor.fetchall()

        for agent in agents:
            agent_id = agent["agent_id"]
            raw_data = json.loads(agent["raw_row_json"]) if agent["raw_row_json"] else {}

            # 1. Verificar si estaba programado
            schedule_text = str(raw_data.get(day_full, "OFF")).upper()
            is_off = "OFF" in schedule_text or schedule_text == "" or schedule_text == "-"

            # Horas programadas para el día (usando Mon Hrs., Tue Hrs. etc)
            day_scheduled_hrs = raw_data.get(cols.get(day_abbr), 0)
            try:
                day_scheduled_hrs = float(day_scheduled_hrs)
            except:
                day_scheduled_hrs = 0.0

            # 2. Obtener duración de login para ese día
            cursor.execute("""
                SELECT SUM(duration_minutes) as total_duration
                FROM login_logout
                WHERE agent_id = ? AND date = ?
            """, (agent_id, date_str))
            login_data = cursor.fetchone()
            total_minutes = login_data["total_duration"] if login_data["total_duration"] else 0

            # 3. Obtener feedback para ese día
            cursor.execute("SELECT type, notes FROM feedbacks WHERE agent_id = ? AND date = ?", (agent_id, date_str))
            feedback = cursor.fetchone()

            status_code = "NP"
            status_detail = ""

            # 4. Adherencia
            sched_start, sched_end = parse_schedule_times(schedule_text)

            # Obtener el primer login y el último logout
            cursor.execute("""
                SELECT MIN(login_time), MAX(logout_time)
                FROM login_logout
                WHERE agent_id = ? AND date = ?
            """, (agent_id, date_str))
            log_times = cursor.fetchone()
            first_login = log_times[0]
            last_logout = log_times[1]

            adherence_detail = ""
            if sched_start and first_login:
                try:
                    f_log = datetime.strptime(first_login, "%H:%M").time()
                    diff_start = (datetime.combine(datetime.min, f_log) - datetime.combine(datetime.min, sched_start)).total_seconds() / 60
                    if diff_start > 15: # 15 min de gracia
                        adherence_detail += f"Login tarde: {int(diff_start)} min. "
                except: pass

            if is_off:
                status_code = "OFF"
                status_detail = "Día libre según roster"
            elif total_minutes >= threshold:
                status_code = "P" # Presente
                status_detail = f"Presencia: {total_minutes} min. {adherence_detail}"
            elif feedback:
                # Si hay feedback, usualmente es una ausencia planificada o justificada
                # Mapeamos algunos tipos a AP (Ausente Planificado) o lo dejamos como el tipo
                status_code = "AP"
                status_detail = f"Feedback: {feedback['type']} - {feedback['notes']}"
            else:
                status_code = "A" # Ausente (No planificado si no hay nada)
                status_detail = "No se detectó login ni hay feedback"

            # Guardar o actualizar evento de asistencia
            cursor.execute("SELECT event_id FROM attendance_events WHERE agent_id = ? AND date = ?", (agent_id, date_str))
            existing_event = cursor.fetchone()

            if existing_event:
                cursor.execute("""
                    UPDATE attendance_events SET
                        status_code = ?, status_detail = ?, source = 'rules_engine'
                    WHERE event_id = ?
                """, (status_code, status_detail, existing_event["event_id"]))
            else:
                cursor.execute("""
                    INSERT INTO attendance_events (agent_id, date, status_code, status_detail, source)
                    VALUES (?, ?, ?, ?, 'rules_engine')
                """, (agent_id, date_str, status_code, status_detail))

        conn.commit()
    return True, None
