import os
import uvicorn
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List

from src import database
from src.client import AzureDevOpsClient
from src.processor import process_tasks_from_ids

app = FastAPI(title="Auditor de Tasks Azure")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#--- GERENCIADOR DE WEBSOCKET ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Envia uma mensagem para todos os clientes conectados."""
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
def on_startup():
    os.makedirs("data", exist_ok=True)
    database.init_db()
    app.state.loop = asyncio.get_event_loop()
    print("Banco de dados inicializado.")

def run_extraction_and_save_task(loop: asyncio.AbstractEventLoop, manager: ConnectionManager):
    
    def send_status(message: str):
        """
        Função 'ponte' segura para enviar dados da nossa
        thread 'sync' para o loop 'async' do WebSocket.
        """
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), loop)

    try:
        send_status("Passo 1/5: Iniciando cliente...")
        client = AzureDevOpsClient()
        
        send_status("Passo 2/5: Buscando IDs (Tag CoE)...")
        ids = client.get_work_item_ids()
        
        if not ids:
            send_status("Nenhum item encontrado")
            return
        
        # 3. Processa TUDO (passando o client e o callback)
            # O processor.py agora cuida dos Passos 3, 4 e 5
        df_final = process_tasks_from_ids(ids, client, send_status)

        # 4. Salva no DB
        send_status("Salvando no banco de dados...")
        if not df_final.empty:
            database.upsert_dataframe(df_final)
        
        send_status("Concluído") # Concluído!
        
    except Exception as e:
        print(f"ERRO NO BACKGROUND TASK: {e}")
        send_status(f"Erro: {str(e)}")

# --- Endpoints ---
@app.get("/")
def get_homepage(request: Request):
    tasks_data = database.get_all_tasks()
    return templates.TemplateResponse(
        "index.html", 
        { "request": request, "tasks": tasks_data }
    )

@app.post("/run-extraction")
async def run_extraction(background_tasks: BackgroundTasks):
    """
    Endpoint do Botão (POST):
    1. Adiciona a tarefa em background.
    2. Retorna 202 ACCEPTED (sem redirect).
    """

    background_tasks.add_task(
        run_extraction_and_save_task, 
        app.state.loop, 
        manager
    )
    
    return Response(status_code=status.HTTP_202_ACCEPTED)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Mantém a conexão viva
        while True:
            # Apenas esperamos o cliente desconectar
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    print("Iniciando servidor FastAPI em http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)