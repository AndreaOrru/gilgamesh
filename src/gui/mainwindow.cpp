#include <QtWidgets>

#include "analysis.hpp"
#include "gui/mainwindow.hpp"
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
    if (analysis != nullptr) {
      delete analysis;
    }
    ROM rom(fileName.toStdString());
    analysis = new Analysis(rom);
    analysis->run();

    for (auto& [pc, subroutine] : analysis->subroutines) {
      for (auto& [pc, instruction] : subroutine.instructions) {
        qInfo() << instruction->toString().c_str();
      }
    }
  }
}
