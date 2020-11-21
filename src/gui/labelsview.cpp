#include "gui/labelsview.hpp"

#include "analysis.hpp"

LabelsView::LabelsView(QWidget* parent) : QListWidget(parent) {
  setFont(QFont("Iosevka Fixed SS09 Extended"));
}

void LabelsView::renderAnalysis(const Analysis* analysis) {
  QStringList labels;
  for (auto& [pc, subroutine] : analysis->subroutines) {
    labels << QString::fromStdString(subroutine.label);
  }

  clear();
  addItems(labels);
}
