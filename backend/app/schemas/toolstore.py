"""Tool Store schemas."""

from pydantic import BaseModel


class ToolInstallRequest(BaseModel):
    tool_id: str


class ToolInstallResponse(BaseModel):
    status: str
    tool_id: str
    needs_restart: bool


class CategoryResponse(BaseModel):
    id: str
    name: str
    icon: str


class ToolResponse(BaseModel):
    id: str
    name: str
    type: str
    category: str
    description: str
    icon: str
    author: str
    tags: list[str]
    popularity: int


class CatalogResponse(BaseModel):
    tools: list[ToolResponse]
    categories: list[CategoryResponse]
