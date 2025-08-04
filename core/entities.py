from dataclasses import dataclass
from typing import Protocol

class Tool(Protocol):
    name: str
    description: str
    
    async def execute(self, **kwargs) -> dict:
        ...

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict]

class ToolRepository(Protocol):
    async def get_tool(self, name: str) -> Tool:
        ...
    
    async def get_all_tools(self) -> list[Tool]:
        ...

class LLMService(Protocol):
    async def process_query(self, query: str) -> LLMResponse:
        ...
    async def process_single_tool(self, query: str, tool_name: str, args: dict, context:dict) -> LLMResponse:
        ...
    async def summary(self, query: str, context:list) -> str:
        ...
    