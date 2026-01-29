import unittest
import os
import sqlite3
from src.database import init_db, DB_NAME
from src.utils import generate_agent_id
from src.importer import find_agent_id

class TestAusentismoLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Usar una DB de prueba
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        init_db()

    def test_agent_id_generation(self):
        id1 = generate_agent_id("Castro", "Yamil", "mail@test.com")
        id2 = generate_agent_id("Castro", "Yamil ", "MAIL@test.com")
        self.assertEqual(id1, id2)

    def test_find_agent_id_missing(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        agent_id = find_agent_id(cursor, "non_existent")
        self.assertIsNone(agent_id)
        conn.close()

if __name__ == "__main__":
    unittest.main()
