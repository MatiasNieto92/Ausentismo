import pandas as pd
from .database import get_connection

def generate_daily_report(date_str, output_path):
    """Genera un reporte diario en Excel o CSV."""
    with get_connection() as conn:
        query = f"""
            SELECT
                a.agent_id,
                a.first_name || ' ' || a.last_name as name,
                a.scheduled_hours,
                e.status_code as status,
                e.status_detail as reason,
                (SELECT GROUP_CONCAT(login_time) FROM login_logout WHERE agent_id = a.agent_id AND date = '{date_str}') as login_times,
                (SELECT GROUP_CONCAT(logout_time) FROM login_logout WHERE agent_id = a.agent_id AND date = '{date_str}') as logout_times,
                (SELECT SUM(duration_minutes) FROM login_logout WHERE agent_id = a.agent_id AND date = '{date_str}') as total_duration
            FROM agents a
            LEFT JOIN attendance_events e ON a.agent_id = e.agent_id AND e.date = '{date_str}'
        """
        df = pd.read_sql_query(query, conn)

        if output_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)

    return True, None
