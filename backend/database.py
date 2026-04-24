import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'vessels_v2.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    # Ativa o modo WAL (Melhor para escritas concorrentes)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    
    cursor = conn.cursor()
    
    # Tabela mestre das embarcações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vessels_master (
            mmsi INTEGER PRIMARY KEY,
            name TEXT,
            vessel_type TEXT DEFAULT 'Desconhecido',
            flag TEXT,
            dimension_a INTEGER,
            dimension_b INTEGER,
            dimension_c INTEGER,
            dimension_d INTEGER,
            callsign TEXT,
            imo_number TEXT,
            last_updated TEXT,
            suspicious INTEGER DEFAULT 0,
            suspect_reason TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            position_count INTEGER DEFAULT 0,
            first_seen TEXT,
            last_seen TEXT,
            destination TEXT,
            eta TEXT,
            draft REAL
        )
    ''')
    
    # Tabela de histórico de posições
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mmsi INTEGER,
            lat REAL,
            lon REAL,
            speed REAL,
            course REAL,
            true_heading REAL,
            nav_status INTEGER,
            timestamp TEXT,
            FOREIGN KEY (mmsi) REFERENCES vessels_master(mmsi)
        )
    ''')
    
    # Tabela de Ocorrências e Ameaças
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS occurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mmsi INTEGER,
            severity TEXT, 
            description TEXT,
            timestamp TEXT,
            FOREIGN KEY (mmsi) REFERENCES vessels_master(mmsi)
        )
    ''')
    
    # Índices para relatórios rápidos
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mmsi_time ON positions_history(mmsi, timestamp)')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # É imperativo usar pequenos timeouts em WAL mode se algo travar a escrita
    conn.execute('PRAGMA busy_timeout = 3000') 
    return conn

if __name__ == '__main__':
    print("Initializing Database Architecture V2...")
    init_db()
    print("Database ready.")
