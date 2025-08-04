tool_dicts = [
           {
            "type": "function",
            "function": {
                "name": "create_google_calendar_event",
                "description": "Create a new event in Google Calendar.",
                "parameters": {
                "type": "object",
                "properties": {
                    "summary": { "type": "string", "description": "Title of the event" },
                    "description": { "type": "string", "description": "Details of the event" },
                    "start_time": { "type": "string", "description": "Start time (RFC 3399)" },
                    "end_time": { "type": "string", "description": "End time (RFC 3399)" },
                    "location": { "type": "string", "description": "Location or link" },
                    "attendees": {
                        "type": "array",
                        "description": "Email addresses of participants",
                        "items": { "type": "string", "format": "email" }
                    }
                },
                "required": ["summary", "start_time", "end_time"],
                "additionalProperties": False
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "list_google_calendar_events",
                "description": "List events from Google Calendar for a specified date or range.",
                "parameters": {
                "type": "object",
                "properties": {
                    "start_date": { "type": "string", "description": "Start date (RFC 3399)" },
                    "end_date": { "type": "string", "description": "End date (RFC 3399)" }
                },
                "required": [],
                "additionalProperties": False
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "edit_google_calendar_event",
                "description": "Edit an existing event in Google Calendar.",
                "parameters": {
                "type": "object",
                "properties": {
                    "prior_event_name": { "type": "string", "description": "Prior title of the event" },
                    "summary": { "type": "string", "description": "New event title" },
                    "description": { "type": "string", "description": "New event details (optional)" },
                    "start_time": { "type": "string", "description": "New start time (RFC 3399, optional)" },
                    "end_time": { "type": "string", "description": "New end time (RFC 3399, optional)" },
                    "location": { "type": "string", "description": "New location (optional)" },
                    "attendees": {
                        "type": "array",
                        "description": "Email addresses of participants",
                        "items": { "type": "string", "format": "email" }
                    }
                },
                "required": ["summary", "prior_event_name"],
                "additionalProperties": False
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "delete_google_calendar_event",
                "description": "Delete an event from Google Calendar by its event name.",
                "parameters": {
                "type": "object",
                "properties": {
                    "summary": { "type": "string", "description": "title of the event to delete" }
                },
                "required": ["summary"],
                "additionalProperties": False
                }
            }
            },
             {
            "type": "function",
            "function": {
                "name": "delete_google_calendar_event",
                "description": "Delete an event from Google Calendar by its event name.",
                "parameters": {
                "type": "object",
                "properties": {
                    "summary": { "type": "string", "description": "title of the event to delete" }
                },
                "required": ["summary"],
                "additionalProperties": False
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "list_notes",
                "description": "List existing user's notes",
            }
            },
            {
            "type": "function",
            "function": {
                "name": "list_folders",
                "description": "List existing user's folders",
            }
            },
            {
            "type": "function",
            "function": {
                "name": "create_note",
                "description": "Create a new note.",
                "parameters": {
                "type": "object",
                "properties": {
                    "title": { "type": "string", "description": "Title of the note" },
                    "body": { "type": "string", "description": "Body of the note" },
                    "folder_name": { "type": "string", "description": "Folder location for the note" },
                },
                "required": ["title", "body"],
                "additionalProperties": False
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "get_note",
                "description": "get an existing note.",
                "parameters": {
                "type": "object",
                "properties": {
                    "title": { "type": "string", "description": "Title of the note" }
                },
                "required": ["title"],
                "additionalProperties": False
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "update_note",
                "description": "update an existing note.",
                "parameters": {
                "type": "object",
                "properties": {
                    "title": { "type": "string", "description": "Title of the note" },
                    "new_title": { "type": "string", "description": "New title of the note" },
                    "body": { "type": "string", "description": "Addtion to the body of the note" }
                },
                "required": ["title", "body"],
                "additionalProperties": False
                }
            }
            },
            {
            "type": "function",
            "function": {
                "name": "delete_note",
                "description": "delete a note.",
                "parameters": {
                "type": "object",
                "properties": {
                    "title": { "type": "string", "description": "Title of the note" },
                },
                "required": ["title"],
                "additionalProperties": False
                }
            }
            }
        ]

