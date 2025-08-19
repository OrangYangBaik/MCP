import base64
from dataclasses import dataclass
import json
import logging
from typing import Optional
import aiohttp
from fastmcp import FastMCP
from core.entities import Tool
from thefuzz import fuzz
import dateutil.parser

logging.basicConfig(level=logging.INFO)

@dataclass
class BaseTool:
    list_tool: Tool
    access_token: Optional[str] = None

    def set_access_token(self, token: str):
        self.access_token = token
        if hasattr(self.list_tool, 'set_access_token'):
            self.list_tool.set_access_token(token)

@dataclass
class CreateEventTool(BaseTool, Tool):
    name: str = "create_google_calendar_event"
    description: str = "Create a new event in Google Calendar. If the event already exists, returns the existing one."

    async def execute(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[list[str]] = None
    ) -> dict:
        events_result = await self.list_tool.execute()
        events = events_result.get("data", [])

        if events:
            for e in events:
                score1 = fuzz.partial_ratio(e.get("summary", ""), summary)
                score2 = fuzz.token_set_ratio(e.get("summary", ""), summary)
                
                score = (score1 + score2) // 2

                if score > 90:
                    dt = dateutil.parser.isoparse(e['start_time'])

                    if start_time == e['start_time']:
                        return {"data": f"Event '{summary}' already exists at {dt}"}
            
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8080/calendar/events"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }

                final_attendees = [{"email": a} for a in (attendees or [])]

                params = [
                    {
                        "summary": summary,
                        "description": description,
                        "location": location,
                        "start_time": start_time,
                        "end_time": end_time,
                        "attendees": final_attendees
                    }
                ]
                async with session.post(url, headers=headers, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"data": data}
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to create event: {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to create event: {str(e)}"}

@dataclass
class EditEventTool(BaseTool, Tool):
    name: str = "edit_google_calendar_event"
    description: str = "Edit an existing Google Calendar event by its name."

    async def execute(
        self,
        prior_event_name: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[list[str]] = None
    ) -> dict:
        events_result = await self.list_tool.execute()
        events = events_result.get("data", [])
        
        found = False
        if events:
            for e in events:
                score1 = fuzz.partial_ratio(e.get("summary", ""), prior_event_name)
                score2 = fuzz.token_set_ratio(e.get("summary", ""), prior_event_name)
                
                score = (score1 + score2) // 2

                if score > 80:
                    eventId = e['id']
                    curr_start_time = e['start_time']
                    curr_end_time = e['end_time']
                    found = True
                    break

        try:
            if not found:
                raise ValueError("The event was not found")
            
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8080/calendar/edit/events"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }

                final_attendees = [{"email": a} for a in (attendees or [])]

                if start_time == None:
                    start_time = curr_start_time
                
                if end_time == None:
                    end_time = curr_end_time

                params = {
                        "id": eventId,
                        "summary": summary,
                        "description": description,
                        "location": location,
                        "start_time": start_time,
                        "end_time": end_time,
                        "attendees": final_attendees
                    }
                async with session.post(url, headers=headers, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"data": data}
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to edit event: {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to edit event: {str(e)}"}

@dataclass
class DeleteEventTool(BaseTool, Tool):
    name: str = "delete_google_calendar_event"
    description: str = "Delete an event from Google Calendar by its name."

    async def execute(self, summary: str) -> dict:
        events_result = await self.list_tool.execute()
        events = events_result.get("data", [])

        if events:
            for e in events:
                score1 = fuzz.partial_ratio(e.get("summary", ""), summary)
                score2 = fuzz.token_set_ratio(e.get("summary", ""), summary)
                
                score = (score1 + score2) // 2
                if score > 80:
                    eventId = e['id']
                    break

        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8080/calendar/delete/events/{eventId}"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }

                async with session.post(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"data": data}
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to edit event: {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to edit event: {str(e)}"}

@dataclass
class ListEventsTool(Tool):
    name: str = "list_google_calendar_events"
    description: str = "List upcoming events within a time range."
    access_token: Optional[str] = None

    def set_access_token(self, token: str):
        self.access_token = token

    async def execute(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8080/calendar/events"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }

                params = {
                    "calendar_id": "primary",
                    "from": start_date,
                    "to": end_date,
                }

                async with session.get(url, headers=headers, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = []
                        i = 1
                        for item in data:
                            events.append({
                                "event_number": (i),
                                "id": item.get("id"),
                                "summary": item.get("summary", "No title"),
                                "start_time": item.get("start_time"),
                                "end_time": item.get("end_time"),
                                "location": item.get("location"),
                                "description": item.get("description")
                            })
                        i += 1
                        return {"data": events}
                    else:
                        error_text = await response.text()
                        print(f"Failed to get event list: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            print(f"Failed to get event list: {str(e)}")
            return {}

@dataclass
class ListNotesTool(Tool):
    name: str = "list_notes"
    description: str = "List existing user's notes."
    access_token: Optional[str] = None

    def set_access_token(self, token: str):
        self.access_token = token

    async def execute(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8081/storage/notes"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        notes = []
                        for i, item in enumerate(data['data'], start=1):
                            notes.append({
                                "note_number": i,
                                "id": item.get("id"),
                                "title": item.get("title")
                            })
                        return {"data": notes}
                    else:
                        error_text = await response.text()
                        print(f"Failed to get note list: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            print(f"Failed to get note list: {str(e)}")
            return {}

@dataclass
class ListFoldersTool(Tool):
    name: str = "list_folder"
    description: str = "List existing user's folders."
    access_token: Optional[str] = None

    def set_access_token(self, token: str):
        self.access_token = token

    def extract_folders(self, folders):
        result = []
        for i, folder in enumerate(folders, start=1):
            entry = {
                "id": folder.get("id"),
                "title": folder.get("title"),
                "parent_id": folder.get("parent_id"),
            }
            result.append(entry)

            children = folder.get("children", [])
            if children:
                result.extend(self.extract_folders(children))
        
        return result

    async def execute(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8081/storage/folders"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        folders = self.extract_folders(data["data"])
                        return {"data": folders}
                    else:
                        error_text = await response.text()
                        print(f"Failed to get folder list: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            print(f"Failed to get folder list: {str(e)}")
            return {}

@dataclass
class DeleteFolderTool(BaseTool, Tool):
    name: str = "delete_folder"
    description: str = "delete an existing folder"

    async def execute(
        self,
        title: str
    ) -> dict:
        folder_result = await self.list_tool.execute()
        notes = folder_result.get("data", [])
        if notes:
            if title:
                for e in notes:
                    score1 = fuzz.partial_ratio(e.get("title", ""), title)
                    score2 = fuzz.token_set_ratio(e.get("title", ""), title)
                    
                    score = (score1 + score2) // 2

                    if score > 90:
                        folder_id = e.get("id")
                        break
                    else :
                        folder_id = ""

        try:
            if not folder_id:
                return {"data": f"there are no folder titled {title}"}
            
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8081/storage/folder/delete?folder_id={folder_id}"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }
                
                async with session.post(url, headers=headers) as response:
                    if response.status == 200:
                        return {"data": f"Folder deleted successfully"}
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to delete {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to delete folder: {str(e)}"}
    
@dataclass
class CreateNoteTool(BaseTool, Tool):
    name: str = "create_note"
    description: str = "Create a new note"

    async def execute(
        self,
        title: str,
        body: str,
        folder_name: Optional[str] = None, 
        files: list = None
    ) -> dict:
        folders_result  = await self.list_tool.execute()
        if folders_result.get("data") is None:
            folders = []
        else:
            folders = folders_result.get("data", [])

        if folders:
            if folder_name:
                for e in folders:
                    score1 = fuzz.partial_ratio(e.get("title", ""), folder_name)
                    score2 = fuzz.token_set_ratio(e.get("title", ""), folder_name)
                    
                    score = (score1 + score2) // 2

                    if score > 90:
                        parent_id = e.get("id")
            else:
                parent_id = ""
        else:
            parent_id = ""

        try:
            data = {
                "title": title,
                "body": body,
                "parent_id": parent_id,
                "folder_tree": json.dumps(folders),
            }
            form_data = aiohttp.FormData()
            form_data.add_field("title", str(data["title"]))
            form_data.add_field("body", str(data["body"]))
            form_data.add_field("parent_id", str(data["parent_id"]))
            form_data.add_field(
                "folder_tree",
                data["folder_tree"],
                content_type="application/json"
            )
            if files:
                for file in files:
                    if isinstance(file, dict):
                        form_data.add_field(
                            name="attachments",
                            value=file["data"],
                            filename=file["filename"],
                            content_type="application/octet-stream"
                        )

            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8081/storage/note"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }

                async with session.post(url, headers=headers, data=form_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"data": f"Note created successfully"}
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to create note: {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to create note: {str(e)}"}

@dataclass
class GetNoteTool(BaseTool, Tool):
    name: str = "get_note"
    description: str = "Get an existing note"

    async def execute(
        self,
        title: str
    ) -> dict:
        notes_result = await self.list_tool.execute()
        notes = notes_result.get("data", [])
        if notes:
            if title:
                for e in notes:
                    score1 = fuzz.partial_ratio(e.get("title", ""), title)
                    score2 = fuzz.token_set_ratio(e.get("title", ""), title)
                    
                    score = (score1 + score2) // 2

                    if score > 90:
                        note_id = e.get("id")
                        break
                    else :
                        note_id = ""

        try:
            if not note_id:
                return {"data": f"there are no note titled {title}"}
            
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8081/storage/note/show"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }
                
                params = {
                    "id": note_id,
                }
                
                async with session.get(url, headers=headers, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        note = data["data"]["note"]
                        files = data["data"]["resources"]

                        summary = f"{note.get('title', '')}\n\n{note.get('body', '')}".strip()
                        result = {"data": summary}

                        file_blobs = []
                       
                        if files:
                            for file in files:
                                resource_url = f"http://localhost:8081/storage/resource?resource_id={file.get('id')}"
                                headers = {
                                    "Authorization": f"Bearer {self.access_token}",
                                    "Accept": "application/json",
                                }

                                async with aiohttp.ClientSession() as inner_session:
                                    async with inner_session.get(resource_url, headers=headers) as resource_response:
                                        if resource_response.status == 200:
                                            content = await resource_response.read()
                                            mime_type = resource_response.headers.get("Content-Type", "application/octet-stream")
                                            filename = file.get("title")

                                            file_blobs.append({
                                                "id": file.get("id"),
                                                "title": filename,
                                                "mime_type": mime_type,
                                                "blob": base64.b64encode(content).decode("utf-8"),
                                            })
                        if file_blobs:
                            result["files"] = file_blobs
                    
                        return result
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to get {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to get note: {str(e)}"}

@dataclass
class UpdateNoteTool(BaseTool, Tool):
    name: str = "update_note"
    description: str = "Update an existing note"

    async def execute(
        self,
        title: str,
        new_title: Optional[str] = None,
        body: Optional[str] = None
    ) -> dict:
        notes_result = await self.list_tool.execute()
        notes = notes_result.get("data", [])

        if notes:
            if title:
                for e in notes:
                    score1 = fuzz.partial_ratio(e.get("title", ""), title)
                    score2 = fuzz.token_set_ratio(e.get("title", ""), title)
                    
                    score = (score1 + score2) // 2
                    if score > 90:
                        note_id = e.get("id")
                        break
                    else :
                        note_id = ""

        try:
            if not note_id:
                return {"data": f"there are no note titled {title}"}
            
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8081/storage/note/update"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }
                
                params = {
                    "id": note_id,
                }

                if new_title:
                    params.update({"title": new_title})
                if body:
                    params.update({"body": body})
                
                async with session.post(url, headers=headers, json=params) as response:
                    if response.status == 200:
                        return {"data": f"Note updated successfully"}
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to update {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to update note: {str(e)}"}

@dataclass
class DeleteNoteTool(BaseTool, Tool):
    name: str = "delete_note"
    description: str = "delete an existing note"

    async def execute(
        self,
        title: str
    ) -> dict:
        notes_result = await self.list_tool.execute()
        notes = notes_result.get("data", [])
        if notes:
            if title:
                for e in notes:
                    score1 = fuzz.partial_ratio(e.get("title", ""), title)
                    score2 = fuzz.token_set_ratio(e.get("title", ""), title)
                    
                    score = (score1 + score2) // 2

                    if score > 90:
                        note_id = e.get("id")
                        break
                    else :
                        note_id = ""

        try:
            if not note_id:
                return {"data": f"there are no note titled {title}"}
            
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8081/storage/note/delete?note_id={note_id}"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }
                
                async with session.post(url, headers=headers) as response:
                    if response.status == 200:
                        return {"data": f"Note deleted successfully"}
                    else:
                        error_text = await response.text()
                        return {"data": f"Failed to delete {response.status} - {error_text}"}
        except Exception as e:
            return {"data": f"Failed to delete note: {str(e)}"}
        
class MCPService:
    def __init__(self, host, port):
        self.mcp = FastMCP("MCP")
        self.access_token = None
        list_event_tool = ListEventsTool()
        list_note_tool = ListNotesTool()
        list_folder_tool = ListFoldersTool()
        self.tools = {
            "create_google_calendar_event": CreateEventTool(list_tool=list_event_tool),
            "edit_google_calendar_event": EditEventTool(list_tool=list_event_tool),
            "delete_google_calendar_event": DeleteEventTool(list_tool=list_event_tool),
            "list_google_calendar_events": list_event_tool,
            "list_notes": list_note_tool,
            "list_folders": list_folder_tool,
            "delete_folder": DeleteFolderTool(list_tool=list_folder_tool),
            "create_note": CreateNoteTool(list_tool=list_folder_tool),
            "get_note": GetNoteTool(list_tool=list_note_tool),
            "update_note": UpdateNoteTool(list_tool=list_note_tool),
            "delete_note": DeleteNoteTool(list_tool=list_note_tool)
        }
        self.host = host
        self.port = port
        self._register_tools()

    def set_access_token(self, token: str):
        self.access_token = token
        for tool in self.tools.values():
            if hasattr(tool, 'set_access_token'):
                tool.set_access_token(token)

    def _register_tools(self):
        @self.mcp.tool()
        async def create_google_calendar_event(
            summary: str, 
            start_time: str, 
            end_time: str,
            location: Optional[str] = None,
            description: Optional[str] = None,
            attendees: Optional[list[str]] = None) -> dict:
            return await self.tools["create_google_calendar_event"].execute(
                summary=summary, start_time=start_time, end_time=end_time,
                location=location, description=description, attendees=attendees
            )

        @self.mcp.tool()
        async def edit_google_calendar_event(prior_event_name: str, 
                                             summary: str,
                                             start_time: Optional[str] = None,
                                             end_time: Optional[str] = None,
                                             location: Optional[str] = None,
                                             description: Optional[str] = None,
                                             attendees: Optional[list[str]] = None) -> dict:
            return await self.tools["edit_google_calendar_event"].execute(
                prior_event_name=prior_event_name, summary=summary, start_time=start_time,
                end_time=end_time, location=location, description=description, attendees= attendees
            )

        @self.mcp.tool()
        async def delete_google_calendar_event(summary: str) -> dict:
            return await self.tools["delete_google_calendar_event"].execute(summary=summary)

        @self.mcp.tool()
        async def list_google_calendar_events(start_date: Optional[str] = None,
                                              end_date: Optional[str] = None) -> dict:
            return await self.tools["list_google_calendar_events"].execute(start_date=start_date, end_date=end_date)
        
        @self.mcp.tool()
        async def list_notes() -> dict:
            return await self.tools["list_notes"].execute()
        
        @self.mcp.tool()
        async def list_folders() -> dict:
            return await self.tools["list_folders"].execute()

        @self.mcp.tool()
        async def create_note(
            title: str,
            body: str,
            folder_name: Optional[str] = None, 
            files: list = None) -> dict:
            return await self.tools["create_note"].execute(
                title=title, body=body, folder_name=folder_name, files=files
            )
        
        @self.mcp.tool()
        async def get_note(
            title: str) -> dict:
            return await self.tools["get_note"].execute(
                title=title
            )
        
        @self.mcp.tool()
        async def update_note(
            title: str, 
            new_title: Optional[str] = None,
            body: Optional[str] = None) -> dict:
            return await self.tools["update_note"].execute(
                title=title, new_title=new_title, body=body
            )
        
        @self.mcp.tool()
        async def delete_note(
            title: str) -> dict:
            return await self.tools["delete_note"].execute(
                title=title
            )
        
    async def run(self):
        await self.mcp.run_async(transport="streamable-http", host=self.host, port=self.port, path="/mcp")

    async def get_tool(self, name: str) -> Tool:
        tool = self.tools.get(name)

        if hasattr(tool, 'access_token'):
            tool.access_token = self.access_token
        return tool

    async def get_all_tools(self) -> list[Tool]:
        return list(self.tools.values())
