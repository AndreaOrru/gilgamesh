from gilgamesh.code_generator import CodeGenerator


class SNESGenerator(CodeGenerator):
    def compile(self):
        buffer = ''
        buffer += self._generate_prologue()

        for instruction in self._db.instructions():
            if instruction.label:
                buffer += '\nseek(0x{:06X})\n'.format(instruction.pc)
                buffer += '{}:\n'.format(instruction.label)
            buffer += '    {:<20}// ${:06X}\n'.format(instruction.format(), instruction.pc)

        return buffer

    @staticmethod
    def _generate_prologue():
        # FIXME: This will only work for LoROM.
        return """arch snes.cpu
macro seek(variable offset) {
    origin ((offset & $7F0000) >> 1) | (offset & $7F0000) & $7FFF)
    base offset
}\n"""
