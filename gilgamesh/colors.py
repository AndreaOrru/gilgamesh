from prompt_toolkit import HTML, print_formatted_text

NORMAL = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


def print(text: str, *args, **kwargs) -> None:
    print_formatted_text(HTML(text.format(*args, **kwargs)))
