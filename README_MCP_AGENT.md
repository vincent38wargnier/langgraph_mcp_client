# MCP Client Agent Integration

This project integrates the Model Context Protocol (MCP) with µAgents framework to create an agent that can interact with AI tools through a standard protocol.

## Setup

1. Make sure you have all dependencies installed:
   ```bash
   pip install uagents langchain-mcp-adapters python-dotenv
   ```

2. Configure your `.env` file with the MCP endpoint:
   ```
   MCP_ENDPOINT=https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550/sse
   MCP_TRANSPORT=sse
   ```

3. Set the correct LangGraph agent address in `agent_config.py`:
   ```python
   langgraph_agent_address = "agent1q0zyxrneyaury3f5c7aj67hfa5w65cykzplxkst5f5mnyf4y3em3kplxn4t"
   ```

## Running the Agent

Start the agent by running:
```bash
python agent_config.py
```

The agent will:
1. Connect to the MCP server
2. Load all available tools
3. Set up communication with the LangGraph agent
4. Process incoming tool requests

## Using the Agent

You can interact with the agent by sending messages in the following format:

### Tool Request Format
```
/tool tool_name param1=value1 param2=value2
```

Example for using the video transcript tool:
```
/tool get_video_transcript url=https://www.youtube.com/watch?v=example
```

For generic messages, the agent will use the echo tool and respond back with the same message.

## Available Tools

The agent automatically loads all tools from the MCP server. Currently, it supports:

- `get_video_transcript`: Retrieves the transcript of a video given its URL
- `echo_tool`: A simple tool that echoes back the message (available as fallback)

## Troubleshooting

If you encounter issues with the MCP connection:

1. Verify that the MCP endpoint is correct in your `.env` file
2. Check that the transport type is supported (sse, websocket, or streamable_http)
3. Ensure all dependencies are properly installed
4. Verify the LangGraph agent address is correct

## Implementation Details

The agent uses:
- µAgents framework for agent communication
- MCP client for tool integration
- Chat protocol for structured messaging
- Asynchronous execution for tool processing

## Security Considerations

- The agent uses a fixed seed for development. In production, generate a secure random seed.
- Make sure to validate all input parameters before executing tools.
- Consider adding authentication for sensitive operations. 