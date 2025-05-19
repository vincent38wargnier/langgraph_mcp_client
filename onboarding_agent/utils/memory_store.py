from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, List

from app.crud.memory import (
    get_or_create_memory,
    update_memory,
    get_memory_value,
    delete_memory_value,
    clear_memory
)
from app.models.memory import Memory
from app.utils.magic_print import magic_print
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self, memory, user_id: str, agent_id: str, agent_config: Optional[Dict[str, Any]] = None):
        self.memory = memory
        self.user_id = user_id
        self.agent_id = agent_id
        self.agent_config = agent_config or {}

    @classmethod
    async def create(cls, user_id: str, agent_id: str, agent_config: Optional[Dict[str, Any]] = None):
        """Create a new MemoryStore instance."""
        memory = await get_or_create_memory(user_id, agent_id)
        return cls(memory, user_id, agent_id, agent_config)

    def _parse_expiry(self, expiry: str) -> Optional[str]:
        """Parse expiry strings like 'HOURS:2', 'DAYS:1', 'EVENT:complete_project'."""
        now = datetime.now()
        
        if expiry.startswith("HOURS:"):
            hours = int(expiry.split(":")[1])
            return (now + timedelta(hours=hours)).isoformat()
        elif expiry.startswith("MINUTES:"):
            minutes = int(expiry.split(":")[1])
            return (now + timedelta(minutes=minutes)).isoformat()
        elif expiry == "TODAY-END":
            return now.replace(hour=23, minute=59, second=59).isoformat()
        elif expiry.startswith("DAYS:"):
            days = int(expiry.split(":")[1])
            return (now + timedelta(days=days)).isoformat()
        elif expiry.startswith("WEEKS:"):
            weeks = int(expiry.split(":")[1])
            return (now + timedelta(weeks=weeks)).isoformat()
        elif expiry.startswith("EVENT:"):
            return expiry
        return expiry if expiry else None

    async def remember(self, path: str, value: Any, expiry: Optional[str] = None) -> Dict[str, Any]:
        """Store a value in memory with optional expiry, adding to existing entries in the same section."""
        try:
            # Ensure the memory is initialized.
            if not self.memory:
                magic_print("Initializing memory store", "blue")
                await self.initialize()
                magic_print("Memory store initialized", "blue")

            # Create a new entry with metadata.
            expiry_time = self._parse_expiry(expiry) if expiry else None
            new_entry = {
                "value": value,
                "expiry": expiry_time,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat()
            }
            magic_print(f"Creating new memory entry at '{path}'", "green")

            # Retrieve the current value at the given path.
            current_entry = await get_memory_value(self.memory, path)
            
            # If there's an existing entry, append the new entry to it.
            if current_entry:
                # If the current entry is not a list, convert it.
                if not isinstance(current_entry, list):
                    magic_print("Converting existing entry to list format", "yellow")
                    current_entry = [current_entry]
                current_entry.append(new_entry)
                updated_value = current_entry
            else:
                # No existing entry; use the new entry directly.
                updated_value = new_entry

            # Update the memory.
            magic_print(f"Updating memory at '{path}'", "cyan")
            self.memory = await update_memory(self.memory, path, updated_value)
            magic_print("Memory updated successfully", "cyan")
            return {"success": True, "message": f"Remembered at {path}"}
        except Exception as e:
            magic_print(f"Error in memory store: {str(e)}", "red")
            return {"success": False, "message": str(e)}

    async def recall(self, path: str) -> Any:
        """Retrieve a value from memory."""
        try:
            if not self.memory:
                await self.initialize()

            value = await get_memory_value(self.memory, path)
            if isinstance(value, dict) and "value" in value:
                value["last_accessed"] = datetime.now().isoformat()
                self.memory = await update_memory(self.memory, path, value)
                magic_print(f"Retrieved value from '{path}'", "yellow")
                return value["value"]
            magic_print(f"Retrieved value from '{path}'", "yellow")
            return value
        except Exception as e:
            magic_print(f"Error recalling value: {str(e)}", "red")
            return None

    async def forget(self, path: str) -> Dict[str, Any]:
        """Remove a value from memory."""
        try:
            if not self.memory:
                await self.initialize()

            magic_print(f"Removing value at '{path}'", "magenta")
            self.memory = await delete_memory_value(self.memory, path)
            return {"success": True, "message": f"Forgot {path}"}
        except Exception as e:
            magic_print(f"Error forgetting value: {str(e)}", "red")
            return {"success": False, "message": str(e)}

    async def clear(self) -> Dict[str, Any]:
        """Clear all memory data."""
        try:
            if not self.memory:
                await self.initialize()

            magic_print("Clearing all memory data", "magenta")
            self.memory = await clear_memory(self.memory)
            return {"success": True, "message": "Memory cleared"}
        except Exception as e:
            magic_print(f"Error clearing memory: {str(e)}", "red")
            return {"success": False, "message": str(e)}

    async def export_markdown(self) -> str:
        """Return memory content as a nicely formatted markdown text, showing only non-empty fields."""
        if not self.memory:
            await self.initialize()

        # Extract the memory content
        memory_data = self.memory.data if hasattr(self.memory, "data") else self.memory

        def format_section(data, section_name, emoji):
            """Format a section of memory with consistent styling."""
            if not data or data in (None, {}, [], "", "None"):
                return None

            lines = []
            lines.append(f"{emoji} {section_name}")

            def format_value(value, indent=1):
                """Format a value with proper indentation and bullet points."""
                if value in (None, {}, [], "", "None"):
                    return None
                
                indent_str = "  " * indent
                
                if isinstance(value, dict):
                    # Handle leaf nodes with metadata
                    if "value" in value and all(k in value for k in ["value", "expiry", "created_at", "last_accessed"]):
                        if value["value"] in (None, "", "None", {}, []):
                            return None
                        return f"{indent_str}• {value['value']}"
                    
                    # Handle regular dictionary
                    sub_lines = []
                    for key, val in value.items():
                        # Convert key from snake_case to Title Case
                        display_key = key.replace('_', ' ').title()
                        formatted_val = format_value(val, indent + 1)
                        
                        if formatted_val is not None:
                            if isinstance(val, (dict, list)) and val:
                                sub_lines.append(f"{indent_str}• {display_key}:")
                                sub_lines.append(formatted_val)
                            else:
                                sub_lines.append(f"{indent_str}• {display_key}: {val}")
                    
                    return "\n".join(sub_lines) if sub_lines else None
                
                elif isinstance(value, list):
                    if not value:
                        return None
                    sub_lines = []
                    for item in value:
                        formatted_item = format_value(item, indent)
                        if formatted_item:
                            sub_lines.append(formatted_item)
                    return "\n".join(sub_lines) if sub_lines else None
                
                else:
                    return f"{indent_str}• {value}"

            # Format the section content
            formatted_content = format_value(data)
            if formatted_content:
                lines.append(formatted_content)
                return "\n".join(lines)
            return None

        # Format each section
        sections = []
        
        # Memory section
        if memory_section := format_section(memory_data.get("memory"), "MEMORY", "🧠"):
            sections.append(memory_section)
        
        # User preferences section
        if prefs_section := format_section(memory_data.get("user_preferences"), "USER PREFERENCES", "👤"):
            sections.append(prefs_section)
        
        # Progress section
        if progress_section := format_section(memory_data.get("progress"), "PROGRESS", "📈"):
            sections.append(progress_section)
        
        # Metadata section (only show if it has meaningful content)
        metadata = memory_data.get("metadata", {})
        if any(v not in (None, "", [], {}, "None") for v in metadata.values()):
            if metadata_section := format_section(metadata, "METADATA", "📊"):
                sections.append(metadata_section)

        # Join all sections with double newlines
        response = "\n\n".join(sections) if sections else "No memory data available"
        magic_print(f"Memory content formatted: \n{response}", "blue")
        return response


