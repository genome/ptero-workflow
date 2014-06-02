class OperationPetriMixin(object):
    @property
    def response_wait_place_name(self):
        return '%s-response-wait' % self.unique_name

    @property
    def response_callback_place_name(self):
        return '%s-response-callback' % self.unique_name

    def get_petri_transitions(self):
        transitions = []

        input_deps_place = self._attach_input_deps(transitions)

        split_place = self._attach_split(transitions, input_deps_place)
        action_place = self._attach_action(transitions, split_place)
        join_place = self._attach_join(transitions, action_place)

        self._attach_output_deps(transitions, join_place)

        return transitions

    def _attach_input_deps(self, transitions):
        transitions.append({
            'inputs': [o.success_place_pair_name(self) for o in self.input_ops],
            'outputs': [self.ready_place_name],
        })

        return self.ready_place_name

    def _attach_output_deps(self, transitions, internal_success_place):
        success_outputs = [self.success_place_pair_name(o) for o in self.output_ops]
        success_outputs.append(self.success_place_pair_name(self.parent))
        transitions.append({
            'inputs': [internal_success_place],
            'outputs': success_outputs,
        })

    def _attach_split(self, transitions, ready_place):
        return ready_place

    def _attach_join(self, transitions, action_done_place):
        return action_done_place

    def _attach_action(self, transitions, action_ready_place):
        # send notification
        transitions.append({
            'inputs': [action_ready_place],
            'outputs': [self.response_wait_place_name],
            'action': {
                'type': 'notify',
                'url': self.event_url('execute'),
                'response_places': {
                    'success': self.response_callback_place_name,
                },
            }
        })

        # wait for response
        transitions.append({
            'inputs': [self.response_wait_place_name,
                self.response_callback_place_name],
            'outputs': [self.success_place_name],
        })

        return self.success_place_name
