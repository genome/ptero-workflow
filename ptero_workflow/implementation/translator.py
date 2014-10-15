def build_petri_net(workflow):
    data = {
        'entry_places': [workflow.start_place_name],
        'transitions': workflow.root_task.get_petri_transitions(),
    }

    return data
