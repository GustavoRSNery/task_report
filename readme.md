# Auditor de Tasks do Azure DevOps

Este projeto é uma aplicação web de auditoria em tempo real, construída com FastAPI e WebSockets, para extrair e validar a conformidade de *Work Items* (Tarefas) de um projeto específico do Azure DevOps.

A interface permite ao usuário disparar uma extração de dados e visualizar os resultados em uma tabela interativa, que inclui filtros dinâmicos, redimensionamento de colunas e controle de visibilidade.

## 🚀 Principais Funcionalidades

* **Interface Web (FastAPI + Jinja2):** Um frontend simples para visualizar dados e iniciar a extração.
* **Feedback em Tempo Real:** Usa **WebSockets** para enviar o status do processo de extração (ex: "Passo 1/5...") para o frontend sem recarregar a página.
* **Extração Robusta:** Conecta-se à API REST do Azure DevOps, busca IDs por tag (via WIQL) e processa os detalhes, incluindo o histórico de comentários de cada task.
* **Validação de KPIs:** O `processor.py` aplica regras de negócio (KPIs) para determinar a conformidade da documentação (links do SharePoint, anexos, complexidade da descrição).
* **Persistência de Dados:** Utiliza **SQLite** para armazenar os resultados da última extração, com lógica de "UPSERT" (atualiza se a task existir, insere se for nova).
* **Tabela Interativa (JavaScript):**
    * **Filtros de Coluna:** Gera dinamicamente filtros dropdown (`<select>`) com os valores únicos de cada coluna.
    * **Visibilidade de Colunas:** Permite ao usuário ocultar ou reexibir colunas através de um menu de checkboxes.
    * **Redimensionamento de Colunas:** Permite ao usuário arrastar para redimensionar colunas.

## ⚙️ Stack Técnica

* **Backend:** Python 3.11+
* **Framework Web:** FastAPI
* **Servidor ASGI:** Uvicorn
* **Comunicação Real-Time:** WebSockets
* **Banco de Dados:** SQLite
* **Validação de Dados:** Pydantic (para configurações e modelos)
* **API/Processamento:** `requests`, `pandas`
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **Template Engine:** Jinja2

## 📂 Estrutura do Projeto

```text
azure-task-validator/
├── main.py             # Servidor FastAPI, endpoints (HTTP, WebSocket)
├── config.py           # Configurações de ambiente (Pydantic)
├── .env.example        # Exemplo das variáveis de ambiente
├── requirements.txt    # Dependências Python
├── data/               # Contém o banco de dados (data/tasks.db)
├── static/             # Arquivos CSS e JS
│   ├── css/style.css
│   └── js/main.js
├── templates/          # Templates HTML (Jinja2)
│   └── index.html
└── src/                # Lógica principal da aplicação
    ├── client.py       # Lógica de API (conexão com Azure DevOps)
    ├── database.py     # Lógica do SQLite (init, upsert)
    ├── models.py       # Modelos de dados Pydantic (TaskData)
    └── processor.py    # Lógica de negócio, validação de KPIs
```
## 🏁 Como Rodar (Localmente)

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPO]
    cd azure-task-validator
    ```

2.  **Crie um ambiente virtual e instale as dependências:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # (Linux/macOS)
    .\.venv\Scripts\activate   # (Windows)
    pip install -r requirements.txt
    ```

3.  **Configure suas credenciais:**
    * Renomeie `.env.example` para `.env`.
    * Edite o arquivo `.env` e adicione seu Token de Acesso Pessoal (PAT) e as URLs:
        ```ini
        AZURE_PAT=seu_token_pat_aqui
        AZURE_ORG_URL=Link2devops
        AZURE_PROJECT=Project_exemple
        AZURE_TAG_FILTER=tag_exemple
        ```

4.  **Execute a aplicação:**
    ```bash
    python main.py
    ```

5.  **Acesse o site:**
    * Abra seu navegador e acesse: **`http://127.0.0.1:8000`**