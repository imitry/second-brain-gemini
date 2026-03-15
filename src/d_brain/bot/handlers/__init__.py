"""Bot message handlers."""

from d_brain.bot.handlers import (
    buttons,
    commands,
    do,
    forward,
    photo,
    process,
    text,
    voice,
    weekly,
)

# Note: auth handler is excluded because GeminiLoginState
# was removed from states.py on the coolify branch.

__all__ = [
    "buttons",
    "commands",
    "do",
    "forward",
    "photo",
    "process",
    "text",
    "voice",
    "weekly",
]
