TARGET = tests
INCLUDEPATH += ../src

DESTDIR = build
OBJECTS_DIR = build

CONFIG += c++17 debug
QT = core

SOURCES += asar.cpp main.cpp
SOURCES += ../src/utils.cpp

SOURCES += ../src/analysis.cpp test_analysis.cpp
SOURCES += ../src/cpu.cpp test_cpu.cpp
SOURCES += ../src/instruction.cpp test_instruction.cpp
SOURCES += ../src/rom.cpp test_rom.cpp
SOURCES += ../src/stack.cpp test_stack.cpp
SOURCES += ../src/subroutine.cpp test_subroutine.cpp
SOURCES += ../src/state.cpp test_state.cpp
