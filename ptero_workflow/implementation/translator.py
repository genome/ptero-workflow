def build_petri_net(workflow):
    data = {
        'entry_places': [workflow.start_place_name],
        'transitions': [],
    }

    for operation in workflow.root_operation.children.itervalues():
        transitions = operation.get_petri_transitions()
        data['transitions'].extend(transitions)

    return data
