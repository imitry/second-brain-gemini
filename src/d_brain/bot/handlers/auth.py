"""Auth logic for Gemini CLI."""

import asyncio
import logging
import re
from typing import Dict

from aiogram import Router, flags
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from d_brain.bot.states import GeminiLoginState

logger = logging.getLogger(__name__)

router = Router(name="auth")

# Store subprocess per user
user_processes: Dict[int, asyncio.subprocess.Process] = {}


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences and other terminal control characters."""
    # Matches standard ANSI escape sequences
    ansi_escape = re.compile(
        r'''
        \x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])
        ''',
        re.VERBOSE
    )
    clean = ansi_escape.sub('', text)
    # Also strip raw control characters often left over (like BEL, backspace, etc), but keep newlines
    clean = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1a\x1c-\x1f]', '', clean)
    return clean

@router.message(Command("auth"))
async def cmd_auth(message: Message, state: FSMContext) -> None:
    """Handle /auth command to login with Gemini CLI."""
    user_id = message.from_user.id
    
    if user_id in user_processes:
        process = user_processes[user_id]
        if process.returncode is None:
            await message.answer("⚠️ An authorization process is already running. Please provide the code or wait for it to timeout.")
            await state.set_state(GeminiLoginState.waiting_for_code)
            return

    await message.answer("🔄 Starting Gemini login process...")
    
    try:
        # Start gemini login as a subprocess
        process = await asyncio.create_subprocess_exec(
            "gemini", "login",
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        user_processes[user_id] = process
        
        # Read stdout asynchronously so we don't block the bot
        async def read_stdout():
            output_buffer = ""
            try:
                while True:
                    # Read chunk to avoid character decode errors on boundaries
                    chunk = await process.stdout.read(1024)
                    if not chunk:
                        break
                    
                    output_buffer += chunk.decode('utf-8', errors='replace')
                    clean_buffer = strip_ansi(output_buffer)
                        
                    # Periodically check for the prompt
                    if "Enter the authorization code:" in clean_buffer or "accounts.google.com" in output_buffer:
                        # Extract the URL robustly, ignoring ANSI fragments
                        url_match = re.search(r'(https://accounts\.google\.com/[^\s\x1b\x00]+)', output_buffer)
                        if url_match:
                            url = url_match.group(1)
                            await message.answer(
                                f"🌐 <b>Gemini CLI Authorization</b>\n\n"
                                f"Please visit the following URL to authorize the bot:\n\n"
                                f"{url}\n\n"
                                f"После успешной авторизации скопируйте полученный код и отправьте его сюда."
                            )
                            await state.set_state(GeminiLoginState.waiting_for_code)
                            return
                        elif "Enter the authorization code:" in clean_buffer:
                            # Fallback if URL not found
                            await message.answer(
                                f"🌐 <b>Gemini CLI Auth</b>\n\n"
                                f"{clean_buffer}\n"
                                f"Please paste the code here:"
                            )
                            await state.set_state(GeminiLoginState.waiting_for_code)
                            return
                            
            except Exception as e:
                logger.error("Error reading stdout from gemini login: %s", e)
                await message.answer("❌ Error during authorization process.")
                
        # Start the background reader task
        asyncio.create_task(read_stdout())
        
    except Exception as e:
        logger.exception("Failed to start gemini login process")
        await message.answer(f"❌ Failed to start Gemini CLI: {e}")


@router.message(GeminiLoginState.waiting_for_code)
async def process_auth_code(message: Message, state: FSMContext) -> None:
    """Handle the authorization code input."""
    user_id = message.from_user.id
    code = message.text.strip()
    
    process = user_processes.get(user_id)
    
    if not process or process.returncode is not None:
        await message.answer("⚠️ The authorization process has expired or is no longer running. Please run /auth again.")
        await state.clear()
        if user_id in user_processes:
            del user_processes[user_id]
        return
        
    await message.answer("⏳ Submitting code to Gemini CLI...")
    
    try:
        if process.stdin:
            process.stdin.write(f"{code}\n".encode('utf-8'))
            await process.stdin.drain()
        
        # Wait for the process to finish
        try:
            await asyncio.wait_for(process.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            process.kill()
            await message.answer("❌ Authorization process timed out while verifying the code.")
            await state.clear()
            del user_processes[user_id]
            return
        
        if process.returncode == 0:
            await message.answer("✅ <b>Gemini CLI authorization was successful!</b>\n\nYou can now use commands like /process and /do.")
        else:
            await message.answer(f"❌ Authorization failed with return code {process.returncode}.")
            
    except Exception as e:
        logger.exception("Error passing code to gemini CLI")
        await message.answer(f"❌ Error verifying code: {e}")
        
    finally:
        await state.clear()
        if user_id in user_processes:
            del user_processes[user_id]
