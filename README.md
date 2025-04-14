# gotquery

A learning project that integrates MCP, FastAPI, and Milvus. The project stores the script of the first season of *Game of Thrones* to allow querying over its content. This serves as a practical example of how to integrate modern API frameworks with cutting-edge vector search technology and flexible communication protocols.

## Overview

This project is designed for learning and experimentation with MCP: 
- **MCP** (Model Context Protocol) to handle communication between the LLM and the tools.
- **FastAPI** to create a high-performance web API.
- **Milvus** as a vector database for similarity search operations.

## Features

### /query Endpoint

- **User Query Integration:**  
  The `/query` endpoint is designed as a POST route where users can send their queries to the application. The query is then forwarded to an LLM for processing.

- **Dynamic Tooling via MCP:**  
  After receiving the user's query, the system retrieves a list of available tools using MCP. These tools, each defined with an input schema and description, are then passed along with the query to the LLM.

- **LLM and Tool Interaction:**  
  The LLM receives both the user's query and the structured tools information. It has the ability to call these tools dynamically based on the context of the query, enabling it to perform tasks such as fetching subtitles or executing other defined actions through MCP.


## Setup

### Prerequisites

- uv installed

### Steps to Run the Application

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/pablolobat0/gotquery.git
   cd gotquery
   ```
2. **Configure Environment Variables:** Create a .env file in the project root with the required variables. For example:
   ```bash
   API_KEY=your_anthropic_api_key_here
   ```
3. **Run the Application:**
```bash
   uv run fastapi dev
   ```

The application will be served at http://127.0.0.1:8000. API documentation is available at http://127.0.0.1:8000/docs.
   

