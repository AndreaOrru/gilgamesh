#include <QInputDialog>
#include <QMenu>
#include <QScrollBar>

#include "gui/disassemblyview.hpp"

#include "analysis.hpp"
#include "gui/constants.hpp"
#include "gui/editassertiondialog.hpp"
#include "gui/editjumptabledialog.hpp"
#include "gui/highlighter.hpp"
#include "gui/mainwindow.hpp"
#include "instruction.hpp"
#include "subroutine.hpp"
#include "utils.hpp"

using namespace std;

DisassemblyView::DisassemblyView(QWidget* parent) : QTextEdit(parent) {
  setFontFamily(MONOSPACE_FONT);
  setReadOnly(true);

  highlighter = new Highlighter(document());

  connect(this, &DisassemblyView::cursorPositionChanged, this,
          &DisassemblyView::highlightCurrentLine);
  highlightCurrentLine();
}

MainWindow* DisassemblyView::mainWindow() {
  return qobject_cast<MainWindow*>(parent());
}

void DisassemblyView::reset() {
  clear();
  labelToBlockNumber.clear();
  blockNumberToLabel.clear();
  blockNumberToInstruction.clear();
  instructionToBlockNumber.clear();
}

void DisassemblyView::renderAnalysis(Analysis* analysis) {
  this->analysis = analysis;

  reset();
  for (auto& [pc, subroutine] : analysis->subroutines) {
    renderSubroutine(subroutine);
  }

  if (lastClickedInstruction.has_value()) {
    auto blockNumber = instructionToBlockNumber[*lastClickedInstruction];
    jumpToPosition(blockNumber, lastClickedVerticalOffset);
  } else {
    moveCursor(QTextCursor::Start);
  }
}

void DisassemblyView::jumpToLabel(QString label) {
  auto blockNumber = labelToBlockNumber[label];
  jumpToPosition(blockNumber);
}

void DisassemblyView::jumpToPosition(int blockNumber, int verticalOffset) {
  auto block = document()->findBlockByNumber(blockNumber);

  QTextCursor cursor(block);
  moveCursor(QTextCursor::End);
  auto verticalScrollEnd = verticalScrollBar()->value();
  setTextCursor(cursor);

  // Don't change the vertical position if we're at the end of the document.
  auto verticalScrollBase = verticalScrollBar()->value();
  if (verticalScrollBase != verticalScrollEnd) {
    verticalScrollBar()->setValue(verticalScrollBase - verticalOffset);
  }
}

Instruction* DisassemblyView::getInstructionFromPos(const QPoint pos) const {
  auto cursor = cursorForPosition(pos);
  auto search = blockNumberToInstruction.find(cursor.blockNumber());
  if (search != blockNumberToInstruction.end()) {
    return search.value();
  } else {
    return nullptr;
  }
}

optional<pair<InstructionPC, QString>> DisassemblyView::getLabelFromPos(
    const QPoint pos) const {
  auto cursor = cursorForPosition(pos);
  auto search = blockNumberToLabel.find(cursor.blockNumber());
  if (search != blockNumberToLabel.end()) {
    return search.value();
  } else {
    return nullopt;
  }
}

void DisassemblyView::setBlockState(BlockState state) {
  textCursor().block().setUserState(state);
}

void DisassemblyView::renderSubroutine(const Subroutine& subroutine) {
  auto label = qformat("%s:", subroutine.label.c_str());
  append(label);
  blockNumberToLabel[textCursor().blockNumber()] = {
      subroutine.pc, QString::fromStdString(subroutine.label)};

  if (subroutine.isEntryPoint) {
    setBlockState(BlockState::EntryPointLabel);
  }

  auto blockNumber = textCursor().blockNumber();
  labelToBlockNumber[QString::fromStdString(subroutine.label)] = blockNumber;

  for (auto& [pc, instruction] : subroutine.instructions) {
    renderInstruction(instruction);
  }
  append("");
}

void DisassemblyView::renderInstruction(Instruction* instruction) {
  if (auto label = instruction->label) {
    append(qformat(".%s:", label->c_str()));
    blockNumberToLabel[textCursor().blockNumber()] = {
        instruction->pc, QString::fromStdString(*label)};
  }
  append(qformat("  %-30s; $%06X |%s", instruction->toString().c_str(),
                 instruction->pc, instructionComment(instruction).c_str()));

  auto instructionStateChange = instruction->stateChange();
  if (instruction->assertion().has_value()) {
    setBlockState(BlockState::AssertedStateChange);
  } else if (instructionStateChange.has_value() &&
             instructionStateChange->unknown()) {
    setBlockState(BlockState::UnknownStateChange);
  } else if (auto jumpTable = instruction->jumpTable()) {
    if (jumpTable->status == JumpTableStatus::Complete) {
      setBlockState(BlockState::CompleteJumpTable);
    } else {
      setBlockState(BlockState::PartialJumpTable);
    }
  }

  auto blockNumber = textCursor().blockNumber();
  blockNumberToInstruction[blockNumber] = instruction;
  instructionToBlockNumber[{instruction->pc, instruction->subroutinePC}] =
      blockNumber;
}

