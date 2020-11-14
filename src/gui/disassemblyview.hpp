#pragma once

#include <QTextEdit>

class DisassemblyView : public QTextEdit {
  Q_OBJECT;

 public:
  DisassemblyView(QWidget* parent = nullptr);
};
