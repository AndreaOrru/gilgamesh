#include <QtWidgets>

#include "analysis.hpp"
#include "gui/disassemblyview.hpp"
#include "gui/labelsview.hpp"
#include "gui/mainwindow.hpp"
#include "qdockwidget.h"
#include "rom.hpp"

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
  setWindowTitle(tr("Gilgamesh"));

  setupMenus();
  setupWidgets();
}

void MainWindow::setupMenus() {
  QMenu* fileMenu = new QMenu(tr("&File"), this);
  menuBar()->addMenu(fileMenu);
  fileMenu->addAction(
      tr("&Open ROM..."), this, [this]() { openROM(); }, QKeySequence::Open);
  fileMenu->addSeparator();
  fileMenu->addAction(tr("E&xit"), qApp, &QApplication::quit,
                      QKeySequence::Quit);

  QMenu* helpMenu = new QMenu(tr("&Help"), this);
  menuBar()->addMenu(helpMenu);
  helpMenu->addAction(tr("&About"), this, &MainWindow::about);
}

void MainWindow::setupWidgets() {
  disassemblyView = new DisassemblyView(this);
  setCentralWidget(disassemblyView);

  leftDockWidget = new QDockWidget("Labels", this);
  labelsView = new LabelsView(leftDockWidget);
  leftDockWidget->setWidget(labelsView);
  addDockWidget(Qt::LeftDockWidgetArea, leftDockWidget);
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

    QStringList labels;
    for (auto& [pc, subroutine] : analysis->subroutines) {
      labels << QString::fromStdString(subroutine.label);
    }
    labelsView->setLabels(labels);
  }
}

void MainWindow::about() {
  QMessageBox::about(
      this, tr("About Gilgamesh"),
      tr("<div align='center'>"

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

         "</div>"));
}
