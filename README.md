# Ausentismo Manager

Sistema de gestión de ausentismo para centros de contacto, desarrollado en Python con Tkinter y SQLite.

## Características

- **Importación de Roster:** Carga de archivos Excel con normalización automática.
- **Procesamiento de Login/Logout:** Cálculo de duración de jornada desde archivos CSV.
- **Gestión de Feedback:** Registro manual o masivo de motivos de ausencia (LOA, PSG, Salud, etc.).
- **Tablero de Indicadores:** Gráficos de distribución de asistencia y tendencia de 7 días.
- **Reportes:** Exportación de reportes diarios a Excel y CSV.

## Requisitos

- Python 3.12+
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar o extraer el proyecto.
2. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Inicialización con datos de ejemplo
Para cargar la base de datos con los archivos de muestra incluidos en `sample_data/`, ejecute:
```bash
python populate_sample_db.py
```

### Ejecución de la aplicación
Inicie la interfaz gráfica con:
```bash
python run_app.py
```

## Estructura del Proyecto

- `src/`: Código fuente modular.
  - `database.py`: Gestión de SQLite.
  - `importer.py`: Lógica de carga de archivos.
  - `rules.py`: Motor de reglas de asistencia.
  - `gui.py`: Interfaz de usuario.
- `sample_data/`: Archivos de ejemplo (Excel/CSV).
- `tests/`: Pruebas unitarias.

## Notas Técnicas
- El sistema utiliza un ID único basado en ACDID o un hash de (Nombre, Apellido, Mail) si el ACDID no está presente.
- El umbral de presencia es configurable (por defecto 30 minutos).
