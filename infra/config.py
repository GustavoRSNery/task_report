from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import base64

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    AZURE_PAT: str = Field(..., description="Personal Access Token do Azure DevOps")
    AZURE_ORG_URL: str = Field(..., description="URL da Organização")
    AZURE_PROJECT: str = Field(..., description="Nome do Projeto")
    AZURE_TAG_FILTER: str = Field("CoE", description="Tag obrigatória para filtrar")
    
    @property
    def headers(self):
        credentials = f":{self.AZURE_PAT}".encode("utf-8")
        b64_auth = base64.b64encode(credentials).decode("utf-8")
        return {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/json"
        }

settings = Settings()