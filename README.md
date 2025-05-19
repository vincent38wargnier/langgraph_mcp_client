# MCP Onboarding Agent with uAgents

This project integrates the MCP onboarding agent with the uAgents framework, allowing it to be deployed as a decentralized agent that can communicate with other agents.

## Features

- Powerful LangGraph-based agent with tool-calling capabilities
- Access to MCP tools for enhanced functionality
- Persistence via MongoDB for conversation history
- Decentralized agent architecture with uAgents

## Prerequisites

- Python 3.9+
- MongoDB instance
- OpenAI API key
- Agentverse API key

## Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_key
   AGENTVERSE_API_KEY=your_agentverse_key
   MONGODB_URI=your_mongodb_uri
   ```

## Deployment

### 1. Start the Onboarding Agent

Run the agent:
```bash
python agent.py
```

This will start the agent and register it with the Agentverse. The output will include the agent's address, which looks like:
```
✅ Registered onboarding agent: {'agent_address': 'agent1q...', 'port': 8080}
```

### 2. Set the Agent Address 

Copy the agent's address from the output and add it to your `.env` file:
```
AGENT_ADDRESS=agent1q...
```

### 3. Run the Client Agent

In a separate terminal, run the client agent:
```bash
python agent_client.py
```

This client agent will automatically send a message to the onboarding agent and display the response.

## Using the Agent

The onboarding agent can respond to user queries and utilize various MCP tools. The client agent provides a simple example of how to interact with it.

To send custom messages to the agent, you can modify the `agent_client.py` file or build your own client using the uAgents framework.

## Troubleshooting

- If you encounter MongoDB connection issues, verify your connection string in the `.env` file
- For agent communication problems, ensure that both agents are running and the correct agent address is used
- Check that your API keys are valid and properly set in the `.env` file

## Architecture

The system consists of:

1. **agent.py** - The main agent that wraps the LangGraph-based onboarding agent with uAgents
2. **agent_client.py** - A client agent that communicates with the main agent using the chat protocol
3. **MongoDB** - Stores conversation history for persistence
4. **MCP Tools** - External tools that the agent can access for additional capabilities

## MCP Integration

The agent can use tools from MCP servers through:

1. **Local Tools**: Using stdio transport with local Python scripts
2. **Remote Tools**: Using SSE transport with remote MCP servers

## Troubleshooting

If you encounter issues:

1. Make sure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify MCP endpoint configuration:
   ```bash
   python fix_mcp_endpoint.py
   ```# langgraph_mcp_client
