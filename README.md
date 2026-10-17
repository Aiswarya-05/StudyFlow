# Study Planner — Python Project

## Overview
A beginner-friendly study planner built using Python. It divides the available study time equally among subjects and creates a simple time-based schedule.

## Features
- Accepts study duration and subject names.
- Allocates available minutes across subjects.
- Validates invalid or missing inputs.
- Handles multiple requests in one session.
- Runs locally without requiring an API key.

## Technologies Used
- Python
- Regular Expressions
- Functions and Loops
- Input Validation
- Unit Testing

## Example
**Input:** 2 hours to study Java, SQL, and Python.

**Output:**
- Java: 40 minutes
- SQL: 40 minutes
- Python: 40 minutes

## How to Run
1. Install Python 3.
2. Open a terminal in the project folder.
3. Run `python main.py`.

## Testing
Run the automated tests with:

`python -m unittest -v test_planner.py`

## Current Limitations
This is a rule-based planner. It does not use an LLM, external tools, or AI-based reasoning.

## Future Improvements
- Add a graphical user interface.
- Support more natural ways of entering study requests.
- Explore integration with an LLM or a local language model.
- Add more automated tests.
