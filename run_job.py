
import os
import pylauncher

test_path = os.path.join(os.getcwd(), 'pylauncher/examples/commandlines')
pylauncher.ClassicLauncher(test_path, debug="job")

