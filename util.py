"""
Utilities for file management
"""

import os
import errno


def ensure_dir(target_dir):
    """Ensure a directory exists"""
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise


class pushdir(object):
    """Change directories for the duration of a with statement."""
    def __init__(self, path):
        self.path = os.path.abspath(path)

    def __enter__(self):
        self._cwd = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, *args):
        os.chdir(self._cwd)
