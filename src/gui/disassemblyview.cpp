#include "gui/disassemblyview.hpp"

#include "analysis.hpp"
#include "highlighter.hpp"
#include "utils.hpp"

DisassemblyView::DisassemblyView(QWidget* parent) : QTextEdit(parent) {
  setFontFamily("monospace");
  setReadOnly(true);

  highlighter = new Highlighter(document());
}

void DisassemblyView::setAnalysis(const Analysis* analysis) {
  clear();

  for (auto& [pc, subroutine] : analysis->subroutines) {
    renderSubroutine(subroutine);
  }
}

void DisassemblyView::renderSubroutine(const Subroutine& subroutine) {
  auto label = qformat("%s:", subroutine.label.c_str());
  append(label);

  for (auto& [pc, instruction] : subroutine.instructions) {
    renderInstruction(instruction);
  }
  append("");
}

void DisassemblyView::renderInstruction(const Instruction* instruction) {
  if (auto label = instruction->label) {
    append(qformat(".%s:", label->c_str()));
  }

  auto code = qformat("  %-30s; $%06X | %s", instruction->toString().c_str(),
                      instruction->pc, "");
  append(code);
}
