from prompt_toolkit import HTML, print_formatted_text  # type: ignore
from prompt_toolkit.styles import Style  # type: ignore

style = Style.from_dict(
    {
        "black": "ansiblack",
        "blue": "ansiblue",
        "cyan": "ansicyan",
        "green": "ansigreen",
        "magenta": "ansimagenta",
        "red": "ansired",
        "yellow": "ansiyellow",
    }
)


def print_html(html: str = "") -> None:
    print_formatted_text(HTML(html), style=style)


def print_error(text: str) -> None:
    print_html(f"<red>{text}</red>\n")