string DisassemblyView::instructionComment(const Instruction* instruction) {
  if (!instruction->comment().empty()) {
    return " " + instruction->comment();
  }

  if (instruction->isSepRep()) {
    auto size = instruction->operation() == Op::SEP ? 8 : 16;
    auto arg = *instruction->argument();

    if ((arg & 0x30) == 0x30) {
      return format(" A: %d-bits, X: %d-bits", size, size);
    } else if ((arg & 0x20) == 0x20) {
      return format(" A: %d-bits", size);
    } else if ((arg & 0x10) == 0x10) {
      return format(" X: %d-bits", size);
    }
  }
  return "";
}

void DisassemblyView::contextMenuEvent(QContextMenuEvent* e) {
  setTextCursor(cursorForPosition(e->pos()));
  QMenu* menu = createStandardContextMenu();

  if (auto instruction = getInstructionFromPos(e->pos())) {
    menu->addSeparator();

    auto editAssertion = menu->addAction("Edit Assertion...");
    connect(editAssertion, &QAction::triggered, this,
            [=]() { this->editAssertionDialog(instruction); });

    auto editComment = menu->addAction("Edit Comment...");
    connect(editComment, &QAction::triggered, this,
            [=]() { this->editCommentDialog(instruction); });

    if (instruction->isControl() &&
        !instruction->absoluteArgument().has_value()) {
      auto editJumpTable = menu->addAction("Edit Jump Table...");
      connect(editJumpTable, &QAction::triggered, this,
              [=]() { this->editJumpTableDialog(instruction); });
    }

    lastClickedInstruction = {instruction->pc, instruction->subroutinePC};
    lastClickedVerticalOffset = cursorRect(cursorForPosition(e->pos())).y();
  }

  if (auto pcLabel = getLabelFromPos(e->pos())) {
    auto editLabel = menu->addAction("Edit Label...");
    connect(editLabel, &QAction::triggered, this,
            [=]() { this->editLabelDialog(pcLabel->first, pcLabel->second); });
  }

  menu->exec(e->globalPos());
  delete menu;
}

void DisassemblyView::editAssertionDialog(Instruction* instruction) {
  EditAssertionDialog dialog(instruction->assertion(), this);
  if (dialog.exec()) {
    auto assertion = dialog.assertion;
    if (assertion.has_value()) {
      analysis->addAssertion(*assertion, instruction->pc,
                             instruction->subroutinePC);
    } else {
      analysis->removeAssertion(instruction->pc, instruction->subroutinePC);
    }

    mainWindow()->runAnalysis();
  };
}

void DisassemblyView::editCommentDialog(Instruction* instruction) {
  auto comment = QString::fromStdString(instruction->comment());

  bool ok;
  QString newComment = QInputDialog::getText(
      this, "Edit Comment", "Comment:", QLineEdit::Normal, comment, &ok);

  if (ok) {
    instruction->setComment(newComment.toStdString());
    mainWindow()->runAnalysis();
  }
}

void DisassemblyView::editJumpTableDialog(Instruction* instruction) {
  EditJumpTableDialog dialog(instruction->jumpTable(), this);
  if (dialog.exec()) {
    auto range = dialog.range;
    auto status = dialog.status;

    if (range.has_value()) {
      analysis->defineJumpTable(instruction->pc, *range, status);
    } else {
      analysis->undefineJumpTable(instruction->pc);
    }

    mainWindow()->runAnalysis();
  }
}

void DisassemblyView::editLabelDialog(InstructionPC pc, QString label) {
  bool ok;
  QString newLabel = QInputDialog::getText(
      this, "Edit Label", "Label:", QLineEdit::Normal, label, &ok);

  if (ok && !newLabel.isEmpty()) {
    analysis->renameLabel(pc, newLabel.toStdString());
    mainWindow()->runAnalysis();
  }
}

void DisassemblyView::highlightCurrentLine() {
  QColor lineColor = QColor(Qt::yellow).lighter(160);

  // Reuse background color if there's one.
  auto formats = textCursor().block().layout()->formats();
  for (auto& format : formats) {
    auto background = format.format.background().color();
    if (background != this->textBackgroundColor()) {
      lineColor = background;
    }
  }

  QTextEdit::ExtraSelection selection;
  selection.format.setBackground(lineColor);
  selection.format.setProperty(QTextFormat::FullWidthSelection, true);
  selection.cursor = textCursor();
  selection.cursor.clearSelection();

  setExtraSelections({selection});
}
