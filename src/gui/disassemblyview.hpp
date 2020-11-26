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
  void jumpToLabel(QString label);

 private:
  MainWindow* mainWindow();

  void reset();
  void setBlockState(BlockState state);
  Instruction* getInstructionFromPos(const QPoint pos) const;
  std::optional<std::pair<InstructionPC, QString>> getLabelFromPos(
      const QPoint pos) const;
  void jumpToPosition(int blockNumber, int verticalOffset = 0);

  void renderSubroutine(const Subroutine& subroutine);
  void renderInstruction(Instruction* instruction);
  std::string instructionComment(const Instruction* instruction);

  void contextMenuEvent(QContextMenuEvent* e);
  void editAssertionDialog(Instruction* instruction);
  void editCommentDialog(Instruction* instruction);
  void editJumpTableDialog(Instruction* instruction);
  void editLabelDialog(InstructionPC pc, QString label);

  void highlightCurrentLine();

  Analysis* analysis = nullptr;
  Highlighter* highlighter;

  QHash<QString, int> labelToBlockNumber;
  QHash<int, std::pair<InstructionPC, QString>> blockNumberToLabel;
  QHash<int, Instruction*> blockNumberToInstruction;
  QHash<std::pair<InstructionPC, SubroutinePC>, int> instructionToBlockNumber;

  std::optional<std::pair<InstructionPC, SubroutinePC>> lastClickedInstruction;
  int lastClickedVerticalOffset;
};
