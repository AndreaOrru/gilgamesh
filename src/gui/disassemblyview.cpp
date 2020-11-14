#include "gui/disassemblyview.hpp"

DisassemblyView::DisassemblyView(QWidget* parent) : QTextEdit(parent) {
  setReadOnly(true);
}
