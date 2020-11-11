#pragma once

#include <QMainWindow>

class QTextEdit;

class MainWindow : public QMainWindow {
  Q_OBJECT

 public:
  MainWindow(QWidget* parent = nullptr);

 public slots:
  void openFile(const QString& path = QString());

 private:
  void setupEditor();
  void setupFileMenu();

  QTextEdit* editor;
};
