######################################################################
# Automatically generated by qmake (3.1) Wed Nov 11 00:57:58 2020
######################################################################

TEMPLATE = app
TARGET = gilgamesh
INCLUDEPATH += src

DESTDIR = build
OBJECTS_DIR = build
MOC_DIR = build

CONFIG += c++17 debug

# You can make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# Please consult the documentation of the deprecated API in order to know
# how to port your code away from it.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

QT += widgets

# Input
SOURCES += src/gui/disassemblyview.cpp src/gui/highlighter.cpp src/gui/labelsview.cpp src/gui/mainwindow.cpp
HEADERS += src/gui/disassemblyview.hpp src/gui/highlighter.hpp src/gui/labelsview.hpp src/gui/mainwindow.hpp

SOURCES += src/analysis.cpp src/cpu.cpp src/instruction.cpp src/main.cpp src/rom.cpp src/stack.cpp src/state.cpp src/subroutine.cpp src/utils.cpp
HEADERS += src/analysis.hpp src/cpu.hpp src/instruction.hpp src/opcodes.hpp src/rom.hpp src/stack.hpp src/state.hpp src/subroutine.hpp src/types.hpp src/utils.hpp
