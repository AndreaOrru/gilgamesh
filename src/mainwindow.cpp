#include "mainwindow.h"

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
  setupEditor();

  setCentralWidget(editor);
  setWindowTitle(tr("Gilgamesh"));
}

void MainWindow::setupEditor() {
  QFont font;
  font.setFamily("monospace");
  font.setFixedPitch(true);
  font.setPointSize(12);

  editor = new QTextEdit;
  editor->setFont(font);
}
