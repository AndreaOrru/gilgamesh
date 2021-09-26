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
  defaultFormat = textCursor().charFormat();

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

  blockToLabel.clear();
  labelToBlock.clear();
  pcToBlock.clear();
  labelToPC.clear();
  blockToInstruction.clear();
}

void DisassemblyView::renderAnalysis(Analysis* analysis) {
  this->analysis = analysis;

  reset();
  for (auto& [pc, subroutine] : analysis->subroutines) {
    renderSubroutine(subroutine);
  }

  if (lastClickedPC) {
    jumpToPC(*lastClickedPC, lastClickedVerticalOffset);
  } else if (lastClickedBlock.has_value()) {
    jumpToBlock(*lastClickedBlock, lastClickedVerticalOffset);
  } else {
    moveCursor(QTextCursor::Start);
  }
}

void DisassemblyView::jumpToLabel(Label label) {
  jumpToBlock(labelToBlock[label.combinedLabel().c_str()]);
}

void DisassemblyView::jumpToPC(PCPair pc, int verticalOffset) {
  jumpToBlock(pcToBlock[pc], verticalOffset);
}

void DisassemblyView::jumpToBlock(int block, int verticalOffset) {
  QTextCursor cursor(document()->findBlockByNumber(block));
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
  auto search = blockToInstruction.find(cursor.blockNumber());
  if (search != blockToInstruction.end()) {
    return search.value();
  } else {
    return nullptr;
  }
}

optional<Label> DisassemblyView::getLabelFromPos(const QPoint pos) const {
  auto cursor = cursorForPosition(pos);
  auto search = blockToLabel.find(cursor.blockNumber());
  if (search != blockToLabel.end()) {
    // Label.
    return *search;
  } else {
    auto label = anchorAt(pos);
    if (!label.isEmpty()) {
      // Label argument.
      return label;
    } else {
      // No label.
      return nullopt;
    }
  }
}

void DisassemblyView::setBlockState(BlockState state) {
  textCursor().block().setUserState(state);
}

void DisassemblyView::renderSubroutine(const Subroutine& subroutine) {
  auto label = subroutine.label;
  append(qformat("%s:", label.c_str()));

  auto block = textCursor().blockNumber();
  blockToLabel[block] = label;
  labelToBlock[label.c_str()] = block;
  labelToPC[label.c_str()] = {subroutine.pc, subroutine.pc};

  if (subroutine.isEntryPoint) {
    setBlockState(BlockState::EntryPointLabel);
  }

  for (auto& [pc, instruction] : subroutine.instructions) {
    renderInstruction(instruction);
  }
  append("");
}

void DisassemblyView::renderInstruction(Instruction* instruction) {
  PCPair pc = {instruction->pc, instruction->subroutinePC};
  if (auto label = instruction->label) {
    append(qformat(".%s:", label->c_str()));
    auto block = textCursor().blockNumber();
    auto combinedLabel = QString::fromStdString(label->combinedLabel());
    blockToLabel[block] = combinedLabel;
    labelToBlock[combinedLabel] = block;
    labelToPC[combinedLabel] = pc;
  }

  // Instruction name.
  auto cursor = textCursor();
  auto format = defaultFormat;
  cursor.insertText("\n  ");
  cursor.insertText((instruction->name() + " ").c_str());

  // Instruction argument.
  if (auto argumentLabel = instruction->argumentLabel()) {
    format.setAnchor(true);
    format.setAnchorHref(argumentLabel->combinedLabel().c_str());
  }
  QString argument = instruction->argumentString().c_str();
  cursor.insertText(argument, format);

  // Instruction comment.
  format = defaultFormat;
  cursor.insertText(QString(ARG_LEN - argument.size(), ' '), format);
  cursor.insertText(qformat("; $%06X |%s", instruction->pc,
                            instructionComment(instruction).c_str()),
                    format);

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

  auto block = textCursor().blockNumber();
  blockToInstruction[block] = instruction;
  pcToBlock[pc] = block;
}

string DisassemblyView::instructionComment(const Instruction* instruction) {
  if (!instruction->comment().empty()) {
    return " " + instruction->comment();
  }

  if (auto assertion = instruction->assertion()) {
    return format(" %s: %s",
                  assertion->type == AssertionType::Instruction ? "Instruction"
                                                                : "Subroutine",
                  ((string)*assertion).c_str());
  }

  if (auto stateChange = instruction->stateChange()) {
    switch (stateChange->unknownReason) {
      case UnknownReason::SuspectInstruction:
        return " Suspect instruction";
      case UnknownReason::MultipleReturnStates:
        return " Multiple return states";
      case UnknownReason::IndirectJump:
        return " Indirect jump";
      case UnknownReason::StackManipulation:
        return " Stack manipulation";
      case UnknownReason::Recursion:
        return " Recursion";
      case UnknownReason::MutableCode:
        return " Mutable code";
      default:
        break;
    }
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
  auto cursor = cursorForPosition(e->pos());
  setTextCursor(cursor);
  lastClickedPC = nullopt;
  lastClickedBlock = cursor.blockNumber();
  lastClickedVerticalOffset = cursorRect(cursorForPosition(e->pos())).y();

  QMenu* menu = createStandardContextMenu();
  if (auto instruction = getInstructionFromPos(e->pos())) {
    lastClickedPC = {instruction->pc, instruction->subroutinePC};

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

  if (auto label = getLabelFromPos(e->pos())) {
    auto editLabel = menu->addAction("Edit Label...");
    connect(editLabel, &QAction::triggered, this,
            [=]() { this->editLabelDialog(*label); });
  }

  menu->exec(e->globalPos());
  delete menu;
}

void DisassemblyView::mouseMoveEvent(QMouseEvent* e) {
  QTextEdit::mouseMoveEvent(e);

  if (!anchorAt(e->pos()).isEmpty()) {
    viewport()->setCursor(Qt::PointingHandCursor);
  } else {
    viewport()->setCursor(Qt::IBeamCursor);
  }
}

void DisassemblyView::mouseDoubleClickEvent(QMouseEvent* e) {
  auto label = anchorAt(e->pos());
  if (!label.isEmpty()) {
    jumpToLabel(label);
  }
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

void DisassemblyView::editLabelDialog(Label label) {
  bool ok;
  QString newLabel = QInputDialog::getText(
      this, "Edit Label", "Label:", QLineEdit::Normal, label, &ok);

  if (ok && !newLabel.isEmpty()) {
    auto& [pc, subroutinePC] = labelToPC[label.combinedLabel().c_str()];
    analysis->renameLabel(newLabel.toStdString(), pc, subroutinePC);
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
