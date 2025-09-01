# JJCIMS MySQL & FastAPI Integration Guide

This guide explains how to migrate JJCIMS from Microsoft Access to a networked MySQL database with FastAPI, allowing multi-computer access across different networks.

## Overview of Changes

The original JJCIMS used a local Microsoft Access database (JJCIMS.accdb) with direct connections via pyodbc. The new architecture:

1. Replaces the Access database with MySQL for improved concurrency and network access
2. Adds a FastAPI backend that acts as the central point for all database operations
3. Implements a compatible connector that preserves the original database interface
4. Uses environment variables to switch between Access and MySQL modes

## Architecture

```
┌───────────────────┐          ┌──────────────────┐          ┌────────────────┐
│                   │          │                  │          │                │
│ JJCIMS Client    │  HTTP/S  │  FastAPI Server  │   SQL    │  MySQL Server  │
│ (any computer)   │ ◄────────┤  (central host)  │ ◄────────┤  (database)    │
│                   │          │                  │          │                │
└───────────────────┘          └──────────────────┘          └────────────────┘
```

## Installation

### 1. Set Up MySQL Database

1. Install MySQL Server on your central server
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install mysql-server
   
   # Windows
   # Download MySQL Installer from https://dev.mysql.com/downloads/installer/
   ```

2. Create database and user
   ```sql
   CREATE DATABASE jjcims_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'jjcims_user'@'%' IDENTIFIED BY 'your_secure_password';
   GRANT ALL PRIVILEGES ON jjcims_db.* TO 'jjcims_user'@'%';
   FLUSH PRIVILEGES;
   ```

### 2. Deploy FastAPI Server

1. Create a virtual environment
   ```bash
   python -m venv env-api
   source env-api/bin/activate  # Linux/Mac
   env-api\Scripts\activate     # Windows
   ```

2. Install dependencies
   ```bash
   cd backend/api
   pip install -r requirements.txt
   ```

3. Configure environment variables
   - Create `.env` file in the server directory with database credentials
   - See `.env` file in the root directory for reference

4. Initialize the database
   ```python
   from main import Base, engine
   Base.metadata.create_all(bind=engine)
   ```

5. Run the server
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

6. For production, use gunicorn with uvicorn workers:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   ```

### 3. Migrate Data from Access to MySQL

You can use one of these approaches to migrate your data:

1. **API-based migration**: Write a script using both connectors to transfer data
2. **Direct export/import**: Use a tool like DBeaver or MySQL Workbench to move data
3. **Manual SQL creation**: Generate SQL from Access schema and import to MySQL

Example of API-based migration script:
```python
from backend.database import get_connector
import os

# Use Access connector for source
os.environ["JJCIMS_DB_TYPE"] = "access"
access_connector = get_connector()

# Use MySQL connector for destination
os.environ["JJCIMS_DB_TYPE"] = "mysql"
mysql_connector = get_connector()

# Example: Migrate items
items = access_connector.fetchall("SELECT * FROM [ITEMSDB]")
for item in items:
    # Convert item to new format and send to API
    # This is a simplified example - you'll need to adapt to your schema
    pass
```

### 4. Configure Clients

1. Install client requirements:
   ```bash
   pip install python-dotenv requests
   ```

2. Configure environment to use MySQL:
   ```
   # .env file
   JJCIMS_DB_TYPE=mysql
   JJCIMS_API_URL=http://your-server-ip:8000
   ```

## Security Considerations

1. **API Authentication**: Add JWT authentication to FastAPI
2. **HTTPS**: Set up HTTPS with a reverse proxy (Nginx/Apache)
3. **Firewall**: Configure firewall to restrict access to the API
4. **MySQL Security**: Use strong passwords and restrict MySQL access

## Troubleshooting

### Connection Issues
- Check that the API server is running
- Ensure the API URL in .env is correct
- Test connectivity with: `curl http://your-server-ip:8000/items/`

### Data Migration Issues
- Verify table schemas match between Access and MySQL
- Check character encoding (use utf8mb4 in MySQL)
- Handle data type differences between Access and MySQL

### API Errors
- Check FastAPI logs for detailed error messages
- Verify that all API endpoints are properly implemented
- Test endpoints using the Swagger UI: http://your-server-ip:8000/docs

## Live Updates for Multi-Computer Access

The FastAPI-based architecture naturally supports multi-computer access across different networks:

1. **Central API Server**: All clients connect to the same API server
2. **Real-Time Updates**: Implement WebSockets for push notifications
3. **Connection Management**: FastAPI handles concurrent connections efficiently

### Adding WebSocket Notifications (Optional Enhancement)

To support real-time updates across clients:

1. Add WebSocket endpoint to FastAPI:
   ```python
   from fastapi import WebSocket, WebSocketDisconnect
   
   # In main.py
   class ConnectionManager:
       def __init__(self):
           self.active_connections = []
   
       async def connect(self, websocket: WebSocket):
           await websocket.accept()
           self.active_connections.append(websocket)
   
       def disconnect(self, websocket: WebSocket):
           self.active_connections.remove(websocket)
   
       async def broadcast(self, message: dict):
           for connection in self.active_connections:
               await connection.send_json(message)
   
   manager = ConnectionManager()
   
   @app.websocket("/ws")
   async def websocket_endpoint(websocket: WebSocket):
       await manager.connect(websocket)
       try:
           while True:
               data = await websocket.receive_text()
               # Process incoming messages if needed
       except WebSocketDisconnect:
           manager.disconnect(websocket)
   ```

2. Broadcast changes after database modifications:
   ```python
   @app.post("/items/", response_model=Item)
   async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
       db_item = ItemDB(**item.dict())
       db.add(db_item)
       db.commit()
       db.refresh(db_item)
       
       # Broadcast the change to all connected clients
       await manager.broadcast({
           "type": "item_created",
           "data": jsonable_encoder(db_item)
       })
       
       return db_item
   ```

3. Connect from client:
   ```python
   import websocket
   import json
   import threading
   
   def on_message(ws, message):
       data = json.loads(message)
       # Process updates based on type
       if data["type"] == "item_created":
           # Update UI with new item
           pass
   
   def start_websocket():
       ws = websocket.WebSocketApp(
           "ws://your-server-ip:8000/ws",
           on_message=on_message
       )
       ws.run_forever()
   
   # Start WebSocket connection in background thread
   threading.Thread(target=start_websocket, daemon=True).start()
   ```

## Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- MySQL Documentation: https://dev.mysql.com/doc/
- WebSockets with FastAPI: https://fastapi.tiangolo.com/advanced/websockets/
