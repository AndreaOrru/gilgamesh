#pragma once

#include <QHash>
#include <QTextEdit>
#include <optional>

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
  PartialJumpTable,
  UnknownStateChange,
};

class DisassemblyView : public QTextEdit {
  Q_OBJECT;

 public:
  DisassemblyView(QWidget* parent = nullptr);

 public slots:
  void renderAnalysis(const Analysis* analysis);
  void jumpToLabel(QString label);

 private:
  MainWindow* mainWindow();

  void reset();
  void setBlockState(BlockState state);
  Instruction* getInstructionFromPos(const QPoint pos) const;
  void jumpToPosition(int blockNumber, int verticalOffset = 0);

  void renderSubroutine(const Subroutine& subroutine);
  void renderInstruction(Instruction* instruction);

  void contextMenuEvent(QContextMenuEvent* e);
  void editAssertionDialog(Instruction* instruction);
  void editCommentDialog(Instruction* instruction);
  void editJumpTableDialog(Instruction* instruction);

  Highlighter* highlighter;
  QHash<QString, int> labelToBlockNumber;
  QHash<int, Instruction*> blockNumberToInstruction;
  QHash<std::pair<InstructionPC, SubroutinePC>, int> instructionToBlockNumber;

  std::optional<std::pair<InstructionPC, SubroutinePC>> lastClickedInstruction;
  int lastClickedVerticalOffset;
};
