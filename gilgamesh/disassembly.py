from bs4 import BeautifulSoup as BS

from gilgamesh.instruction import Instruction
from gilgamesh.log import Log
from gilgamesh.subroutine import Subroutine


class Disassembly:
    def __init__(self, log: Log, subroutine: Subroutine):
        self.log = log
        self.subroutine = subroutine

    def get_html(self) -> str:
        s = []
        for instruction in self.subroutine.instructions.values():
            s.append(self._instruction(instruction))
            s.append(self._assertion_info(instruction))
        return "".join(s)

    def get_text(self) -> str:
        html = self.get_html()
        return BS(f"<pre>{html}</pre>", "html.parser").get_text()

    def _instruction(self, instruction: Instruction) -> str:
        s = []

        subroutine_pc = instruction.subroutine
        label = self.log.get_label(instruction.pc, subroutine_pc)
        if label:
            s.append(f"<red>{label}</red>:\n")

        operation = "<green>{:4}</green>".format(instruction.name)
        if instruction.argument_alias:
            argument = "<red>{:16}</red>".format(instruction.argument_alias)
        else:
            argument = "{:16}".format(instruction.argument_string)

        s.append(
            "  {}{}<grey>; ${:06X} | {}</grey>\n".format(
                operation,
                argument,
                instruction.pc,
                self.log.comments.get(instruction.pc, ""),
            )
        )

        return "".join(s)

    def _assertion_info(self, instruction: Instruction) -> str:
        subroutine = self.log.subroutines[instruction.subroutine]
        if subroutine.has_asserted_state_change and (
            instruction.stopped_execution or instruction.is_return
        ):
            return "  <grey>; Asserted state change: {}</grey>\n".format(
                subroutine.state_change.state_expr
            )
        elif instruction.pc in self.log.instruction_assertions:
            return "  <grey>; Asserted state change: {}</grey>\n".format(
                self.log.instruction_assertions[instruction.pc].state_expr
            )
        elif instruction.stopped_execution:
            return "  <grey>; Unknown state at ${:06X}</grey>\n".format(
                instruction.next_pc
            )
        return ""
