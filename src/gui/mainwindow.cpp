#include <QtWidgets>

#include "gui/constants.hpp"
#include "gui/mainwindow.hpp"

#include "analysis.hpp"
#include "gui/addentrypointdialog.hpp"
#include "gui/disassemblyview.hpp"
#include "gui/subroutinesview.hpp"
#include "rom.hpp"

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
  setWindowTitle(APP_TITLE);
  QApplication::setApplicationName(APP_TITLE);
  setWindowIcon(QIcon(APP_ICON_PATH));

  setupMenus();
  setupWidgets();
  setupSignals();
}

void MainWindow::setupMenus() {
  QMenu* fileMenu = new QMenu("&File", this);
  menuBar()->addMenu(fileMenu);
  fileMenu->addAction(
      "&Open ROM...", this, [this]() { openROM(); }, QKeySequence::Open);
  fileMenu->addSeparator();
  fileMenu->addAction("E&xit", qApp, &QApplication::quit, QKeySequence::Quit);

  QMenu* editMenu = new QMenu("&Edit", this);
  menuBar()->addMenu(editMenu);
  editMenu->addAction("Add &Entry Point...", this,
                      &MainWindow::addEntryPointDialog);

  QMenu* helpMenu = new QMenu("&Help", this);
  menuBar()->addMenu(helpMenu);
  helpMenu->addAction("&About...", this, &MainWindow::about);
}

void MainWindow::setupWidgets() {
  disassemblyView = new DisassemblyView(this);
  setCentralWidget(disassemblyView);

  leftDockWidget = new QDockWidget("Subroutines", this);
  subroutinesView = new SubroutinesView(leftDockWidget);
  leftDockWidget->setWidget(subroutinesView);
  addDockWidget(Qt::LeftDockWidgetArea, leftDockWidget);
}

void MainWindow::setupSignals() {
  connect(this, &MainWindow::analysisChanged, disassemblyView,
          &DisassemblyView::renderAnalysis);
  connect(this, &MainWindow::analysisChanged, subroutinesView,
          &SubroutinesView::renderAnalysis);

  connect(subroutinesView, &SubroutinesView::itemDoubleClicked, disassemblyView,
          [this](auto item) { disassemblyView->jumpToLabel(item->text()); });
}

void MainWindow::runAnalysis() {
  analysis->run();
  emit analysisChanged(analysis);
}

void MainWindow::openROM(const QString& path) {
  QString fileName = path;

  if (fileName.isNull()) {
    fileName = QFileDialog::getOpenFileName(this, "Open ROM", "",
                                            "SNES ROMs (*.smc *.sfc *.fig)");
  }

  if (!fileName.isEmpty()) {
    if (analysis != nullptr) {
      delete analysis;
    }
    analysis = new Analysis(fileName.toStdString());
    runAnalysis();
  }
}

void MainWindow::addEntryPointDialog() {
  AddEntryPointDialog dialog(this);
  if (dialog.exec()) {
    analysis->addEntryPoint(dialog.label, dialog.pc, dialog.state);
    runAnalysis();
  }
}

void MainWindow::about() {
  QMessageBox::about(
      this, "About Gilgamesh",
      "<div align='center'>"

      "<p><b>Gilgamesh</b></p>"
      "<p>0.1.0</p>"
      "<p>The definitive reverse engineering tool for SNES.</p>"

      "<p><a href='https://github.com/AndreaOrru/gilgamesh'>"
      "github.com/AndreaOrru/gilgamesh</a></p>"

      "<small>"
      "<p>Copyright (c) 2020, Andrea Orru</p>"
      "<p><a "
      "href='https://github.com/AndreaOrru/gilgamesh/blob/main/LICENSE'>"
      "BSD 2-Clause License</a></p>"
      "</small>"

      "</div>");
}
