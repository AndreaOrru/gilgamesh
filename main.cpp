#include <QApplication>
#include <QWidget>

int main(int argc, char* argv[])
{
    QApplication app(argc, argv);

    QWidget window;
    window.resize(300, 300);
    window.setWindowTitle("Gilgamesh");
    window.show();

    return app.exec();
}
