from . import generator
import os
import sys
import unittest


MODULE = sys.modules[__name__]


def base_dir():
    return os.path.dirname(os.path.abspath(__file__))


generator.create_test_cases(target_module=MODULE,
        test_case_directory=os.path.join(base_dir(),'system_tests'))


if __name__ == '__main__':
    unittest.main()
