#!/bin/sh

cd ./tests

qmake
bear make -j$(nproc)
./build/tests
