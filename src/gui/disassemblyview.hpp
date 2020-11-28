#pragma once

#include <QHash>
#include <QTextEdit>
#include <optional>

#include "instruction.hpp"
#include "label.hpp"
#include "types.hpp"

class Analysis;
class Highlighter;
class Instruction;
class MainWindow;
class Subroutine;

enum BlockState {
  None = -1,
  AssertedStateChange,
  CompleteJumpTable,
  EntryPointLabel,
  PartialJumpTable,
  UnknownStateChange,
};

class DisassemblyView : public QTextEdit {
  Q_OBJECT;

 public:
  DisassemblyView(QWidget* parent = nullptr);

 public slots:
  void renderAnalysis(Analysis* analysis);
  void jumpToLabel(Label label);

 private:
  MainWindow* mainWindow();

  void reset();
  void setBlockState(BlockState state);
  Instruction* getInstructionFromPos(const QPoint pos) const;
  std::optional<Label> getLabelFromPos(const QPoint pos) const;
  void jumpToBlock(int block, int verticalOffset = 0);
  void jumpToPC(PCPair pc, int verticalOffset = 0);

  void renderSubroutine(const Subroutine& subroutine);
  void renderInstruction(Instruction* instruction);
  std::string instructionComment(const Instruction* instruction);

  void contextMenuEvent(QContextMenuEvent* e) override;
  void mouseMoveEvent(QMouseEvent* e) override;
  void mouseDoubleClickEvent(QMouseEvent* e) override;

  void editAssertionDialog(Instruction* instruction);
  void editCommentDialog(Instruction* instruction);
  void editJumpTableDialog(Instruction* instruction);
  void editLabelDialog(Label label);

  void highlightCurrentLine();

  Analysis* analysis = nullptr;
  Highlighter* highlighter;
  QTextCharFormat defaultFormat;

  QHash<int, Label> blockToLabel;
  QHash<QString, int> labelToBlock;
  QHash<PCPair, int> pcToBlock;
  QHash<QString, PCPair> labelToPC;
  QHash<int, Instruction*> blockToInstruction;

  std::optional<int> lastClickedBlock;
  int lastClickedVerticalOffset;
  std::optional<PCPair> lastClickedPC;

  static const size_t LINE_LEN = 30;
  static const size_t OP_LEN = 3;
  static const size_t ARG_LEN = LINE_LEN - OP_LEN - 1;
};
