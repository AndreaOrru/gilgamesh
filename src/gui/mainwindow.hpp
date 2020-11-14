#pragma once

#include <QMainWindow>

class Analysis;
class DisassemblyView;
class LabelsView;

class MainWindow : public QMainWindow {
  Q_OBJECT

 public:
  MainWindow(QWidget* parent = nullptr);

 signals:
  void analysisChanged(const Analysis* analysis);

 private slots:
  void openROM(const QString& path = QString());
  void about();

 private:
  void setupMenus();
  void setupWidgets();
  void setupSignals();

  QDockWidget* leftDockWidget;

  DisassemblyView* disassemblyView;
  LabelsView* labelsView;

  Analysis* analysis = nullptr;
};
