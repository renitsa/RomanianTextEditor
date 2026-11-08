"""
Application-level exceptions.
"""


class UserCancelled(Exception):
    """Raised when the user chooses to exit (or presses Ctrl+C) during an interactive prompt.

    The application handles it once at the top level, so prompts do not need to
    terminate the process themselves.
    """
