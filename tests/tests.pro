TARGET = tests
INCLUDEPATH += ../src

DESTDIR = build
OBJECTS_DIR = build

CONFIG += c++17 debug
QT =

SOURCES += asar.cpp main.cpp
SOURCES += ../src/utils.cpp

SOURCES += ../src/rom.cpp test_rom.cpp
