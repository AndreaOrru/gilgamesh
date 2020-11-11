#!/bin/sh

qmake
bear make -j$(nproc)
./build/gilgamesh
