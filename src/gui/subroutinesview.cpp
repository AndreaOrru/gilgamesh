#include "gui/subroutinesview.hpp"

#include "analysis.hpp"
#include "gui/constants.hpp"

SubroutinesView::SubroutinesView(QWidget* parent) : QListWidget(parent) {
  setFont(QFont(MONOSPACE_FONT));
}

void SubroutinesView::renderAnalysis(const Analysis* analysis) {
  QStringList labels;
  for (auto& [pc, subroutine] : analysis->subroutines) {
    labels << QString::fromStdString(subroutine.label);
  }

  clear();
  addItems(labels);
}
