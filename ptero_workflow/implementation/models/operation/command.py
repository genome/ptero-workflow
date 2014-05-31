from ..job import Job, ResponseLink
from .operation_base import Operation
from .mixins.petri import OperationPetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm.session import object_session
import os
import requests
import simplejson


__all__ = ['CommandOperation', 'ParallelByCommandOperation']


class CommandOperation(OperationPetriMixin, Operation):
    __tablename__ = 'operation_command'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    serialized_command_line = Column(Text, nullable=False)

    @property
    def command_line(self):
        return simplejson.loads(self.serialized_command_line)

    @command_line.setter
    def command_line(self, new_value):
        self.serialized_command_line = simplejson.dumps(new_value)


    __mapper_args__ = {
        'polymorphic_identity': 'command',
    }

    def execute(self, color, group, response_links):
        job_id = self._submit_to_fork(color)

        job = Job(operation=self, color=color, job_id=job_id)
        s = object_session(self)
        for name, url in response_links.iteritems():
            s.add(ResponseLink(job=job, url=url, name=name))

        s.add(job)
        s.commit()

    def ended(self, job_id, **kwargs):
        s = object_session(self)
        job = s.query(Job).filter_by(operation=self, job_id=job_id).one()

        if kwargs['exit_code'] == 0:
            outputs = simplejson.loads(kwargs['stdout'])
            self.set_outputs(outputs, job.color)
            s.commit()
            response = requests.put(job.response_links['success'].url)

        else:
            LOG.error('job failed: %s', kwargs)
            raise RuntimeError('Job failed')


    def _submit_to_fork(self, color):
        body_data = self._fork_submit_data(color)
        response = requests.post(self._fork_submit_url,
                data=simplejson.dumps(body_data),
                headers={'Content-Type': 'application/json'})
        return response.json()['job_id']

    @property
    def _fork_submit_url(self):
        return 'http://%s:%d/v1/jobs' % (
            os.environ.get('PTERO_FORK_HOST', 'localhost'),
            int(os.environ.get('PTERO_FORK_PORT', 80)),
        )

    def _fork_submit_data(self, color):
        return {
            'command_line': self.command_line,
            'user': os.environ.get('USER'),
            'stdin': simplejson.dumps(self.get_inputs(color)),
            'callbacks': {
                'ended': self.event_url('ended'),
            },
        }


class ParallelByCommandOperation(ParallelPetriMixin, Operation):
    __tablename__ = 'operation_command_parallel'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'parallel-by-command',
    }
