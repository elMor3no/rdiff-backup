#!/usr/bin/env python3

import sys
import os
from distutils.core import setup, Extension

assert len(sys.argv) == 1
sys.argv.append("build")

setup(
    name="CModule",
    version="0.9.0",
    description="rdiff-backup's C component",
    ext_modules=[
        Extension("C", ["cmodule.c"]),
        Extension("_librsync", ["_librsyncmodule.c"], libraries=["rsync"])
    ])


def get_libraries():

for filename in get_libraries():
    assert not os.system("mv '%s' ." % (filename, ))
assert not os.system("rm -rf build")
