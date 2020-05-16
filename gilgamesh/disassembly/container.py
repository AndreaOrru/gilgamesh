import os
from subprocess import check_call
from tempfile import NamedTemporaryFile
from typing import Dict, Iterable, List

from gilgamesh.disassembly.disassembly import Disassembly
from gilgamesh.disassembly.parser import Token
from gilgamesh.disassembly.renames import apply_renames
from gilgamesh.errors import ParserError
from gilgamesh.log import Log
from gilgamesh.subroutine import Subroutine


class DisassemblyContainer(Disassembly):
    HEADER = ";;" + ("=" * 41) + "\n"

    def __init__(self, log: Log, subroutines: Iterable[Subroutine]):
        super().__init__(next(iter(subroutines)))  # HACK
        self.disassemblies = [Disassembly(sub) for sub in subroutines]

    def edit(self) -> None:
        # Save the subroutines' disassembly in a temporary file.
        original_tokens: List[List[List[Token]]] = []
        with NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            for disassembly in self.disassemblies:
                f.write(self.HEADER)
                text, tokens = disassembly._get_text()
                original_tokens.append(tokens)
                f.write(text)
                f.write("\n\n\n")
            filename = f.name

        # Edit the file in an editor.
        check_call([*os.environ["EDITOR"].split(), filename])
        new_text = open(filename).read()
        os.remove(filename)

        global_renames: Dict[str, str] = {}
        subroutine_texts = new_text.split(self.HEADER)

        # Apply all the changes local to the individual subroutines.
        for i, disassembly in enumerate(self.disassemblies):
            new_tokens = disassembly._text_to_tokens(subroutine_texts[i + 1])
            renames = disassembly._apply_changes(original_tokens[i], new_tokens)

            # Gather global renames.
            for old, new in renames.items():
                if global_renames.get(old, new) != new:
                    raise ParserError(f'Ambiguous label change: "{old}" -> "{new}".')
                global_renames[old] = new

        # Apply the global renames.
        apply_renames(self.log, global_renames)
