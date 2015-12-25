from collections import defaultdict
from ptero_common import nicer_logging
from ptero_workflow.implementation import exceptions
from pprint import pformat

LOG = nicer_logging.getLogger(__name__)


def unique_links(links):
    link_counts = defaultdict(lambda:0)
    for link in links:
        key = str({
            'source': link['source'],
            'destination': link['destination']
            })
        link_counts[key] += 1

    violations = []
    for link_key, count in link_counts.iteritems():
        if count > 1:
            violations.append(link_key)

    if violations:
        raise exceptions.NonUniqueLinkError(
                "Found non-uniq link entries for: %s" % str(violations))


ILLEGAL_TASK_NAMES = set(['input connector', 'output connector'])


def dag_task_names(task_names):
    violations = ILLEGAL_TASK_NAMES.intersection(set(task_names))
    if violations:
        raise exceptions.IllegalTaskNameError('illegal task name(s): %s'
                % pformat(sorted(violations)))


def required_inputs(workflow_data):
    required_inputs = set()
    for link in workflow_data['links']:
        if link['source'] == 'input connector':
            required_inputs.update(link.get('dataFlow', {}).keys())

    supplied_inputs = set(workflow_data['inputs'].keys())
    missing_inputs = required_inputs - supplied_inputs
    if missing_inputs:
        raise exceptions.MissingInputsError("Missing required inputs: %s" %
                ', '.join(sorted(missing_inputs)))
