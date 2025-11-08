#!/usr/bin/env python3
# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""
The main entry point of the AI ​​software system.
This module provides a command line interface (CLI) for the main system capabilities.
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
from dotenv import load_dotenv

colorama_init(autoreset=True) # Enable ANSI management on Windows
with open('banner.txt', 'r', encoding='utf-8') as file:
    banner = file.read()

# Configure logging system
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
    """Initialize environment variables and create required folders."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Ensure that the required folders exist
    for dir_path in ["data/logs", "data/logs/cache"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def parse_arguments() -> argparse.Namespace:
    """Parsing command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Artificial Intelligence Software System - Intelligent Task Processing",
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
        help="Number of concurrent tasks that can be run (default: 3)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logs"
    )

    return parser.parse_args()

def print_banner(text=banner, color=Fore.WHITE) -> None:
    """Printing a welcome banner in the CLI."""
    term_width = shutil.get_terminal_size((80, 20)).columns
    
    try:
        # If the text is already ASCII art, we display it directly
        lines = str(text).splitlines()
        for line in lines:
            # Calculate the distance required to center the text
            padding = (term_width - len(line)) // 2
            if padding > 0:
                print(color + " " * padding + line + Style.RESET_ALL)
            else:
                print(color + line + Style.RESET_ALL)
    except Exception as e:
        logger.error(f"Error displaying banner: {str(e)}")
        print(color + str(text) + Style.RESET_ALL)

async def process_user_input(task_engine: TaskEngine, memory: MemoryManager, mode: str) -> None:
    """Processing user input in an interactive loop."""
    print_banner(banner, color=Fore.WHITE)
    print("\n Welcome to the Software-AI System!")
    print("Please enter your tasks (one task per line). Use Ctrl+C to exit.\n")

    try:
        # Outer loop: allows multiple rounds of adding + executing tasks
        while True:
            # Inner loop: receives one or more tasks from the user
            while True:
                try:
                    user_input = input("New Task > ").strip()

                    if not user_input:
                        continue

                    # Save the task in short-term memory
                    memory.remember_short(
                        content=user_input,
                        ttl=3600,  # 1 hour TTL
                        metadata={"type": "user_task", "mode": mode}
                    )

                    # Add task to processing engine
                    task_engine.add_task(user_input, mode=mode)
                    print(f"Task added: {user_input}")

                    # Ask to add more tasks or start execution
                    choice = input("\n What other tasks are you doing? (y/N) ").strip().lower()
                    if choice == 'y':
                        # keep collecting
                        continue
                    else:
                        break

                except EOFError:
                    break

            # If no tasks have been added in this round, ask whether to continue or exit
            if not task_engine.queue:
                cont = input("\n No tasks have been added. Do you want to continue? (Y/N) ").strip().lower()
                if cont == 'n':
                    break
                else:
                    # Return to task collection
                    continue

            # Execute all collected tasks
            print("\n Executing tasks...")

            # Snapshots tasks before execution, as run_all does not clear the queue
            tasks_list = list(task_engine.queue)
            results = await task_engine.run_all()

            # Save results in long-term memory
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
                    print(f"\nThe task failed or had no results.\n")

            # Clear the engine's queue to start fresh for the next round
            task_engine.queue.clear()

            # Ask if the user wants to add or run more tasks
            cont = input("\n Do you want to add or perform more tasks? (Y/N)").strip().lower()
            if cont == 'n':
                break
            # Otherwise, continue the outer loop to collect more tasks
            continue

    except KeyboardInterrupt:
        print("\nShutting down the software...")
    finally:
        memory.shutdown()

async def main() -> None:
    """The main entry point of the application."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Setting up the environment
        setup_environment()
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            
        # Launching the main components
        task_engine = TaskEngine(concurrency=args.concurrency)
        memory = MemoryManager()
        
        # Process user input and execute tasks
        await process_user_input(task_engine, memory, args.mode)
        
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())