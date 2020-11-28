TARGET = tests
INCLUDEPATH += ../src

DESTDIR = build
OBJECTS_DIR = build

CONFIG += c++17 debug

QT = core
LIBS += -lboost_serialization

SOURCES += $$files(*.cpp, true)
SOURCES += $$files(../src/*.cpp, false)
