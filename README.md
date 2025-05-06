# True Agent-to-Agent (A2A) Demo

This project demonstrates a true Agent-to-Agent (A2A) interaction using Google's [A2A protocol](https://github.com/google-research/google-research/tree/master/a2a). It consists of two agents that communicate with each other:

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

## Running the Demo

You can run the agents in different ways:

### Run Both Agents Together

```bash
python -m a2a_demo all
```

### Run Echo Agent Only

```bash
python -m a2a_demo echo
```

### Run Math Agent Only

```bash
python -m a2a_demo math
```

### Options

- `--host`: Host address (default: localhost)
- `--port`: Port number (default: 10002 for Echo, 10003 for Math)
- `--ollama-host`: Ollama API address (default: http://localhost:11434)
- `--ollama-model`: Ollama model to use (optional)

## Testing the Demo

1. Start both agents using the `all` command
2. Send a request to the Echo Agent at http://localhost:10002/
3. For math questions like "What is 25 \* 13?", the Echo Agent will delegate to the Math Agent
4. For non-math questions, the Echo Agent will handle them directly

## Benefits of Agent-to-Agent Communication

- **Specialization**: Agents can focus on specific tasks they excel at
- **Modularity**: New agent capabilities can be added without modifying existing agents
- **Scalability**: The system can be extended with additional specialized agents
- **Efficiency**: Tasks are directed to the most capable agent for processing
