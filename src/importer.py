import pandas as pd
import json
import os
from .database import get_connection
from .utils import load_config, generate_agent_id
from .models import Agent

def normalize_dataframe(df):
    """Normaliza los encabezados y limpia espacios en blanco."""
    df.columns = [str(c).strip() for c in df.columns]
    return df

def import_roster(file_path):
    """Importa el roster desde un archivo Excel."""
    config = load_config()
    cols = config["roster_columns"]

    try:
        df = pd.read_excel(file_path)
        df = normalize_dataframe(df)

        agents_imported = 0
        with get_connection() as conn:
            cursor = conn.cursor()

            for _, row in df.iterrows():
                # Extraer datos básicos
                acdid = str(row.get(cols["acdid"], "-")).strip()
                payroll = str(row.get(cols["payroll"], "-")).strip()
                last_name = str(row.get(cols["last_name"], "")).strip()
                first_name = str(row.get(cols["first_name"], "")).strip()
                mail = str(row.get(cols["mail"], "")).strip()
                rut = str(row.get(cols["rut"], "")).strip()
                site = str(row.get(cols["site"], "")).strip()
                lob = str(row.get(cols["lob"], "")).strip()

                # Manejar ACDID faltante
                if acdid == "-" or not acdid:
                    acdid = generate_agent_id(last_name, first_name, mail)

                # Buscar si ya existe por Payroll o Mail o ACDID (si existe)
                query = "SELECT agent_id FROM agents WHERE payroll_number = ? OR mail = ?"
                params = [payroll, mail]
                if acdid != "-":
                    query += " OR acdid = ?"
                    params.append(acdid)

                cursor.execute(query, params)
                existing = cursor.fetchone()

                raw_json = row.to_json()

                if existing:
                    agent_id = existing[0]
                    update_sql = """
                    UPDATE agents SET
                        acdid = ?, payroll_number = ?, last_name = ?, first_name = ?,
                        mail = ?, rut = ?, site = ?, scheduled_hours = ?,
                        raw_row_json = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                    """
                    cursor.execute(update_sql, (
                        acdid, payroll, last_name, first_name, mail, rut, site,
                        row.get(cols["scheduled_hours"], 0), raw_json, agent_id
                    ))
                else:
                    insert_sql = """
                    INSERT INTO agents (
                        acdid, payroll_number, last_name, first_name, mail, rut, site,
                        scheduled_hours, raw_row_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_sql, (
                        acdid, payroll, last_name, first_name, mail, rut, site,
                        row.get(cols["scheduled_hours"], 0), raw_json
                    ))

                agents_imported += 1

            conn.commit()
        return agents_imported, None
    except Exception as e:
        return 0, str(e)

def find_agent_id(cursor, identifier):
    """Busca el agent_id por acdid, payroll o mail."""
    if not identifier or identifier == "-":
        return None

    query = """
    SELECT agent_id FROM agents
    WHERE acdid = ? OR payroll_number = ? OR mail = ?
    """
    cursor.execute(query, (identifier, identifier, identifier))
    row = cursor.fetchone()
    return row[0] if row else None

def import_login_logout(file_path):
    """Importa registros de login/logout desde un CSV."""
    try:
        df = pd.read_csv(file_path)
        df = normalize_dataframe(df)

        records_imported = 0
        with get_connection() as conn:
            cursor = conn.cursor()

            for _, row in df.iterrows():
                ident = str(row.get("agent_identifier", "")).strip()
                date = str(row.get("date", "")).strip()
                login_t = str(row.get("login_time", "")).strip()
                logout_t = str(row.get("logout_time", "")).strip()

                agent_id = find_agent_id(cursor, ident)

                # Calcular duración si es posible
                duration = 0
                try:
                    if login_t and logout_t:
                        # Asumiendo formato ISO o similar que pandas entienda
                        start = pd.to_datetime(f"{date} {login_t}")
                        end = pd.to_datetime(f"{date} {logout_t}")
                        duration = int((end - start).total_seconds() / 60)
                except:
                    pass

                insert_sql = """
                INSERT INTO login_logout (
                    agent_id, date, login_time, logout_time, duration_minutes, source_file
                ) VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_sql, (
                    agent_id, date, login_t, logout_t, duration, os.path.basename(file_path)
                ))
                records_imported += 1

            conn.commit()
        return records_imported, None
    except Exception as e:
        return 0, str(e)

def import_feedback_csv(file_path):
    """Importa feedback masivo desde un CSV."""
    try:
        df = pd.read_csv(file_path)
        df = normalize_dataframe(df)

        records_imported = 0
        with get_connection() as conn:
            cursor = conn.cursor()

            for _, row in df.iterrows():
                ident = str(row.get("agent_identifier", "")).strip()
                date = str(row.get("date", "")).strip()
                f_type = str(row.get("type", "")).strip()
                notes = str(row.get("notes", "")).strip()

                agent_id = find_agent_id(cursor, ident)
                if not agent_id:
                    continue

                insert_sql = """
                INSERT INTO feedbacks (agent_id, date, type, notes, created_by)
                VALUES (?, ?, ?, ?, 'csv_import')
                """
                cursor.execute(insert_sql, (agent_id, date, f_type, notes))
                records_imported += 1

            conn.commit()
        return records_imported, None
    except Exception as e:
        return 0, str(e)
