# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 TahaNili Shahin

"""Helper tool for creating a Browser object with configurable default settings.

Here we can read browser-related settings from environment variables to
make configuration simple across different environments.
"""

from __future__ import annotations

import os
from typing import Any
from browser_use import Browser


def create_browser(*, headless: bool | None = None, window_size: dict | None = None) -> Browser:
    """Returns a Browser instance with logical settings.

    Parameters:
    - headless: If None, value is read from BROWSER_HEADLESS environment variable
    - window_size: Dictionary {'width': ..., 'height': ...}
    """
    if headless is None:
        # Default value is read from environment variable ("1" or "true" means headless)
        env_val = os.getenv("BROWSER_HEADLESS", "1").lower()
        headless = env_val not in ("0", "false", "no")

    if window_size is None:
        window_size = {"width": 1280, "height": 720}

    # Return browser instance with specified settings
    return Browser(
        headless=headless,
        keep_alive=True,
        window_size=window_size,
    )