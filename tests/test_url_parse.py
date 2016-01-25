import unittest
from ptero_workflow.urls import url_parse
from ptero_workflow.implementation.exceptions import UrlParseError


class TestUrlParse(unittest.TestCase):
    def test_execution_detail_url_parse(self):
        parsed_url = url_parse('execution-detail',
                'http://localhost:80/v1/executions/1234?param=value')
        self.assertEqual(len(parsed_url), 1)
        self.assertEqual(parsed_url['execution_id'], '1234')

    def test_raises_parse_error(self):
        self.assertRaises(UrlParseError, url_parse, 'execution-detail',
                'http://localhost:80/v1/executions')
