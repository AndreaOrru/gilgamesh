#include <QApplication>
#include "mainwindow.h"

int main(int argc, char* argv[]) {
  QApplication app(argc, argv);

  MainWindow window;
  window.resize(1024, 768);
  window.show();

  return app.exec();
}
