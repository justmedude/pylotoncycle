# Style Guide

This project follows a set of coding standards to ensure that the codebase is clean, maintainable, and human-readable.

## 1. Formatting
- We use **[Black](https://github.com/psf/black)** for code formatting.
- Line length is set to **78** characters (as configured in `pyproject.toml`).

## 2. Linting
- We use **[flake8](https://flake8.pycqa.org/en/latest/)** for linting.
- Contributions should pass a standard `flake8` run.

## 3. Type Hints
- All new code should include **PEP 484 type hints**.
- Existing code is being progressively updated to include type hints for better clarity and IDE support.

## 4. Docstrings
- We follow the **Google Style Python Docstrings**.
- Every class and public method/function should have a docstring.
- Example:
  ```python
  def fetch_data(user_id: str, limit: int = 10) -> list[dict]:
      """Fetches workout data for a specific user.

      Args:
          user_id: The unique identifier for the user.
          limit: The maximum number of records to return.

      Returns:
          A list of dictionaries containing workout information.
      """
  ```

## 5. String Formatting
- Use **f-strings** (literal string interpolation) for all string formatting where possible.
- Avoid `%` formatting and `.format()` unless there is a specific technical reason to use them.

## 6. Language Compatibility
- Bias towards **Python 3.7+** compatibility.
