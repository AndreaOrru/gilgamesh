#pragma once

#include <QHash>
#include <QTextEdit>

#include "types.hpp"

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
  void jumpToLabel(QString label);

 private:
  void renderSubroutine(const Subroutine& subroutine);
  void renderInstruction(const Instruction* instruction);

  Highlighter* highlighter;
  QHash<QString, int> labelToBlockNumber;
};
