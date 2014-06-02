class OperationPetriMixin(object):
    def _method_place_name(self, method, kind):
        return '%s-%s-%s' % (self.unique_name, method, kind)

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
        input_place_name = action_ready_place
        success_places = []
        for method in self.method_list:
            success_place, failure_place = self._attach_method(transitions,
                    method, input_place_name)
            input_place_name = failure_place
            success_places.append(success_place)

        for sp in success_places:
            transitions.append({
                'inputs': [sp],
                'outputs': [self.success_place_name],
            })

        return self.success_place_name

    def _attach_method(self, transitions, method, input_place_name):
        success_place_name = self._method_place_name(
                method.name, 'success')
        failure_place_name = self._method_place_name(
                method.name, 'failure')

        wait_place_name = self._method_place_name(
                method.name, 'wait')

        success_callback_place_name = self._method_place_name(
                method.name, 'success-callback')
        failure_callback_place_name = self._method_place_name(
                method.name, 'failure-callback')

        transitions.append({
            'inputs': [input_place_name],
            'outputs': [wait_place_name],
            'action': {
                'type': 'notify',
                'url': self.event_url('execute', method=method.name),
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
