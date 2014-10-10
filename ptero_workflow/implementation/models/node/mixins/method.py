class MethodPetriMixin(object):
    def _attach(self, transitions, input_place_name):
        success_place_name = self.task._method_place_name(
                self.name, 'success')
        failure_place_name = self.task._method_place_name(
                self.name, 'failure')

        wait_place_name = self.task._method_place_name(
                self.name, 'wait')

        success_callback_place_name = self.task._method_place_name(
                self.name, 'success-callback')
        failure_callback_place_name = self.task._method_place_name(
                self.name, 'failure-callback')

        transitions.append({
            'inputs': [input_place_name],
            'outputs': [wait_place_name],
            'action': {
                'type': 'notify',
                'url': self.task.event_url('execute', method=self.name),
                'response_places': {
                    'success': success_callback_place_name,
                    'failure': failure_callback_place_name,
                },
            }
        })

        transitions.extend([
            {
                'inputs': [wait_place_name, success_callback_place_name],
                'outputs': [success_place_name],
            },
            {
                'inputs': [wait_place_name, failure_callback_place_name],
                'outputs': [failure_place_name],
            }
        ])

        return success_place_name, failure_place_name

