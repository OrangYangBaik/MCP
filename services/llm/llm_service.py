from datetime import datetime, timedelta, timezone
import json
from openai import AsyncOpenAI, OpenAIError
from core.entities import LLMResponse
from services.mcp.tool_list import tool_dicts

class LLMClient:
    def __init__(self, model: str, base_url: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
    
    async def process_query(self, query: str) -> LLMResponse:
        try:
            tools = tool_dicts
            
            WIB = timezone(timedelta(hours=7))
            curr_time_wib = datetime.now(WIB)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{
                            "role": "system",
                            "content": (
                                "You are a smart assistant that solves multi-step queries by calling tools in the correct order. "
                            
                                "For example:\n"
                                "User query: 'Delete the event called Lunch with Alex and edit garys birthday event to geri birthday'\n"
                                "Tool calls:\n"
                                "{\"type\":\"function\",\"function\":{\"name\":\"delete_google_calendar_event\",\"arguments\":\"{\\\"event_name\\\":\\\"Gary's birthday\\\"}\"}}]\n\n"
                                "{\"type\":\"function\",\"function\":{\"name\":\"edit_google_calendar_event\",\"arguments\":\"{\\\"prior_event_name\\\":\\\"Gary's birthday\\\", \\\"event_name\\\":\\\"geri birthday\\\"}\"}}]\n\n"

                                "Another example:\n"
                                "User query: 'Please delete the calendar event called Lunch with Alex and Gary's birthday.'\n"
                                "Tool calls:\n"
                                "{\"type\":\"function\",\"function\":{\"name\":\"delete_google_calendar_event\",\"arguments\":\"{\\\"event_name\\\":\\\"Lunch with Alex\\\"}\"}}]\n\n"
                                "{\"type\":\"function\",\"function\":{\"name\":\"delete_google_calendar_event\",\"arguments\":\"{\\\"event_name\\\":\\\"Gary's birthday\\\"}\"}}]\n\n"

                                "Only call tools that are needed. For events name use the exact wording"
                                "All datetime values (such as `start_time` and `end_time`) MUST be in full RFC 3339 format **with timezone offset set to WIB (UTC+07:00)**.\n"
                                "That means use format like `2025-06-18T21:15:15+07:00`. Do **not** use `Z` or leave the timezone blank.\n"
                                "**Do not omit** the timezone offset. **Always output WIB time using `+07:00`.**\n\n"

                                "**Correct format example:**\n"
                                "{\n"
                                "  \"start_time\": \"2025-06-18T10:00:00+07:00\",\n"
                                "  \"end_time\": \"2025-06-18T12:00:00+07:00\"\n"
                                "}\n"
                            )
                        },
                        {"role": "user", "content": "current time is: " + curr_time_wib.isoformat() + ". query: " + query}
                ],
                tools=tools,
                tool_choice="auto",
                temperature= 0.1
            )
            
            if not response.choices:
                return LLMResponse(content="Error: Empty response", tool_calls=[])
            
            message = response.choices[0].message
            tool_calls = []
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        'name': tool_call.function.name,
                        'args': json.loads(tool_call.function.arguments)
                    })
            else:
                 return LLMResponse(
                    content=message.content,
                    tool_calls= None
                )
            
            return LLMResponse(
                content=message.content or "",
                tool_calls=tool_calls
            )
        
        except OpenAIError as e:
            return LLMResponse(content=f"LLM API error: {str(e)}", tool_calls=[])
        except Exception as e:
            return LLMResponse(content=f"Error: {str(e)}", tool_calls=[])
        
    async def process_single_tool(self, query: str, tool_name: str, args: dict) -> dict:
        try:
            tool_needed = next(
                (tool for tool in tool_dicts if tool["function"]["name"] == tool_name),
                None
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are executing a single tool: `{tool_name}`.\n"
                        "Given the user query, tool, and prior knowledge results, resolve any missing or dependent arguments "
                        "and return only the tool arguments in correct format."
                        "JUST CALL ONE TOOL."
                        "All datetime values MUST be in full RFC 3339 format **with timezone offset**.\n"
                        "That means use format like `2025-09-06T13:00:00+07:00` with`+07:00` offset.\n"
                        "**DO NOT OMIT** the timezone offset. If uncertain, use `Z`.\n\n"
                    )
                },
                {
                    "role": "user",
                    "content": f"User query: {query}\nArgs: {json.dumps(args)}\n"
                }
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[tool_needed],
                temperature= 0.1
            )

            if not response.choices or not response.choices[0].message.tool_calls:
                raise ValueError("No tool call returned")

            tool_call = response.choices[0].message.tool_calls[0]
            updated_args = json.loads(tool_call.function.arguments)
            return updated_args

        except Exception as e:
            raise RuntimeError(f"Error processing single tool: {str(e)}")
    
    async def summary(self, query: str, context: list) -> str:
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that summarizes the context based on the query.\n"
                        "Context is the result of the system backend.\n"
                        "Given context, generate a warm, natural-sounding summary.\n"
                        "If the context is a list, present the summary using a bulleted or numbered list that includes relevant details for each item.\n"
                        "If the context is a single object or paragraph, summarize it concisely in a human-like tone.\n"
                        "Be concise, friendly, and sound natural — not robotic or overly formal.\n"
                        "Avoid making up information thats not in the context. Only summarize what's given.\n"
                        "DO NOT CHANGE the information from tool response, just use as is"
                        "DO NOT TELL THE USER ANY ID, OMIT THE IDS"
                        "if there are list make them stacking, use '\n' for that"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"query:\n{query}\n\n"
                        f"context:\n{json.dumps(context)}\n\n"
                        "summarize them"
                    )
                }
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature= 0.3
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"Error processing single tool: {str(e)}")