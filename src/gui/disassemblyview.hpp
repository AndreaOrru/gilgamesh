#pragma once

#include <QTextEdit>

class Analysis;
class Highlighter;
class Instruction;
class Subroutine;

class DisassemblyView : public QTextEdit {
  Q_OBJECT;

 public:
  DisassemblyView(QWidget* parent = nullptr);

 public slots:
  void setAnalysis(const Analysis* analysis);

 private:
  void renderSubroutine(const Subroutine& subroutine);
  void renderInstruction(const Instruction* instruction);

  Highlighter* highlighter;
};
