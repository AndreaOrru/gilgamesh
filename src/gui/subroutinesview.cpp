#include "gui/subroutinesview.hpp"

#include "analysis.hpp"
#include "gui/constants.hpp"

SubroutinesView::SubroutinesView(QWidget* parent) : QListWidget(parent) {
  setFont(QFont(MONOSPACE_FONT));
}

void SubroutinesView::renderAnalysis(const Analysis* analysis) {
  clear();
  for (auto& [pc, subroutine] : analysis->subroutines) {
    auto item =
        new QListWidgetItem(QString::fromStdString(subroutine.label), this);

    if (subroutine.isEntryPoint) {
      item->setForeground(ENTRYPOINT_COLOR);
    } else if (subroutine.isResponsibleForUnknown()) {
      item->setForeground(Qt::red);
    }

    addItem(item);
  }
}
