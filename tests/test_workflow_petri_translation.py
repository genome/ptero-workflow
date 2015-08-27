import os
import unittest
import tests.util
from ptero_workflow.implementation.factory import Factory
from ptero_workflow.implementation import translator


class TestWorkflowPetriTranslation(unittest.TestCase):

    @property
    def workflow_data(self):
        pass

    @property
    def petri_data(self):
        factory = Factory(os.environ.get('PTERO_WORKFLOW_DB_STRING', 'sqlite://'))
        self.backend = factory.create_backend()
        workflow = self.backend._save_workflow(self.workflow_data)
        return translator.build_petri_net(workflow)

    @property
    def expire_actions(self):
        return [ i for i in self.petri_data['transitions']
            if i.get('action') and i['action']['type'] == 'expire' ]

    @property
    def workflow_data(self):
        return {
            'tasks': {
                'A': {
                    'methods': [
                        {
                            'name': 'execute',
                            'service': 'job',
                            'serviceUrl': tests.util.shell_command_url(),
                            'parameters': {
                                'commandLine': ['./echo_command'],
                                'user': 'dummy-user',
                                'workingDirectory': '/tmp',
                                'environment': {}
                            }
                        }
                    ]
                }
            },

            'links': [
                {
                    'source': 'input connector',
                    'destination': 'A',
                    'dataFlow': {
                        'in_a': 'param',
                    },
                },
                {
                    'source': 'A',
                    'destination': 'output connector',
                    'dataFlow': {
                        'param': 'out_a',
                    },
                }
            ],

            'inputs': {
                'in_a': 'kittens'
            }
        }

    def set_expire(self, type, ttl):
        os.environ['PTERO_WORKFLOW_%s_EXPIRE_SECONDS' % type] = str(ttl)

    def unset_expire(self, type):
        if os.environ.get('PTERO_WORKFLOW_%s_EXPIRE_SECONDS' % type):
            del os.environ['PTERO_WORKFLOW_%s_EXPIRE_SECONDS' % type]

    def test_has_no_expire_actions(self):
        self.unset_expire('SUCCEEDED')
        self.unset_expire('FAILED')
        self.assertTrue( len(self.expire_actions) == 0 )

    def test_success_expire_actions(self):
        self.set_expire('SUCCEEDED', 1)
        self.unset_expire('FAILED')
        self.assertTrue( len(self.expire_actions) == 1 )

    def test_failure_expire_actions(self):
        self.set_expire('FAILED', 1)
        self.unset_expire('SUCCEEDED')
        self.assertTrue( len(self.expire_actions) == 1 )

    def test_success_and_failure_expire_actions(self):
        self.set_expire('SUCCEEDED', 1)
        self.set_expire('FAILED', 1)
        self.assertTrue( len(self.expire_actions) == 2 )

if __name__ == '__main__':
    unittest.main()
