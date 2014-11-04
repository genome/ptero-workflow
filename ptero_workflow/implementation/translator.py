def build_petri_net(workflow):
    data = {
        'initialMarking': [workflow.start_place_name],
        'transitions': workflow.get_petri_transitions(),
    }

    return data
