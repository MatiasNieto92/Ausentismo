import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import pandas as pd
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from .database import get_connection, init_db
from .importer import import_roster, import_login_logout, import_feedback_csv
from .rules import process_attendance
from .utils import load_config, save_config
from .reports import generate_daily_report

class AusentismoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ausentismo Manager v1.0")
        self.root.geometry("1200x800")

        self.config = load_config()
        self.selected_date = datetime.now().strftime("%Y-%m-%d")

        self.setup_menu()
        self.setup_layout()

    def setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cargar Roster Excel", command=self.load_roster)
        file_menu.add_command(label="Cargar Login/Logout CSV", command=self.load_login_logout)
        file_menu.add_command(label="Importar Feedback CSV", command=self.load_feedback)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        report_menu = tk.Menu(menubar, tearoff=0)
        report_menu.add_command(label="Exportar Reporte Diario", command=self.export_report)
        report_menu.add_command(label="Exportar Gráficos (PNG)", command=self.export_dashboard_png)
        menubar.add_cascade(label="Reportes", menu=report_menu)

        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Configuración", command=self.show_config_win)
        menubar.add_cascade(label="Herramientas", menu=config_menu)

        self.root.config(menu=menubar)

    def setup_layout(self):
        # Panel Izquierdo (Filtros)
        self.left_panel = ttk.Frame(self.root, width=200, padding=10)
        self.left_panel.pack(side="left", fill="y")

        ttk.Label(self.left_panel, text="FILTROS", font=("Arial", 12, "bold")).pack(pady=10)

        ttk.Label(self.left_panel, text="Fecha:").pack(anchor="w")
        self.date_entry = DateEntry(self.left_panel, date_pattern='y-mm-dd')
        self.date_entry.pack(fill="x", pady=5)

        ttk.Label(self.left_panel, text="Con Feedback:").pack(anchor="w")
        self.filter_feedback = ttk.Combobox(self.left_panel, values=["Todos", "Si", "No"])
        self.filter_feedback.pack(fill="x", pady=5)
        self.filter_feedback.set("Todos")

        ttk.Label(self.left_panel, text="LOB:").pack(anchor="w")
        self.filter_lob = ttk.Combobox(self.left_panel)
        self.filter_lob.pack(fill="x", pady=5)

        ttk.Label(self.left_panel, text="Estado:").pack(anchor="w")
        self.filter_status = ttk.Combobox(self.left_panel, values=["Todos", "P", "A", "AP", "NP", "OFF"])
        self.filter_status.pack(fill="x", pady=5)

        ttk.Button(self.left_panel, text="Aplicar Filtros", command=self.load_agent_list).pack(fill="x", pady=5)
        ttk.Button(self.left_panel, text="Procesar Asistencia", command=self.run_process).pack(fill="x", pady=10)

        self.update_filter_values()

        # Panel Central (Tablero)
        self.center_panel = ttk.Frame(self.root, padding=10)
        self.center_panel.pack(side="left", fill="both", expand=True)

        self.nb = ttk.Notebook(self.center_panel)
        self.nb.pack(fill="both", expand=True)

        self.tab_dashboard = ttk.Frame(self.nb)
        self.tab_agents = ttk.Frame(self.nb)

        self.nb.add(self.tab_dashboard, text="Tablero de Indicadores")
        self.nb.add(self.tab_agents, text="Lista de Agentes")

        # Tabla de agentes
        columns = ("ID", "Nombre", "Apellido", "Estado", "Detalle")
        self.tree = ttk.Treeview(self.tab_agents, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_agent_select)
        self.tree.bind("<Double-1>", self.on_agent_double_click)

        # Panel Derecho (Detalles)
        self.right_panel = ttk.Frame(self.root, width=300, padding=10)
        self.right_panel.pack(side="right", fill="y")
        ttk.Label(self.right_panel, text="DETALLE AGENTE", font=("Arial", 12, "bold")).pack(pady=10)

    def load_roster(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if path:
            count, err = import_roster(path)
            if err:
                messagebox.showerror("Error", f"Error al importar roster: {err}")
            else:
                messagebox.showinfo("Éxito", f"Se importaron/actualizaron {count} agentes.")
                self.update_filter_values()

    def load_login_logout(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            count, err = import_login_logout(path)
            if err:
                messagebox.showerror("Error", f"Error al importar login: {err}")
            else:
                messagebox.showinfo("Éxito", f"Se importaron {count} registros de login.")

    def load_feedback(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            count, err = import_feedback_csv(path)
            if err:
                messagebox.showerror("Error", f"Error al importar feedback: {err}")
            else:
                messagebox.showinfo("Éxito", f"Se importaron {count} feedbacks.")

    def update_filter_values(self):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT lob FROM agents")
            lobs = [r[0] for r in cursor.fetchall() if r[0]]
            self.filter_lob['values'] = ["Todos"] + lobs

    def run_process(self):
        date_str = self.date_entry.get()
        success, err = process_attendance(date_str)
        if success:
            messagebox.showinfo("Proceso", f"Procesamiento completado para {date_str}")
            self.refresh_ui()
        else:
            messagebox.showerror("Error", err)

    def refresh_ui(self):
        self.draw_charts()
        self.load_agent_list()

    def load_agent_list(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        date_str = self.date_entry.get()
        fb_f = self.filter_feedback.get()
        lob_f = self.filter_lob.get()
        status_f = self.filter_status.get()

        with get_connection() as conn:
            query = f"""
                SELECT a.agent_id, a.first_name, a.last_name, a.lob, e.status_code, e.status_detail,
                (SELECT COUNT(*) FROM feedbacks f WHERE f.agent_id = a.agent_id AND f.date = '{date_str}') as has_fb
                FROM agents a
                LEFT JOIN attendance_events e ON a.agent_id = e.agent_id AND e.date = '{date_str}'
                WHERE 1=1
            """
            if lob_f and lob_f != "Todos":
                query += f" AND a.lob = '{lob_f}'"
            if status_f and status_f != "Todos":
                query += f" AND e.status_code = '{status_f}'"

            if fb_f == "Si":
                query += " AND has_fb > 0"
            elif fb_f == "No":
                query += " AND has_fb = 0"

            df = pd.read_sql_query(query, conn)

            for _, row in df.iterrows():
                self.tree.insert("", "end", values=(
                    row["agent_id"], row["first_name"], row["last_name"],
                    row["status_code"] or "N/A", row["status_detail"] or ""
                ))

    def on_agent_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        agent_id = item["values"][0]
        self.show_agent_detail(agent_id)

    def on_agent_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        agent_id = item["values"][0]
        agent_name = f"{item['values'][1]} {item['values'][2]}"
        self.open_feedback_dialog(agent_id, agent_name)

    def open_feedback_dialog(self, agent_id, agent_name):
        date_str = self.date_entry.get()
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar Feedback - {agent_name}")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Agente: {agent_name}", font=("Arial", 10, "bold")).pack(pady=10)
        ttk.Label(dialog, text=f"Fecha: {date_str}").pack(pady=5)

        ttk.Label(dialog, text="Tipo de Feedback:").pack(anchor="w", padx=20)
        fb_combo = ttk.Combobox(dialog, values=["VAC", "LOA", "BAJA", "PSG", "PCG", "P. Personales", "P. Salud", "Sin Herramientas"])
        fb_combo.pack(fill="x", padx=20, pady=5)

        ttk.Label(dialog, text="Notas:").pack(anchor="w", padx=20)
        fb_text = tk.Text(dialog, height=5)
        fb_text.pack(fill="both", padx=20, pady=5, expand=True)

        def save():
            f_type = fb_combo.get()
            notes = fb_text.get("1.0", tk.END).strip()
            if not f_type:
                messagebox.showwarning("Aviso", "Seleccione un tipo de feedback", parent=dialog)
                return

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO feedbacks (agent_id, date, type, notes, created_by)
                    VALUES (?, ?, ?, ?, 'manual_double_click')
                """, (agent_id, date_str, f_type, notes))
                conn.commit()

            # Reprocesar asistencia para esta fecha para que se refleje el cambio
            process_attendance(date_str)
            self.refresh_ui()
            messagebox.showinfo("Éxito", "Feedback guardado y asistencia actualizada.", parent=dialog)
            dialog.destroy()

        ttk.Button(dialog, text="Guardar y Actualizar", command=save).pack(pady=20)

    def show_agent_detail(self, agent_id):
        # Limpiar panel derecho
        for widget in self.right_panel.winfo_children():
            if widget.winfo_name() != "!label": # Mantener el título
                widget.destroy()

        date_str = self.date_entry.get()
        ttk.Label(self.right_panel, text=f"Agente ID: {agent_id}").pack(pady=5)
        ttk.Label(self.right_panel, text=f"Fecha: {date_str}", font=("Arial", 10, "italic")).pack(pady=2)

        ttk.Label(self.right_panel, text="Tipo de Feedback:").pack(anchor="w")
        self.fb_type = ttk.Combobox(self.right_panel, values=["VAC", "LOA", "BAJA", "PSG", "PCG", "P. Personales", "P. Salud", "Sin Herramientas"])
        self.fb_type.pack(fill="x", pady=5)

        ttk.Label(self.right_panel, text="Notas:").pack(anchor="w")
        self.fb_notes = tk.Text(self.right_panel, height=4)
        self.fb_notes.pack(fill="x", pady=5)

        ttk.Button(self.right_panel, text="Guardar Feedback",
                   command=lambda: self.save_manual_feedback(agent_id)).pack(fill="x", pady=10)

        ttk.Separator(self.right_panel, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(self.right_panel, text="Forzar Estado:").pack(anchor="w")
        self.manual_status = ttk.Combobox(self.right_panel, values=["P", "A", "AP", "NP", "OFF"])
        self.manual_status.pack(fill="x", pady=5)

        ttk.Button(self.right_panel, text="Forzar Estado",
                   command=lambda: self.force_status(agent_id)).pack(fill="x", pady=10)

        ttk.Button(self.right_panel, text="Ver Historial",
                   command=lambda: self.view_history(agent_id)).pack(fill="x", pady=10)

    def force_status(self, agent_id):
        status = self.manual_status.get()
        date_str = self.date_entry.get()
        if not status: return

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id FROM attendance_events WHERE agent_id = ? AND date = ?", (agent_id, date_str))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE attendance_events SET status_code = ?, status_detail = 'Manual override' WHERE event_id = ?", (status, existing[0]))
            else:
                cursor.execute("INSERT INTO attendance_events (agent_id, date, status_code, status_detail, source) VALUES (?, ?, ?, 'Manual override', 'manual')", (agent_id, date_str, status))
            conn.commit()
        self.refresh_ui()

    def view_history(self, agent_id):
        with get_connection() as conn:
            df = pd.read_sql_query(f"SELECT date, status_code, status_detail FROM attendance_events WHERE agent_id = {agent_id} ORDER BY date DESC", conn)

        history_win = tk.Toplevel(self.root)
        history_win.title("Historial de Agente")
        text = tk.Text(history_win)
        text.insert(tk.END, df.to_string(index=False))
        text.pack(fill="both", expand=True)

    def save_manual_feedback(self, agent_id):
        f_type = self.fb_type.get()
        notes = self.fb_notes.get("1.0", tk.END).strip()
        date_str = self.date_entry.get()

        if not f_type:
            messagebox.showwarning("Aviso", "Seleccione un tipo de feedback")
            return

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedbacks (agent_id, date, type, notes, created_by)
                VALUES (?, ?, ?, ?, 'manual_gui')
            """, (agent_id, date_str, f_type, notes))
            conn.commit()

        process_attendance(date_str)
        self.refresh_ui()
        messagebox.showinfo("Éxito", "Feedback guardado y asistencia actualizada.")

    def draw_charts(self):
        # Limpiar panel de dashboard e hilos previos de matplotlib
        for widget in self.tab_dashboard.winfo_children():
            widget.destroy()
        plt.close('all')

        date_str = self.date_entry.get()

        with get_connection() as conn:
            # 1. Datos para gráfico de pastel (Motivos)
            df_status = pd.read_sql_query(f"""
                SELECT status_code, COUNT(*) as total
                FROM attendance_events
                WHERE date = '{date_str}' AND status_code != 'OFF'
                GROUP BY status_code
            """, conn)

            # 2. Datos para tendencia 7 días
            end_date = pd.to_datetime(date_str)
            start_date = end_date - timedelta(days=6)
            df_trend = pd.read_sql_query(f"""
                SELECT date, status_code, COUNT(*) as total
                FROM attendance_events
                WHERE date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{date_str}'
                AND status_code != 'OFF'
                GROUP BY date, status_code
            """, conn)

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4))

        if not df_status.empty:
            ax1.pie(df_status['total'], labels=df_status['status_code'], autopct='%1.1f%%')
            ax1.set_title("Distribución de Asistencia")

            # Top 5 motivos (si hay ausencias)
            df_reasons = df_status[df_status['status_code'].isin(['A', 'AP', 'NP'])]
            if not df_reasons.empty:
                df_reasons.plot(kind='bar', x='status_code', y='total', ax=ax3, legend=False)
                ax3.set_title("Top Motivos Ausencia")
            else:
                ax3.text(0.5, 0.5, "Sin ausencias hoy", ha='center')
        else:
            ax1.text(0.5, 0.5, "No hay datos para esta fecha", ha='center')
            ax3.text(0.5, 0.5, "Sin datos", ha='center')

        if not df_trend.empty:
            # Pivotar para el gráfico de línea
            df_pivot = df_trend.pivot(index='date', columns='status_code', values='total').fillna(0)
            df_pivot.plot(kind='line', ax=ax2, marker='o')
            ax2.set_title("Tendencia 7 Días")
            ax2.legend(loc='upper right', fontsize='small')
        else:
            ax2.text(0.5, 0.5, "Sin datos de tendencia", ha='center')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.tab_dashboard)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_config_win(self):
        config_win = tk.Toplevel(self.root)
        config_win.title("Configuración")
        config_win.geometry("300x200")

        ttk.Label(config_win, text="Umbral de presencia (min):").pack(pady=10)
        val_var = tk.StringVar(value=str(self.config.get("presence_threshold_minutes", 30)))
        entry = ttk.Entry(config_win, textvariable=val_var)
        entry.pack(pady=5)

        def save():
            try:
                self.config["presence_threshold_minutes"] = int(val_var.get())
                save_config(self.config)
                messagebox.showinfo("Éxito", "Configuración guardada.")
                config_win.destroy()
            except:
                messagebox.showerror("Error", "Ingrese un número válido.")

        ttk.Button(config_win, text="Guardar", command=save).pack(pady=20)

    def export_dashboard_png(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if path and hasattr(self, 'current_fig'):
            self.current_fig.savefig(path)
            messagebox.showinfo("Éxito", f"Imagen guardada en {path}")

    def export_report(self):
        date_str = self.date_entry.get()
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
            initialfile=f"reporte_ausentismo_{date_str}.xlsx"
        )
        if path:
            success, err = generate_daily_report(date_str, path)
            if success:
                messagebox.showinfo("Éxito", f"Reporte guardado en {path}")
            else:
                messagebox.showerror("Error", err)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = AusentismoApp(root)
    root.mainloop()
