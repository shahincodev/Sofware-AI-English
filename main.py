#!/usr/bin/env python3
# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 TahaNili (Shahin)

"""
Main entry point for the Sofware-AI system.
This module provides a command-line interface (CLI) to interact with the core capabilities.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional
from pyfiglet import Figlet
from colorama import init as colorama_init, Fore, Style


from core.agent_core import create_agent
from core.memory_system import MemoryManager
from core.task_engine import TaskEngine
from core.voice_io import VoiceManager
from dotenv import load_dotenv

colorama_init(autoreset=True) # enable ANSI handling on Windows
with open('banner.txt', 'r', encoding='utf-8') as file:
    banner = file.read()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path("data/logs/app.log"))
    ]
)
logger = logging.getLogger(__name__)

def setup_environment() -> None:
    """Initialize environment variables and create required directories."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Ensure required directories exist
    for dir_path in ["data/logs", "data/logs/cache"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Sofware-AI — intelligent task processing system",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--mode",
        choices=["browser", "code"],
        default="browser",
        help="Operation mode: 'browser' for web interaction, 'code' for code analysis"
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Number of concurrent tasks to run (default: 3)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
    "--input-mode",
    choices=["text", "voice"],
    default="text",
    help="Select input type: 'text' for keyboard, 'voice' for microphone"
    )

    return parser.parse_args()

def print_banner(text=banner, color=Fore.CYAN) -> None:
    """Print welcome banner in the CLI."""
    term_width = shutil.get_terminal_size((80, 20)).columns
    
    try:
        # If the input text is already ASCII art, print it directly
        lines = str(text).splitlines()
        for line in lines:
            # compute padding needed to center the text
            padding = (term_width - len(line)) // 2
            if padding > 0:
                print(color + " " * padding + line + Style.RESET_ALL)
            else:
                print(color + line + Style.RESET_ALL)
    except Exception as e:
        logger.error(f"Error displaying banner: {str(e)}")
        print(color + str(text) + Style.RESET_ALL)

async def process_user_input(task_engine: TaskEngine, memory: MemoryManager, mode: str, input_mode: str, voice: VoiceManager) -> None:
    """Process user input in an interactive loop."""

    print_banner(banner, color=Fore.CYAN)
    # voice greeting if voice input selected
    if input_mode == "voice":
        voice.speak("Hello! Welcome to the AI system.", block=True)
    print("\nWelcome to Sofware-AI — Intelligent Task Processor!\n")
    print("Enter your tasks (one task per line). Use Ctrl+C to exit.\n")

    try:
        # outer loop: allows multiple rounds of adding + executing tasks
        while True:
            # inner loop: collect one or more tasks from the user
            while True:
                try:

                    if input_mode == "voice":
                        user_input = voice.listen(timeout=7)
                        if not user_input:
                            print("No voice input detected, please try again.")
                            continue
                    else:
                        user_input = input("New task > ").strip()
                        if not user_input:
                            continue

                    # store task in short-term memory
                    memory.remember_short(
                        content=user_input,
                        ttl=3600,  # 1 hour TTL
                        metadata={"type": "user_task", "mode": mode}
                    )

                    # add task to processing engine
                    task_engine.add_task(user_input, mode=mode)
                    print(f"Task added: {user_input}")

                    # ask whether to add more tasks or start execution

                    if input_mode == "voice":
                        voice.speak("Do you have another task? Say 'yes' to add another, or stay silent to continue.")
                        choice = voice.listen(timeout=5)
                        if choice and ("yes" in choice.lower()):
                            continue
                        else:
                            break
                    else:
                        choice = input("\nAdd another task? (y/N) ").strip().lower()
                        if choice == 'y':
                            continue
                        else:
                            break

                except EOFError:
                    break

            # If no task was added in this round, ask whether to continue or exit

            if not task_engine.queue:
                if input_mode == "voice":
                    voice.speak("No tasks were added. Do you want to continue? Say 'no' to exit.")
                    cont = voice.listen(timeout=5)
                    if cont and ("no" in cont.lower()):
                        break
                    else:
                        continue
                else:
                    cont = input("\nNo tasks were added. Do you want to continue? (Y/n) ").strip().lower()
                    if cont == 'n':
                        break
                    else:
                        continue

            # Execute all collected tasks
            print("\nExecuting collected tasks...")

            # Snapshot the tasks before execution because run_all does not clear the queue
            tasks_list = list(task_engine.queue)
            results = await task_engine.run_all()

            # Store results in long-term memory
            for (task_text, task_mode), result in zip(tasks_list, results):
                if result:
                    memory.remember_long(
                        content=result,
                        metadata={
                            "type": "task_result",
                            "original_task": task_text,
                            "mode": task_mode
                        }
                    )
                    print(f"\nTask result: {result}\n")
                else:
                    print(f"\nTask failed or produced no result.\n")

            # Clear the engine queue to start the next round fresh
            task_engine.queue.clear()

            # Ask whether the user wants to add more tasks or finish

            # Ask whether the user wants to add more tasks or finish
            if input_mode == "voice":
                voice.speak("Would you like to add more tasks or continue? Say 'no' to finish.")
                cont = voice.listen(timeout=5)
                if cont and ("no" in cont.lower()):
                    break
                else:
                    continue
            else:
                cont = input("\nWould you like to add more tasks or continue? (Y/n) ").strip().lower()
                if cont == 'n':
                    break
                else:
                    continue

    except KeyboardInterrupt:
        print("\nShutting down application...")
    finally:
        memory.shutdown()
        voice.shutdown()

async def main() -> None:
    """Main program entry point."""
    try:
    # Parse command line arguments
        args = parse_arguments()

    # Setup environment
        setup_environment()

        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

    # Initialize core components
        task_engine = TaskEngine(concurrency=args.concurrency)
        memory = MemoryManager()
        voice = VoiceManager()

    # Process user input and execute tasks
        await process_user_input(task_engine, memory, args.mode, args.input_mode, voice)

    except Exception as e:
        logger.exception("Unhandled fatal error occurred")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())