import aiohttp_cors
import anyio
import os
import json
import logging

from services.mcp.mcp_service import MCPService
from services.llm.llm_service import LLMClient
from core.use_cases import ProcessQueryUseCase
from aiohttp import web
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_query_request(request: web.Request) -> web.Response:
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return web.json_response({"error": "Missing or invalid Authorization header"}, status=401)
        access_token = auth_header.split("Bearer ")[1]

        content_type = request.content_type

        if content_type.startswith("application/json"):
            data = await request.json()
            query = data.get("query")
            files = None

        elif content_type.startswith("multipart/form-data"):
            reader = await request.multipart()

            query = None
            files = []

            async for part in reader:
                if part.name == "query":
                    query = await part.text()
                elif part.name == "files[]":
                    filename = part.filename
                    file_data = await part.read()
                    files.append({"filename": filename, "data": file_data})

        else:
            logging.error({"error": f"Unsupported Content-Type: {content_type}"})
            return web.json_response({"error": f"Unsupported Content-Type: {content_type}"}, status=415)

        if not query:
            logging.error({"error": "Missing 'query' in request"})
            return web.json_response({"error": "Missing 'query' in request"}, status=400)

        use_case = request.app["use_case"]
        result = await use_case.execute(query, access_token=access_token, files=files)

        if files:
            files.clear()
            del files

        return web.json_response({"result": result})
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def start_http_server(use_case, host: str, port: int):
    app = web.Application()
    app["use_case"] = use_case
    
    query_route = app.router.add_post("/query", handle_query_request)

    cors = aiohttp_cors.setup(app, defaults={
        "http://localhost:5173": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    cors.add(query_route)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner

async def main():
    load_dotenv()
    
    mcp_service = MCPService(host= os.getenv("MCP_HOST"), port= int(os.getenv("MCP_PORT")))
    llm_client = LLMClient(
        model= os.getenv("MODEL_NAME"),
        base_url= os.getenv("MODEL_BASE_URL"),
        api_key= os.getenv("MODEL_API_KEY")
    )
    
    use_case = ProcessQueryUseCase(
        llm_service=llm_client,
        tool_repo=mcp_service
    )
    
    http_runner = None
    async with anyio.create_task_group() as tg:
        # Start MCP server
        tg.start_soon(mcp_service.run)
        # Start HTTP server
        http_runner = await start_http_server(use_case, host=os.getenv("API_HOST"), port=int(os.getenv("API_PORT")))
        
        try:
            await anyio.sleep(float("inf"))
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            if http_runner:
                await http_runner.cleanup()

if __name__ == "__main__":
    anyio.run(main)