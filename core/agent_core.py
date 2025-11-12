# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""Factory for creating Agent or CodeAgent with more secure settings.

Key changes:
- Model loading through AIBrain
- Removal of hardcoded sensitive values; session key is read from environment variable
- File paths are placed in a configurable and secure manner
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from browser_use import Agent, CodeAgent
from .ai_brain import AIBrain
from .browser_core import create_browser


def create_agent(task: str, mode: str = "browser") -> Agent | CodeAgent:
    """Creates an Agent or CodeAgent based on mode.

    Parameters:
    - task: Task text for the agent
    - mode: 'browser' or 'code'
    """

    ai_brain = AIBrain()
    # Determine model based on agent type
    llm = ai_brain.get_model("browse" if mode == "browser" else "analyze")

    browser = create_browser() if mode == "browser" else None

    agent_class = CodeAgent if mode == "code" else Agent

    # Read session key from environment variable; if not set, use None
    session_key = os.getenv("SESSION_KEY")

    # Allowed paths for agent (if needed, you can read settings from file or env)
    available_paths = [str(Path("./data").resolve())]

    if not callable(agent_class):
        module = agent_class
        cls = None
        # Give priority to well-known names
        for name in ("CodeAgent", "Agent"):
            cls = getattr(module, name, None)
            if cls and callable(cls):
                agent_class = cls
                break
        # If not found yet, take the first type defined in the module
        if not callable(agent_class):
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type):
                    agent_class = obj
                    break
        if not callable(agent_class):
            raise TypeError(f"agent_class ({module!r}) is not callable and no suitable class was found in the module")

    agent = agent_class(
        task=task,
        llm=llm,
        browser=browser,
        max_steps=20,
        use_vision=False,
        flash_mode=(mode == "fast"),
        sensitive_data={"session_key": session_key} if session_key else None,
        available_file_paths=available_paths,
    )

    return agent