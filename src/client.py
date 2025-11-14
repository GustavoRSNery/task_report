import requests
from infra.config import settings

class AzureDevOpsClient:
    def __init__(self):
        self.base_url = f"{settings.AZURE_ORG_URL}/{settings.AZURE_PROJECT}/_apis/wit"
        self.api_version = "api-version=7.0"
        self.comment_api_version = "api-version=6.0-preview.3" # Versão da API de comentários

    def get_work_item_ids(self):
        """
        Busca os IDs das tasks, filtrando pelo Projeto E pela Tag (exemplo: CoE) definida no .env.

        Assim como é feito no DevOps mas de forma intuitiva e natural, 
        essa função filtra o pool de dados criando uma query (isto é visivel quando vc olha as tasks atrvés dos graficos).

        Nisto ele gera o Json, que é possivel pegar ele através do /wiql, e isto é a primeira chamada para pegar os IDs.
        Depois em get_work_items_details ele pega os dados de cada comentario.
        """
        query = f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = '{settings.AZURE_PROJECT}'
        AND [System.WorkItemType] <> ''
        AND [System.Tags] CONTAINS '{settings.AZURE_TAG_FILTER}'
        ORDER BY [System.Id] DESC
        """
        
        url = f"{self.base_url}/wiql?{self.api_version}"
        response = requests.post(url, headers=settings.headers, json={"query": query})
        
        if response.status_code == 200:
            work_items = response.json().get("workItems", [])
            return [item['id'] for item in work_items]
        else:
            raise Exception(f"Erro ao buscar IDs (Status {response.status_code}): {response.text}")

    def get_work_items_details(self, ids: list) -> list:
        """
        Traz todas as colunas das tasks no DevOps de uma vez. 
        Depois eu apenas escolho quais colunas eu quero pegar no processor.py
        """
        if not ids:
            return []
            
        # Batch request (limitado a 200 por vez, simplificado aqui)
        # Se tiver mais de 200 tasks CoE, implementamos a paginação depois
        ids_chunk = ids[:200] 
        ids_str = ",".join(map(str, ids_chunk))
        
        url = f"{self.base_url}/workitems?ids={ids_str}&$expand=all&{self.api_version}"
        response = requests.get(url, headers=settings.headers)
        
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            raise Exception(f"Erro ao buscar detalhes: {response.text}")
    
    def get_work_item_comments(self, item_id: int) -> str:
        """
        Busca o texto de todos os comentários de uma Task específica
        e retorna como um único bloco de texto.
        """
        url = f"{self.base_url}/workitems/{item_id}/comments?{self.comment_api_version}"
        response = requests.get(url, headers=settings.headers)
        
        if response.status_code != 200:
            print(f"Warning: Não foi possível buscar comentários para a Task {item_id}")
            return ""

        comments = response.json().get("comments", [])
        all_comment_text = " ".join([comment.get("text", "") for comment in comments])
        return all_comment_text