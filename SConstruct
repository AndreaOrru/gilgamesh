from os import environ

VariantDir('build/source', 'source', duplicate=0)
VariantDir('build/tests', 'tests', duplicate=0)

env = Environment(
    ENV=environ,
    CXX='clang++',
    CXXFLAGS=['-g', '-std=c++17', '-Wall'],
    CPPPATH=['#include'],
    LIBS=['fmt'],
)

source_files = Glob('build/source/*.cpp')
test_files = Glob('build/tests/*.cpp') + [
    f for f in source_files if f.name != 'main.cpp'
]

env.Program('gilgamesh', source_files)
env.Program('test_gilgamesh', test_files)
