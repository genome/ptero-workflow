from collections import defaultdict
from .exceptions import NonUniqueLinkError
import logging

LOG = logging.getLogger(__name__)

def validate_unique_links(links):
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
        raise NonUniqueLinkError("Found non-uniq link entries for: %s" % str(violations))
