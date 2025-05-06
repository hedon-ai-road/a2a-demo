# True Agent-to-Agent (A2A) Demo

This project demonstrates a true Agent-to-Agent (A2A) interaction using Google's [A2A protocol](https://github.com/google/A2A). It consists of two agents that communicate with each other:

1. **Echo Agent**: The main agent that interacts with the user and delegates math-related questions to the Math Agent.
2. **Math Agent**: A specialized agent that handles mathematical calculations.

## Architecture

```
┌───────────────┐           ┌───────────────┐
│               │  Delegates│               │
│   Echo Agent  ├──────────►│   Math Agent  │
│               │  Math Qs  │               │
└───────┬───────┘           └───────────────┘
        │
        │ Interacts
        │
        ▼
┌───────────────┐
│               │
│      User     │
│               │
└───────────────┘
```

The system works as follows:

1. The user sends requests to the Echo Agent
2. The Echo Agent analyzes the request:
   - If it's a math-related question, it delegates to the Math Agent
   - Otherwise, it handles the request itself
3. The Math Agent processes mathematical calculations and returns results
4. The Echo Agent returns the final response to the user

## A2A Protocol Implementation

This project implements the Google A2A protocol, allowing agents to:

- Register and discover each other's capabilities
- Send tasks to each other
- Process and return results

The implementation uses the following key components:

- **Agent Cards**: JSON descriptions of each agent's capabilities
- **Task Manager**: Handles processing and delegating tasks
- **Server**: Manages HTTP communication between agents

## Fault Tolerance

The system includes robust fault tolerance mechanisms:

- **Connection Retry**: The Echo Agent attempts multiple reconnections to the Math Agent if the initial connection fails
- **Local Fallback**: If the Math Agent is unavailable or fails to respond, the Echo Agent can solve basic math problems locally
- **Error Handling**: Comprehensive error handling ensures the system remains operational even during service disruptions

## Running the Demo

You can run the agents in different ways:

### Start Ollama

```bash
ollama serve
```

### Run Both Agents

```bash
uv run a2a-demo
```

### Run Only the Echo Agent (with local math solving)

```bash
uv run a2a-demo --not-start-math
```

### Options

- `--echo-host`: Echo Agent host address (default: localhost)
- `--echo-port`: Echo Agent port number (default: 10002)
- `--math-host`: Math Agent host address (default: localhost)
- `--math-port`: Math Agent port number (default: 10003)
- `--ollama-host`: Ollama API address (default: http://localhost:11434)
- `--ollama-model`: Ollama model to use (default: llama3.2)
- `--not-start-math`: Whether not to start the Math Agent (default: false)

### Run Client

```bash
uv run google-a2a-cli --agent http://localhost:10002
```

## Testing the Demo

1. Start the agent(s) using one of the commands above
2. Send a request to the Echo Agent at http://localhost:10002/
3. For math questions like "What is 25 \* 13?", the Echo Agent will:
   - First try to delegate to the Math Agent
   - If Math Agent is unavailable, solve the problem locally
4. For non-math questions, the Echo Agent will handle them directly

## Benefits of Agent-to-Agent Communication

- **Specialization**: Agents can focus on specific tasks they excel at
- **Modularity**: New agent capabilities can be added without modifying existing agents
- **Scalability**: The system can be extended with additional specialized agents
- **Efficiency**: Tasks are directed to the most capable agent for processing
- **Fault Tolerance**: The system continues functioning even if individual agents fail

## Supported Math Operations

The system supports various math operations:

- Basic arithmetic: addition, subtraction, multiplication, division, exponentiation
- Mathematical functions: sqrt, sin, cos, tan, log, exp
- Simple numeric operations when no explicit operation is detected
