from pydantic import BaseModel, Field
from typing import Optional

class TaskData(BaseModel):
    """
    Define a estrutura de dados limpa de um Work Item
    após o processamento inicial.
    """
    ID: int
    Type: Optional[str] = None
    Title: Optional[str] = "Sem Título"
    State: Optional[str] = None
    Tags: Optional[str] = ""
    Assigned_To: str = "Unassigned"
    Iteration_Path: Optional[str] = ""
    Parent_ID: Optional[int] = None
    
    # Dados brutos para KPIs
    Raw_Description: Optional[str] = ""
    Clean_Desc_Text: Optional[str] = ""
    Desc_Length: int = 0
    Attachment_Count: int = 0
    Comments_Text: Optional[str] = ""