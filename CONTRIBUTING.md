# Project Contribution Guidelines

⚠️ Important Notice Regarding License and Contribution

This project is published exclusively with all rights reserved to its owner (All Rights Reserved). Before submitting any changes or Pull Requests, please coordinate with the owner through an issue or email and obtain written permission for contribution or publication. Contact information can be found in the `LICENSE` file.

Thank you for your interest in contributing to the Sofware-AI project! This guide will help you properly follow the contribution process.

## Pull Request Process

1. First, fork the repository.
2. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```
3. Make and commit your changes.
4. Run tests to ensure everything works correctly.
5. Push the branch to your fork.
6. Submit a Pull Request to the `main` branch of the main repository.

## Coding Style

- Follow PEP 8.
- Write docstrings for all functions and classes (English).
- Use Type hints.
- Write explanatory comments in English.
- Maximum line length: 100 characters.

Example:
```python
def process_task(task: str, mode: str = "browser") -> Optional[str]:
    """Process a task and return the result.

    Args:
        task: The task text to process
        mode: Execution mode ('browser' or 'code')

    Returns:
        Processing result or None if error occurs
    """
    ...
```

## Commit Guidelines

- Write concise and meaningful commit messages
- Use imperative verbs
- Suggested structure:
  ```
  type: brief description (max 50 characters)

  More detailed explanation if needed (max 72 characters per line)
  ```
- Common types:
  - `feat`: new feature
  - `fix`: bug fix
  - `docs`: documentation changes
  - `style`: code appearance changes (like indentation)
  - `refactor`: code rewriting without behavior changes
  - `test`: adding/editing tests
  - `chore`: miscellaneous updates

Example:
```
feat: add support for chatgpt-4 model

- Add ChatGPT4Agent class
- Update AIBrain to support new model
- Add related tests
```

## Important Notes

- Before starting work, ensure there's a related issue.
- Propose large changes in an issue first.
- Include only one main change per PR.
- Keep PRs small (preferably under 500 lines).
- Before PR ensure:
  - All tests pass
  - Changes are documented
  - Code follows style guide

## Bug Reports

To report a bug:
1. Write a clear title
2. Describe exact steps to reproduce the issue
3. Explain expected behavior and current behavior
4. Include environment information (OS, Python version, etc.)

## Questions

If you have questions:
- First read the documentation
- Search through issues
- If you can't find the answer, open a new issue with the `question` label

Thank you for your contribution! 🙏