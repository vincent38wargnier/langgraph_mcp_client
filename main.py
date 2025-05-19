import asyncio
import os
import sys
import traceback
from uuid import uuid4

# Add the root directory to sys.path to handle imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.onboarding_agent.graph import run_agent
from app.utils.magic_print import magic_print
from app.models import connect_to_mongo, close_mongo_connection

async def main():
    """
    Simple CLI to interact with the simplified agent using MongoDB for storage.
    """
    magic_print("=" * 50, "blue")
    magic_print("🤖 SIMPLIFIED AGENT CLI WITH MCP TOOLS", "blue")
    magic_print("=" * 50, "blue")
    
    # Connect to MongoDB
    connect_to_mongo()
    
    conversation_id = None
    
    try:
        while True:
            # Get user input
            user_message = input("\n💬 You: ")
            
            # Exit conditions
            if user_message.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                magic_print("Goodbye! 👋", "green")
                break
                
            # Process message with agent
            try:
                magic_print("⏳ Processing...", "yellow")
                result = await run_agent(
                    message=user_message,
                    conversation_id=conversation_id
                )
                
                # Store conversation ID for next turn
                conversation_id = result["conversation_id"]
                
                # Display agent response
                magic_print(f"\n🤖 Agent: {result['response']}", "green")
                
                # Optional: Display conversation ID
                magic_print(f"📝 Conversation ID: {conversation_id}", "blue")
                
            except Exception as e:
                magic_print(f"❌ Error: {str(e)}", "red")
                magic_print("Details:", "red")
                traceback.print_exc()
                magic_print("Continuing with a fresh conversation...", "yellow")
                conversation_id = None
    finally:
        # Close MongoDB connection when done
        close_mongo_connection()

if __name__ == "__main__":
    # Set up better exception handling for asyncio
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        magic_print("\nGoodbye! 👋", "green")
    except Exception as e:
        magic_print(f"❌ Fatal error: {str(e)}", "red")
        traceback.print_exc()
        sys.exit(1) 