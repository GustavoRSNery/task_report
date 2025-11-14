import pandas as pd
from bs4 import BeautifulSoup
import re
from typing import List, Callable

from src.client import AzureDevOpsClient
from src.models import TaskData

# Regex para encontrar links do SharePoint da organização
SHAREPOINT_REGEX = re.compile(r"https://bkbrasil\.sharepoint\.com", re.IGNORECASE)
# Definição de "Descrição Completa"
COMPLEX_DESCRIPTION_THRESHOLD = 20 # Quantidade de caracteres na descrição


def clean_html(html_content):
    """Remove tags HTML da descrição ou comentarios e retorna apenas o texto limpo."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "lxml") 
    return soup.get_text(strip=True)

def get_parent_id(relations_list):
    """Varre a lista de 'relations' e retorna o ID do Pai."""
    if not relations_list:
        return None
        
    for relation in relations_list:
        if relation.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
            parent_url = relation.get('url', '')
            if parent_url:
                try:
                    return int(parent_url.split('/')[-1])
                except (ValueError, IndexError):
                    pass # Ignora se a URL for malformatada
    return None

def process_tasks_from_ids(ids: List[int], client: AzureDevOpsClient, send_status: Callable) -> pd.DataFrame:
    """
    Orquestra todo o processamento:
    1. Busca detalhes das tasks (em lote)
    2. Para cada task, busca os comentários (N+1)
    3. Limpa e valida usando o modelo Pydantic
    4. Aplica as regras de KPI
    5. Retorna o DataFrame final
    """
    
    # 1. Buscar Detalhes
    send_status(f"Passo 3/5: Buscando {len(ids)} detalhes...")
    details_json = client.get_work_items_details(ids)
    
    processed_list = []
    
    # 2. Loop para buscar comentários
    send_status(f"Passo 4/5: Buscando comentários...")
    
    for i, item_json in enumerate(details_json):
        send_status(f"Passo 4/5: Vendo os comentários da task {item_json.get('id')} | {i+1}/{len(details_json)}")
        
        fields = item_json.get('fields', {})
        
        item_id = item_json.get('id')
        comments_text = client.get_work_item_comments(item_id)
        
        # 4. Limpa e Parseia os dados
        raw_desc = fields.get('System.Description', '')
        clean_desc = clean_html(raw_desc)
        
        assigned_to_data = fields.get('System.AssignedTo')
        assigned_to = "Unassigned"
        if isinstance(assigned_to_data, dict):
            assigned_to = assigned_to_data.get('displayName', 'Unassigned')

        # 5. Monta o modelo de dados usando pydantic | Bom isto pode ser um pouco de over engeneering, mas eu gosto de definir bem o modelo de dados, é possivel ver isto nas fuções
        task = TaskData(
            ID=item_id,
            Type=fields.get('System.WorkItemType'),
            Title=fields.get('System.Title'),
            State=fields.get('System.State'),
            Tags=fields.get('System.Tags', ''),
            Assigned_To=assigned_to,
            Iteration_Path=fields.get('System.IterationPath', ''),
            Parent_ID=get_parent_id(item_json.get('relations')),
            Raw_Description=raw_desc,
            Clean_Desc_Text=clean_desc,
            Desc_Length=len(clean_desc),
            Attachment_Count=fields.get('System.AttachedFileCount', 0),
            Comments_Text=comments_text
        )
        
        processed_list.append(task.model_dump())

    # 6. Cria DataFrame
    if not processed_list:
        return pd.DataFrame()
    df = pd.DataFrame(processed_list)
    
    # 7. Aplica as Validações que definimos na função apply_validations
    send_status("Passo 5/5: Validando dados...")
    df_final = apply_validations(df)
    
    return df_final

def apply_validations(df: pd.DataFrame) -> pd.DataFrame: # Alterar depois # As metricas ainda não estão vindo corretamente nas analises
    """Aplica as 3 regras de validação (KPIs)"""
    if df.empty:
        return df

    # KPI 1: Tem link do SharePoint (na Descrição OU nos Comentários) ?
    df['Has_Link_in_Desc'] = df['Raw_Description'].str.contains(SHAREPOINT_REGEX, na=False)
    df['Has_Link_in_Comment'] = df['Comments_Text'].str.contains(SHAREPOINT_REGEX, na=False)
    df['KPI_Has_SharePoint_Link'] = (df['Has_Link_in_Desc'] | df['Has_Link_in_Comment'])

    # KPI 2: Descrição é complexa (baseado no threshold) ?
    df['KPI_Has_Complex_Desc'] = df['Desc_Length'] > COMPLEX_DESCRIPTION_THRESHOLD

    # KPI 3: Tem arquivos anexados ?
    df['KPI_Has_Attachment'] = df['Attachment_Count'] > 0

    # O ponto focal é: A documentação existe? (KPI 1 ou KPI 3)
    df['Is_Documented'] = (df['KPI_Has_SharePoint_Link'] | df['KPI_Has_Attachment'])
    
    # A task está CONFORME se:
    # 1. Ela está documentada (Link ou Anexo)
    # OU
    # 2. Ela tem uma descrição complexa (que a justifica)
    
    df['Compliance'] = df.apply(
        lambda x: '✅ OK' if (x['Is_Documented'] or x['KPI_Has_Complex_Desc']) else '❌ NOK',
        axis=1
    )
    
    return df