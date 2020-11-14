#include "gui/disassemblyview.hpp"

#include "analysis.hpp"

DisassemblyView::DisassemblyView(QWidget* parent) : QTextEdit(parent) {
  setFontFamily("monospace");
  setReadOnly(true);
}

void DisassemblyView::setAnalysis(const Analysis* analysis) {
  for (auto& [pc, subroutine] : analysis->subroutines) {
    auto label = QString::fromStdString(subroutine.label);
    append(label);
  }
}
