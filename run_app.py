import tkinter as tk
from src.gui import AusentismoApp
from src.database import init_db

def main():
    # Asegurar que la DB esté inicializada
    init_db()

    root = tk.Tk()
    app = AusentismoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
