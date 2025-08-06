# 🧾 Project Info
This project is a chat-based assistant that helps you manage your Google Calendar and personal notes - just by chatting.

# 🗨️ What can it do?
With this project, you can talk to an AI assistant to:

📅 Create, view, edit, or delete events on your Google Calendar — just like you would in the official app, but using natural language.

📝 Create, organize, edit, or delete personal notes and folders, stored securely in the cloud.

Think of it like having your own smart personal assistant that helps you stay organized — all through chat.

# ✨ Features
This project comes with tools designed to automate and manage user tasks. Currently, the supported tools include:

📅 Google Calendar Tools
- Create Event
  Easily create a new event with title, time, location, and attendees.

- List Events
  Fetch upcoming or past events by specifying date ranges.

- Edit Event
  Modify existing calendar events by updating title, description, time, and other details.

- Delete Event
  Remove an event from the calendar using its title.

📝 Notes Tools
- List Notes
  View all existing notes created by the user.

- Create Note
  Create a new note with a title and content, optionally organized under a folder.

- Get Note
  Retrieve the content of a note by its title.

- Update Note
  Modify an existing note's content and/or title.

- Delete Note
  Permanently delete a note based on its title.

📁 Folder Tools
- List Folders
  View the list of folders available in the system.

- Delete Folder
  Delete a folder by specifying its name.

# ⚙️ Setup
To run the MCP project along with its frontend and backend tool integrations, follow these steps:

1. Frontend (React)
Clone and set up the frontend interface:
```
git clone https://github.com/OrangYangBaik/simple-chatbot-react
cd simple-chatbot-react
npm install
```
2. MCP Core
Clone the MCP core logic and install the required Python dependencies:
```
git clone https://github.com/OrangYangBaik/MCP
cd MCP
pip install -r requirements.txt
```
3. Backend Tools
MCP connects to additional backend services for functionality like calendar and note management.

  Google Calendar Service
```
git clone https://github.com/OrangYangBaik/calendar
go mod tidy
```
  Joplin Note Service
```
git clone https://github.com/OrangYangBaik/joplin
go mod tidy
```
