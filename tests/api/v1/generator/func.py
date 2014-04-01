from .base_case import TestCaseMixin
import os
import socket
import unittest


_TEST_DIR_BLACKLIST = [
    'README.md',
]


def create_test_cases(target_module, test_case_directory):
    for test_case_name in os.listdir(test_case_directory):
        if test_case_name in _TEST_DIR_BLACKLIST:
            continue
        _create_and_attach_test_case(target_module, test_case_directory,
                test_case_name)


def _create_and_attach_test_case(target_module, test_case_directory,
        test_case_name):
    tc = _create_test_case(test_case_directory, test_case_name)
    _attach_test_case(target_module, tc)


def _create_test_case(test_case_directory, test_case_name):
    class_dict = {
        'api_port': _get_available_port(),
        'callback_port': _get_available_port(),
        'directory': os.path.join(test_case_directory, test_case_name),
        'test_name': test_case_name,
    }
    return type(test_case_name, (TestCaseMixin, unittest.TestCase),
            class_dict)


def _attach_test_case(target_module, test_case):
    setattr(target_module, test_case.__name__, test_case)


def _get_available_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()

    return port
