#pragma once

#include <QMainWindow>
#include "gui/disassemblyview.hpp"
#include "qdockwidget.h"

class Analysis;
class DisassemblyView;
class LabelsView;

class MainWindow : public QMainWindow {
  Q_OBJECT

 public:
  MainWindow(QWidget* parent = nullptr);

 public slots:
  void openROM(const QString& path = QString());
  void about();

 private:
  void setupMenus();
  void setupWidgets();

  QDockWidget* leftDockWidget;

  DisassemblyView* disassemblyView;
  LabelsView* labelsView;

  Analysis* analysis;
};
