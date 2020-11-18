TARGET = tests
INCLUDEPATH += ../src

DESTDIR = build
OBJECTS_DIR = build

CONFIG += c++17 debug
QT = core

SOURCES += asar.cpp main.cpp
SOURCES += ../src/utils.cpp

SOURCES += ../src/instruction.cpp
SOURCES += ../src/rom.cpp test_rom.cpp
SOURCES += ../src/stack.cpp test_stack.cpp
SOURCES += ../src/subroutine.cpp test_subroutine.cpp
SOURCES += ../src/state.cpp
