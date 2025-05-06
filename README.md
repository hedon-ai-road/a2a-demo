# A2A Demo: Echo Agent with Ollama Integration

## Overview

This project demonstrates a simple implementation of Google's Agent-to-Agent (A2A) protocol with Ollama LLM integration. The demo creates an Echo Agent that can receive user messages and respond with AI-generated content using the Ollama API. Refer to [A2A Protocol](https://google.github.io/A2A/tutorials/python/1-introduction/) for more details.

## Project Structure

- `src/a2a_demo/__init__.py`: Main entry point that configures and starts the A2A server
- `src/a2a_demo/agent.py`: LLM integration with Ollama using LangChain and LangGraph
- `src/a2a_demo/task_manager.py`: Custom task manager that handles A2A protocol requests

## How It Works

### Architecture

The A2A Demo follows a client-server architecture defined by Google's A2A protocol:

1. **A2A Server**: Exposes an HTTP API that implements the A2A protocol endpoints
2. **Task Manager**: Handles incoming tasks and manages their lifecycle
3. **LLM Integration**: Connects to Ollama for generating AI responses
4. **Streaming Support**: Provides real-time updates during task processing

### Components and Flow

```
┌───────────────┐    HTTP/A2A     ┌─────────────────┐    LLM API     ┌─────────────┐
│  A2A Client   │───────────────> │  A2A Server     │───────────────>│   Ollama    │
│ (Any A2A App) │ <───────────────│ (Echo Agent)    │ <──────────────│ (LLM Model) │
└───────────────┘                 └─────────────────┘                └─────────────┘
                                         │
                                         │
                                 ┌───────▼───────┐
                                 │  Task Manager │
                                 └───────────────┘
```

#### 1. Server Initialization

In `__init__.py`, the application:

- Configures the agent with an `AgentSkill` for echo functionality
- Sets up `AgentCapabilities` (enabling streaming)
- Creates an `AgentCard` with metadata about the agent
- Initializes the `MyAgentTaskManager` with Ollama connection parameters
- Starts the A2A server on the specified host and port

#### 2. LLM Integration

In `agent.py`, the application:

- Creates an Ollama agent using LangChain and LangGraph
- Provides a `run_ollama` function to send prompts to the LLM and receive responses
- Uses the ReAct agent pattern for reasoning capabilities

#### 3. Task Management

In `task_manager.py`, the custom `MyAgentTaskManager` class:

- Handles both standard and streaming A2A protocol requests
- Implements `on_send_task` for synchronous requests
- Implements `on_send_task_subscribe` for streaming responses
- Manages the task lifecycle (working -> input_required -> completed)
- Sends AI-generated responses back to the client

### Key Features

#### Streaming Responses

The agent supports streaming responses through the A2A protocol's Server-Sent Events (SSE) mechanism. This allows clients to receive real-time updates as the agent processes tasks.

#### Interactive Dialog

The task manager implements a simple interactive dialog pattern:

1. Client sends initial message
2. Server streams three AI-generated responses using Ollama
3. Server asks if the user wants more messages (Y/N)
4. If the user responds with "Y", the process repeats
5. If the user responds with "N", the task is marked as completed

#### LLM Integration

The agent integrates with the Ollama API to generate responses using large language models:

- Configurable model selection (default: llama3.2)
- Adjustable generation parameters (temperature, etc.)
- Structured API for sending prompts and receiving responses

## Usage

To run the A2A Echo Agent:

```bash
uv run -m a2a_demo --host localhost --port 10002 --ollama-host http://127.0.0.1:11434 --ollama-model llama3.2
```

Parameters:

- `--host`: Host to bind the server to (default: localhost)
- `--port`: Port to listen on (default: 10002)
- `--ollama-host`: URL of the Ollama API server (default: http://127.0.0.1:11434)
- `--ollama-model`: Ollama model to use (default: llama3.2)

## A2A Protocol Flow

The A2A protocol implementation follows this flow:

1. **Discovery**: Clients can discover the agent's capabilities via its Agent Card
2. **Task Creation**: Clients create tasks by sending messages to the agent
3. **Processing**: The agent processes tasks and generates responses using Ollama
4. **Streaming**: For streaming requests, the agent sends incremental updates
5. **Interaction**: The agent can request additional input from the client
6. **Completion**: Tasks reach a final state (completed, failed, canceled)

## Technical Details

### A2A Protocol Implementation

This demo uses Google's A2A protocol, which defines:

- Agent Cards for discovery and capability advertisement
- Task management for handling work units
- Message exchange for communication
- Streaming for real-time updates
- State management for task tracking

### LangChain and LangGraph Integration

The demo uses:

- LangChain for LLM integration with Ollama
- LangGraph for creating a ReAct agent pattern
- Async/await pattern for non-blocking operation
