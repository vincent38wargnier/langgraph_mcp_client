"""
MongoDB models and connection management.
"""
from mongoengine import connect, disconnect
from app.settings.config import settings
from app.models.conversation import Conversation
from app.utils.magic_print import magic_print

def connect_to_mongo():
    # Print connection details
    magic_print("\n🔌 MongoDB Connection Setup:", "blue")
    magic_print(f"URI: {settings.MONGODB_URI[:20]}...{settings.MONGODB_URI[-20:]}", "cyan")
    magic_print("\n⚙️ Connection Settings:", "blue")
    magic_print("- Server Selection Timeout: 10s", "yellow")
    magic_print("- Connect Timeout: 10s", "yellow")
    magic_print("- Socket Timeout: 10s", "yellow")
    magic_print("- Max Pool Size: 50", "yellow")
    magic_print("- Min Pool Size: 10", "yellow")
    magic_print("- Max Idle Time: 50s", "yellow")
    magic_print("- Wait Queue Timeout: 5s", "yellow")
    magic_print("- Retry Writes: Enabled", "yellow")
    magic_print("- Retry Reads: Enabled", "yellow")
    
    connect(
        host=settings.MONGODB_URI,
        serverSelectionTimeoutMS=10000,  # 10 seconds timeout
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        retryWrites=True,
        retryReads=True,
        maxPoolSize=50,
        minPoolSize=10,
        maxIdleTimeMS=50000,
        waitQueueTimeoutMS=5000
    )
    magic_print("\n✅ Successfully connected to MongoDB!", "green")

def close_mongo_connection():
    disconnect()
    magic_print("🔌 Disconnected from MongoDB", "yellow")

# Expose models for use in other modules
__all__ = ['Conversation', 'connect_to_mongo', 'close_mongo_connection'] 