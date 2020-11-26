#pragma once

#include <QMainWindow>

class Analysis;
class DisassemblyView;
class SubroutinesView;

class MainWindow : public QMainWindow {
  Q_OBJECT

 public:
  MainWindow(QWidget* parent = nullptr);
  void runAnalysis();

 signals:
  void analysisChanged(const Analysis* analysis);

 private slots:
  void openROM(const QString& path = QString());
  void saveAnalysis();
  void addEntryPointDialog();
  void about();

 private:
  void setupMenus();
  void setupWidgets();
  void setupSignals();

  QDockWidget* leftDockWidget;

  DisassemblyView* disassemblyView;
  SubroutinesView* subroutinesView;

  Analysis* analysis = nullptr;
};

#define ACCESS_MAIN_WINDOW \
  MainWindow* mainWindow() { return qobject_cast<MainWindow*>(parent()); }
