# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 TahaNili Shahin

"""Simple layer for selecting LLM models.

Here we use lazy-loading so that heavy modules are only loaded when needed.
Configuration through environment variables is also supported.
"""

from __future__ import annotations

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AIBrain:
    """Class for managing and selecting appropriate model based on purpose.

    Operation: Models are created on demand to keep program startup lightweight.
    """

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}

    def _load_model(self, name: str) -> Any:
        """Load model by logical name. This function encapsulates heavy imports."""
        try:
            if name == "reasoning":
                from browser_use.llm.google.chat import ChatGoogle

                model = ChatGoogle(model=os.getenv("GOOGLE_REASONING_MODEL", "gemini-2.5-flash"),
                                   temperature=float(os.getenv("MODEL_TEMPERATURE", "0.5")))
            elif name == "browser_use":
                from browser_use.llm.browser_use.chat import ChatBrowserUse

                model = ChatBrowserUse()
            elif name == "fast":
                from browser_use.llm.groq.chat import ChatGroq

                model = ChatGroq(model=os.getenv("GROQ_MODEL", "groq-1"),
                                  temperature=float(os.getenv("MODEL_TEMPERATURE", "0.7")))
            else:
                from browser_use.llm.openai.chat import ChatOpenAI

                model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
                                    temperature=float(os.getenv("MODEL_TEMPERATURE", "0")))
            logger.info("Loaded model: %s", name)
            return model
        except Exception as exc:
            logger.exception("Failed to load model %s: %s", name, exc)
            raise

    def get_model(self, purpose: str) -> Any:
        """Select model based on purpose.

        Possible values for purpose: 'analyze', 'browse', 'realtime', or default.
        """
        key = {
            "analyze": "reasoning",
            "browse": "browser_use",
            "realtime": "fast",
        }.get(purpose, "normal")

        if key not in self._models:
            self._models[key] = self._load_model(key)

        return self._models[key]