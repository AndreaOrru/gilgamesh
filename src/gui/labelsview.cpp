#include "gui/labelsview.hpp"

LabelsView::LabelsView(QWidget* parent) : QListWidget(parent) {
  setFont(QFont("monospace"));
}

void LabelsView::setLabels(QStringList labels) {
  clear();
  addItems(labels);
}
