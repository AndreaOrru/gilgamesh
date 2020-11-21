#include <QDebug>

#include "gui/disassemblyview.hpp"

#include "analysis.hpp"
#include "highlighter.hpp"
#include "instruction.hpp"
#include "subroutine.hpp"
#include "utils.hpp"

DisassemblyView::DisassemblyView(QWidget* parent) : QTextEdit(parent) {
  setFontFamily("Iosevka Fixed SS09 Extended");
  setReadOnly(true);
  setTextInteractionFlags(this->textInteractionFlags() |
                          Qt::TextSelectableByKeyboard);

  highlighter = new Highlighter(document());
}

void DisassemblyView::setAnalysis(const Analysis* analysis) {
  clear();
  for (auto& [pc, subroutine] : analysis->subroutines) {
    renderSubroutine(subroutine);
  }
  moveCursor(QTextCursor::Start);
}

void DisassemblyView::jumpToLabel(QString label) {
  auto blockNumber = labelToBlockNumber[label];
  auto block = document()->findBlockByNumber(blockNumber);

  QTextCursor cursor(block);
  moveCursor(QTextCursor::End);
  setTextCursor(cursor);
}

void DisassemblyView::renderSubroutine(const Subroutine& subroutine) {
  auto label = qformat("%s:", subroutine.label.c_str());
  append(label);

  auto blockNumber = textCursor().blockNumber();
  labelToBlockNumber[QString::fromStdString(subroutine.label)] = blockNumber;

  for (auto& [pc, instruction] : subroutine.instructions) {
    renderInstruction(instruction);
  }
  append("");
}

void DisassemblyView::setBlockState(BlockState state) {
  textCursor().block().setUserState(state);
}

void DisassemblyView::renderInstruction(const Instruction* instruction) {
  if (auto label = instruction->label) {
    append(qformat(".%s:", label->c_str()));
  }

  auto code = qformat("  %-30s; $%06X | %s", instruction->toString().c_str(),
                      instruction->pc, "");
  append(code);

  auto instructionStateChange = instruction->stateChange();
  if (instructionStateChange.has_value() && instructionStateChange->unknown()) {
    setBlockState(BlockState::UnknownStateChange);
  }
}
