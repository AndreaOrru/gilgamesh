#!/bin/sh

cd ./tests || exit 1

qmake || exit 1
bear -- make -j$(nproc) || exit 1
./build/tests
