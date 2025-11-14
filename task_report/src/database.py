import sqlite3
import pandas as pd

DB_PATH = "data/tasks.db"

def init_db():
    """Cria a tabela de tasks se ela não existir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Colunas principais dos KPIs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        ID INTEGER PRIMARY KEY,
        Title TEXT,
        Assigned_To TEXT,           
        State TEXT,
        Tags TEXT,
        Iteration_Path TEXT,
        KPI_Has_SharePoint_Link BOOLEAN,
        KPI_Has_Complex_Desc BOOLEAN,
        KPI_Has_Attachment BOOLEAN,
        Compliance TEXT,
        Last_Updated_At DATETIME DEFAULT CURRENT_TIMESTAMP,
        Parent_ID INTEGER
    )
    """)
    conn.commit()
    conn.close()

def upsert_dataframe(df: pd.DataFrame):
    """
    Atualiza ou insere (UPSERT) os dados do DataFrame no SQLite.
    Foco na sua regra: "apenas atualizar as linhas já existentes".
    """
    if df.empty:
        return

    # Garantir que temos as colunas certas para o DB
    db_cols = ['ID', 'Title','Assigned_To', 'State','Tags','Iteration_Path', 'KPI_Has_SharePoint_Link', 'KPI_Has_Complex_Desc', 'KPI_Has_Attachment', 'Compliance','Parent_ID']
    df_to_save = df[db_cols].copy()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    

    # Se o ID (PRIMARY KEY) bater, ele executa o 'DO UPDATE'
    query = """
    INSERT INTO tasks (ID, Title, Assigned_To, State, Tags, Iteration_Path, KPI_Has_SharePoint_Link, KPI_Has_Complex_Desc, KPI_Has_Attachment, Compliance, Parent_ID)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(ID) DO UPDATE SET
        Title = excluded.Title,
        Assigned_To = excluded.Assigned_To,
        State = excluded.State,
        Tags = excluded.Tags,
        Iteration_Path = excluded.Iteration_Path,
        KPI_Has_SharePoint_Link = excluded.KPI_Has_SharePoint_Link,
        KPI_Has_Complex_Desc = excluded.KPI_Has_Complex_Desc,
        KPI_Has_Attachment = excluded.KPI_Has_Attachment,
        Compliance = excluded.Compliance,
        Parent_ID = excluded.Parent_ID,
        Last_Updated_At = CURRENT_TIMESTAMP
    """
    
    data_tuples = [tuple(row) for row in df_to_save.to_numpy()]
    
    cursor.executemany(query, data_tuples)
    conn.commit()
    conn.close()
    print(f"Banco de dados atualizado com {len(data_tuples)} registros.")

def get_all_tasks():
    """Busca todos os dados do DB para exibir na página."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY Compliance DESC, ID DESC")
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return tasks