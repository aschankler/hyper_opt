"""
Starts the optimization
"""

import os
import sys

sys.path.append(os.getcwd())


def run():
    from .run_job import main
    main()


if __name__ == '__main__':
    run()
