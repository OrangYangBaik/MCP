from .entities import ToolRepository, LLMService

class ProcessQueryUseCase:
    def __init__(self, llm_service: LLMService, tool_repo: ToolRepository):
        self.llm_service = llm_service
        self.tool_repo = tool_repo
    
    async def execute(self, query: str, access_token: str, files: list[dict] = None) -> dict:
        if access_token and hasattr(self.tool_repo, 'set_access_token'):
            self.tool_repo.set_access_token(access_token)

        response = await self.llm_service.process_query(query)

        if not response.tool_calls:
            return response.content

        results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            args = tool_call["args"]

            if tool_name == "create_note" and files:
                args["files"] = files

            actual_result = await self.execute_tool(tool_name=tool_name, args=args)
            
            data = actual_result.get("data")
            file_blobs = actual_result.get("files", [])
            all_files = []

            if data:
                results.append(f"response from {tool_name}: {data}")

            if file_blobs:
                all_files.extend(file_blobs)

        end_result = await self.llm_service.summary(query=query, context=results)

        return {
            "summary": end_result,
            "files": all_files if all_files else None
        }

    async def execute_tool(self, tool_name: str, args: dict) -> dict:
        tool = await self.tool_repo.get_tool(tool_name)
        return await tool.execute(**args)