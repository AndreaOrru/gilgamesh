#include "gui/subroutinesview.hpp"

#include "analysis.hpp"

SubroutinesView::SubroutinesView(QWidget* parent) : QListWidget(parent) {
  setFont(QFont("Iosevka Fixed SS09 Extended"));
}

void SubroutinesView::renderAnalysis(const Analysis* analysis) {
  QStringList labels;
  for (auto& [pc, subroutine] : analysis->subroutines) {
    labels << QString::fromStdString(subroutine.label);
  }

  clear();
  addItems(labels);
}
