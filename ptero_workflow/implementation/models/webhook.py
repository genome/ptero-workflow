from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from collections import defaultdict
import logging

LOG = logging.getLogger(__name__)

__all__ = ['Webhook']

class Webhook(Base):
    __tablename__ = 'webhook'

    id = Column(Integer, primary_key=True)

    method_id = Column(Integer, ForeignKey('method.id'), nullable=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=True)

    task = relationship('Task', backref='webhooks')
    method = relationship('Method', backref='webhooks')

    name = Column(String, nullable=False)
    url = Column(String, nullable=False)


def get_sorted_webhook_dict(entity):
    unsorted_webhook_dict = defaultdict(set)
    for webhook in entity.webhooks:
        unsorted_webhook_dict[webhook.name].add(webhook.url)

    sorted_webhook_dict = {}
    for name, unsorted_urls in unsorted_webhook_dict.iteritems():
        if len(unsorted_urls) == 1:
            entry = unsorted_urls.pop()
        else:
            entry = sorted(unsorted_urls)
        sorted_webhook_dict[name] = entry
    return sorted_webhook_dict

def get_webhooks_for_task(task, name):
    raise NotImplementedError

def get_webhooks_for_method(method, name):
    raise NotImplementedError
