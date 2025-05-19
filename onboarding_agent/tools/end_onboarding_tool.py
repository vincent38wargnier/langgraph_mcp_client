from typing import Dict, Any, Annotated
from langchain_core.tools import tool
from app.utils.magic_print import magic_print
from langgraph.prebuilt import InjectedState
from app.models.conversation import Conversation
from bson.objectid import ObjectId

@tool
async def end_onboarding(
    state: Annotated[dict, InjectedState]
) -> Dict[str, Any]:
    """Marks the end of the onboarding process and activates full coaching mode.
    
    Use this tool during Step 7 (Final Onboarding Step & Starting The Coaching Journey)
    after receiving and acknowledging the user's first coaching goal/challenge.
    
    This updates the conversation state from "onboarding" to "coaching",
    which unlocks the full coaching experience with all features.
    
    Call this only once when you're ready to transition from onboarding to actually addressing 
    the user's specific goal or challenge.
    
    The tool requires no parameters and utilizes the conversation_id from state.
    
    Returns:
        Dict[str, Any]: Operation result with success status and a message.
    """
    magic_print("=" * 50, "green")
    magic_print("🎉 END ONBOARDING TOOL CALLED", "green")
    magic_print("=" * 50, "green")
    
    conversation_id = state.get("conversation_id")
    if not conversation_id:
        magic_print("❌ Conversation ID not found in state", "red")
        return {"success": False, "message": "Conversation ID not found in state"}
    
    try:
        # Find the conversation
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation:
            magic_print(f"❌ Conversation with ID {conversation_id} not found", "red")
            return {"success": False, "message": f"Conversation with ID {conversation_id} not found"}
        
        # Update the conversation state
        previous_state = conversation.conversation_state
        conversation = conversation.update_conversation_state("coaching")
        
        magic_print(f"✅ Onboarding completed! Conversation state updated from '{previous_state}' to 'coaching'", "green")
        
        # Add a system message marking the completion
        conversation.add_message(
            role="system", 
            content="Onboarding process completed. Conversation has transitioned to coaching mode."
        )
        
        # Return success response
        return {
            "success": True, 
            "message": "Onboarding completed successfully. Conversation is now in coaching mode."
        }
        
    except Exception as e:
        error_msg = f"Error in end_onboarding operation: {str(e)}"
        magic_print(f"❌ {error_msg}", "red")
        return {"success": False, "message": error_msg} 