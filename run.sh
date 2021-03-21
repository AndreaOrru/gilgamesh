#!/bin/sh

qmake || exit 1
bear -- make -j$(nproc) || exit 1
./build/gilgamesh
