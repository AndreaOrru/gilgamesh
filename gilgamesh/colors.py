from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.styles import Style

NORMAL = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

style = Style.from_dict({"red": "ansired", "green": "ansigreen"})


def print_html(html: str = "") -> None:
    print_formatted_text(HTML(html), style=style)
