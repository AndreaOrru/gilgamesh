#pragma once

#include <QMainWindow>
#include <QTextEdit>

class MainWindow : public QMainWindow {
  Q_OBJECT

 public:
  MainWindow(QWidget* parent = nullptr);

 private:
  void setupEditor();

  QTextEdit* editor;
};
