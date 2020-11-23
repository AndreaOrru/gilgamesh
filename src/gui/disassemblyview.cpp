#include <QInputDialog>
#include <QMenu>
#include <QScrollBar>

#include "gui/disassemblyview.hpp"

#include "analysis.hpp"
#include "gui/editassertiondialog.hpp"
#include "gui/editjumptabledialog.hpp"
#include "gui/highlighter.hpp"
#include "gui/mainwindow.hpp"
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

MainWindow* DisassemblyView::mainWindow() {
  return qobject_cast<MainWindow*>(parent());
}

void DisassemblyView::reset() {
  clear();
  labelToBlockNumber.clear();
  blockNumberToInstruction.clear();
}

void DisassemblyView::renderAnalysis(const Analysis* analysis) {
  auto savedScroll = verticalScrollBar()->value();
  reset();

  for (auto& [pc, subroutine] : analysis->subroutines) {
    renderSubroutine(subroutine);
  }

  verticalScrollBar()->setValue(savedScroll);
}

void DisassemblyView::jumpToLabel(QString label) {
  auto blockNumber = labelToBlockNumber[label];
  auto block = document()->findBlockByNumber(blockNumber);

  QTextCursor cursor(block);
  moveCursor(QTextCursor::End);
  setTextCursor(cursor);
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

void DisassemblyView::setBlockState(BlockState state) {
  textCursor().block().setUserState(state);
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

void DisassemblyView::renderInstruction(Instruction* instruction) {
  if (auto label = instruction->label) {
    append(qformat(".%s:", label->c_str()));
  }
  append(qformat("  %-30s; $%06X | %s", instruction->toString().c_str(),
                 instruction->pc, instruction->comment().c_str()));

  auto instructionStateChange = instruction->stateChange();
  if (instruction->assertion().has_value()) {
    setBlockState(BlockState::AssertedStateChange);
  } else if (instructionStateChange.has_value() &&
             instructionStateChange->unknown()) {
    setBlockState(BlockState::UnknownStateChange);
  }

  auto blockNumber = textCursor().blockNumber();
  blockNumberToInstruction[blockNumber] = instruction;
}

void DisassemblyView::contextMenuEvent(QContextMenuEvent* e) {
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
  }

  menu->exec(e->globalPos());
  delete menu;
}

void DisassemblyView::editAssertionDialog(Instruction* instruction) {
  EditAssertionDialog dialog(instruction->assertion(), this);
  if (dialog.exec()) {
    auto analysis = instruction->analysis;
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
    renderAnalysis(instruction->analysis);
  }
}

void DisassemblyView::editJumpTableDialog(Instruction* instruction) {
  EditJumpTableDialog dialog(this);
  if (dialog.exec()) {
    auto analysis = instruction->analysis;
    auto range = dialog.range;

    analysis->defineJumpTable(instruction->pc, range);
    mainWindow()->runAnalysis();
  }
}
