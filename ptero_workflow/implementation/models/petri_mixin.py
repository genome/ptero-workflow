class PetriMixin(object):
    def _pn(self, *args):
        raise NotImplementedError

    def callback_url(self, *args):
        raise NotImplementedError

    def attach_notify_and_wait_transitions(self, transitions, start_place,
            name):
        transitions.extend([
            {
                'inputs': [start_place],
                'outputs': [self._pn('wait', name)],
                'action': {
                    'type': 'notify',
                    'url': self.callback_url(name),
                    'response_places': {
                        'success': self._pn('done_waiting_success', name),
                        'failure': self._pn('done_waiting_failure', name),
                    },
                },
            },

            {
                'inputs': [self._pn('wait', name),
                    self._pn('done_waiting_success', name)],
                'outputs': [self._pn('success', name)],
            },

            {
                'inputs': [self._pn('wait', name),
                    self._pn('done_waiting_failure', name)],
                'outputs': [self._pn('failure', name)],
            },
        ])
        return self._pn('success', name), self._pn('failure', name)

