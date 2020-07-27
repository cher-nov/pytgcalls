#!/usr/bin/env python3

import sys
import os
import glob
import time
import stat
import shutil

sys.dont_write_bytecode = True  # prevent __pycache__ on importing 'setup'
sys.path.insert(0, os.path.realpath(__file__))  # ensure to import './setup.py'
from setup import (
    PACKAGE_NAME, PACKAGE_VERSION, ENVVAR_VERSION_SUFFIX, execute_py
)

def purge(skip_errors, *extra_folders):
    # shutil.rmtree fails on read-only files in Windows
    # https://bugs.python.org/issue19643
    def remove_readonly(func, path, *_):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    package_wildcard = "{}-{}*/".format(PACKAGE_NAME, PACKAGE_VERSION)
    for folder in ("build", "dist", PACKAGE_NAME+".egg-info", *extra_folders,
            *glob.glob(package_wildcard)):
        try:
            shutil.rmtree(folder,
                          onerror=remove_readonly,
                          ignore_errors=skip_errors)
        except FileNotFoundError:
            pass

def main(argv):
    if "testpip" in argv:
        execute_py(
            "pip", "install",
            "-v", "-v", "-v",  # v-v-verbose!
            "--pre", "--force-reinstall", "--no-cache-dir",
            "--index-url", "https://test.pypi.org/simple/",
            "--extra-index-url", "https://pypi.org/simple",
            "{}=={}.*".format(PACKAGE_NAME, PACKAGE_VERSION),
            module=True
        )
        return

    purge(False)
    if "testpypi" in argv:
        # https://test.pypi.org/help/#file-name-reuse
        # https://www.python.org/dev/peps/pep-0440/#developmental-releases
        os.environ[ENVVAR_VERSION_SUFFIX] =  "dev{}".format(int(time.time()))
        os.environ["TWINE_REPOSITORY_URL"] = "https://test.pypi.org/legacy/"

    try:
        execute_py("setup.py", "sdist")
        #execute_py("setup.py", "bdist_wheel")
        execute_py("twine", "upload", "dist/*", module=True)
    finally:
        purge(True)


if __name__ == '__main__':
    main(sys.argv)
