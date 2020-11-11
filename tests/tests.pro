TARGET = tests
INCLUDEPATH += ../src

DESTDIR = build
OBJECTS_DIR = build

CONFIG += c++17 debug
QT =

SOURCES += ../src/rom.cpp ../src/utils.cpp
SOURCES += asar.cpp main.cpp test_rom.cpp
