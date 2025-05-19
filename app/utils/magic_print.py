"""
Simple utility for colored terminal output.
"""

def magic_print(message, color=None):
    """
    Print colored messages to the terminal.
    
    Args:
        message: The message to print
        color: Color to use (red, green, blue, yellow, cyan, magenta)
    """
    # ANSI color codes
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'reset': '\033[0m'
    }
    
    # Print with color if specified, otherwise normal print
    if color and color in colors:
        print(f"{colors[color]}{message}{colors['reset']}")
    else:
        print(message) 