#include <QtWidgets>

#include "mainwindow.hpp"
#include "rom.hpp"

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
  setupFileMenu();
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

void MainWindow::setupFileMenu() {
  QMenu* fileMenu = new QMenu(tr("&File"), this);
  menuBar()->addMenu(fileMenu);

  fileMenu->addAction(
      tr("&Open ROM..."), this, [this]() { openROM(); }, QKeySequence::Open);

  fileMenu->addSeparator();
  fileMenu->addAction(tr("E&xit"), qApp, &QApplication::quit,
                      QKeySequence::Quit);
}

void MainWindow::openROM(const QString& path) {
  QString fileName = path;

  if (fileName.isNull()) {
    fileName = QFileDialog::getOpenFileName(this, tr("Open ROM"), "",
                                            "SNES ROMs (*.smc *.sfc *.fig)");
  }

  if (!fileName.isEmpty()) {
    if (rom != nullptr) {
      delete rom;
    }
    rom = new ROM(fileName.toStdString());
  }
}
