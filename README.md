# Sofware-AI

A simple and extensible system for executing intelligent tasks using LLM models and automated browser tools.

This repository contains a Python module set that can receive tasks from users, execute them using an Agent, and store results in short-term and long-term memory.

---

## Project Introduction

Sofware-AI is an experimental and extensible project aimed at providing a simple framework for building "intelligent agents". These Agents can interact with browsers, analyze code, or perform textual/analytical tasks. Project name: "Sofware-AI".

This version focuses on three main components: model selection (LLM), task execution engine (Task Engine), and memory system (Memory System).

---

## Quickstart

```bash
# Clone the repository
git clone https://github.com/tahanilishahin/Sofware-AI-Persian.git
cd Sofware-AI-Persian

# Create virtual environment
python -m venv .venv

# Activate virtual environment (in PowerShell)
.\.venv\Scripts\Activate.ps1
# or in Bash/WSL
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit .env file
cp .env.example .env
# Now open the .env file and enter the API keys

# Run the program
python main.py
```

Or use the prepared scripts:
```bash
# On Windows:
.\run.bat

# On Linux/macOS/WSL:
chmod +x run.sh  # only first time
./run.sh
```

## General Operation (Summary)

1. You run the program (CLI).
2. Enter tasks linearly (one task per line).
3. The program queues tasks and uses appropriate Agent based on mode (`--mode`).
4. Execution results are stored in short-term memory and transferred to long-term memory if needed.

This simple design allows you to use Agents as modules and reconfigure or extend behaviors.

---

## Project Features

- Interactive task input from users (CLI).
- Concurrent execution of multiple tasks with configurable concurrency limit (`--concurrency`).
- Automatic selection of LLM models based on purpose (`AIBrain`).
- Support for different execution modes: `browser` (web interaction) and `code` (code analysis).
- Short-term memory system with TTL and long-term memory with SQLite.
- Storage of execution results in long-term memory for later retrieval.
- Welcome banner in CLI (with ASCII art) for user-friendly appearance.
- Ready-made scripts: `run.bat` for Windows and `run.sh` for Unix/WSL that create virtual environment, install dependencies, and run the program.
- Environment variables sample file: `.env.example` for guidance in placing API keys.

---

## Complete Setup and Usage (Step by Step)

Prerequisites:
- Python 3.11 or newer
- Internet connection for installing dependencies and accessing APIs

Note: Commands below are provided for both PowerShell/Windows and Unix (Linux, macOS, WSL).

1) Copy or Clone the Repository

```powershell
# PowerShell
git clone <url-of-repo> Sofware-AI
cd Sofware-AI
```

2) Using Ready-Made Scripts (Easiest Method)

- Windows (CMD): Double click or run in CMD

```
run.bat
# or with arguments
run.bat --mode code --concurrency 5
```

- Unix / macOS / WSL:

```bash
chmod +x run.sh  # only once
./run.sh
# or with arguments
./run.sh --mode code --concurrency 5
```

The scripts do the following:
- Create or use a local venv (`.venv`)
- Install dependencies from `requirements.txt` (if exists)
- If `.env` file doesn't exist, copy from `.env.example` for you to fill
- Run `main.py` with passed arguments

3) Manual Installation and Execution (Optional)

If you prefer to do everything manually:

PowerShell (Windows):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or .\.venv\Scripts\activate.bat in CMD
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env  # then edit .env with real values
python main.py
```

Bash (Linux/macOS/WSL):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env  # then edit .env with real values
python main.py
```

4) How to Use the CLI

- Running `python main.py` or executing the above scripts enters interactive mode.
- Available command line arguments:
  - `--mode`: Execution mode, possible value `browser` or `code` (default `browser`).
  - `--concurrency`: Number of concurrent tasks (e.g., `--concurrency 3`).
  - `--debug`: Enable debug logs for troubleshooting.

Example:

```
python main.py --mode code --concurrency 5
```

5) Filling the `.env` File

- The `.env.example` file provides a template of variables. Make sure to copy this file to `.env` and enter the actual API key values.
- Make sure not to commit the `.env` file to the repository. (.gitignore ignores this file.)

Important: Keep API keys confidential. Use secret variables for CI.

---

## Tips and Troubleshooting

- If ANSI colors aren't displaying correctly on Windows, use PowerShell or terminals like Windows Terminal. The program uses `colorama` for support.
- If you receive errors during package installation, check Python version and ensure `pip` is up to date.
- API connection errors are usually due to incorrect keys or network limitations; verify the values of `OPENAI_API_KEY`, `GROQ_API_KEY`, `BROWSER_USE_API_KEY`, `GOOGLE_API_KEY`.

---

## Further Development

This project is designed to keep internal components like `AIBrain`, `TaskEngine`, `MemoryManager` separate. You can:
- Add new models to `AIBrain`.
- Change short-term → long-term memory transfer policies.
- Write new Agents or customize existing ones.

If you need help, I can assist you in implementing a feature or testing.

---

## Contributing

If you want to contribute to the project, please read our brief guide in `CONTRIBUTING.md`. The file explains how to open an issue, how to create a new branch, what commit and coding style to follow, and what standards exist for submitting Pull Requests.

---

## License

This project is published exclusively and all rights are reserved to the project owner.

Copyright Information and Contact:

- Copyright Owner: TahaNili (Shahin)
- Year: 2025
- Contact:
  - GitHub: https://github.com/tahanilishahin
  - Email: tahanilishahin@gmail.com

Without explicit written permission from the owner, none of the following is allowed:
- Copying, distributing, publishing, or displaying the program
- Modifying, creating derivative works, or selling the program

To obtain permission for use or receive a commercial license, please contact the owner via email or GitHub page above.

Technical Note: The complete proprietary license text is available in the `LICENSE` file; this file has an SPDX identifier of `NOASSERTION` indicating that no specific public license is applied.

Notice: Due to the proprietary nature of the project, any contributions or code submissions must be coordinated with and approved by the owner. Please coordinate with the owner through issues or email before opening a Pull Request.

--- 