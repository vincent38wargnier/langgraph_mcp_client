from mongoengine import Document, StringField, ListField, BooleanField, DateTimeField, DictField
from datetime import datetime
import uuid
from app.utils.magic_print import magic_print

class Conversation(Document):
    """
    MongoDB model for storing conversations.
    """
    id = StringField(primary_key=True)
    messages = ListField(DictField())  # List of message dicts with role, content, timestamp
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'conversations',
        'indexes': [
            'is_active', 
            'created_at'
        ]
    }
    
    def add_message(self, role, content, task_id=None):
        """Add a message to the conversation"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        if task_id:
            message['task_id'] = task_id
        
        self.messages.append(message)
        self.updated_at = datetime.now()
        self.save()
        return self
    
    @classmethod
    def get_or_create(cls, conversation_id=None):
        """Get an existing conversation or create a new one"""
        if conversation_id:
            try:
                # Try to find the conversation by ID
                conversation = cls.objects(id=conversation_id).first()
                if conversation:
                    magic_print(f"Found existing conversation: {conversation_id}", "green")
                    return conversation
            except Exception as e:
                magic_print(f"Error retrieving conversation: {str(e)}", "red")
        
        # Create new conversation if not found or no ID provided
        conversation_id = conversation_id or str(uuid.uuid4())
        magic_print(f"Creating new conversation: {conversation_id}", "blue")
        return cls(id=conversation_id, messages=[], is_active=True).save() 