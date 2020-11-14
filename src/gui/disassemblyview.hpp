#pragma once

#include <QTextEdit>

class Analysis;

class DisassemblyView : public QTextEdit {
  Q_OBJECT;

 public:
  DisassemblyView(QWidget* parent = nullptr);

 public slots:
  void setAnalysis(const Analysis* analysis);
};
