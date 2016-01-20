from . import models
from .models.execution.execution_base import Execution
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from ptero_workflow.implementation import exceptions
from ptero_workflow.implementation.model_builder import ModelBuilder
from ptero_common import nicer_logging
from ptero_common.server_info import get_server_info
from ptero_workflow.urls import petri_url_for
import re
from ptero_common.statuses import (scheduled, errored)
import uuid

LOG = nicer_logging.getLogger(__name__)


_TASK_BASE = 'ptero_workflow.implementation.celery_tasks.'


class Backend(object):
    def __init__(self, session, celery_app, db_revision):
        self.session = session
        self.celery_app = celery_app
        self.db_revision = db_revision

    @property
    def submit_net_task(self):
        return self.celery_app.tasks[_TASK_BASE + 'submit_net.SubmitNet']

    @property
    def http_with_result_task(self):
        return self.celery_app.tasks['ptero_common.celery.http.HTTPWithResult']

    @property
    def http_task(self):
        return self.celery_app.tasks['ptero_common.celery.http.HTTP']

    def create_spawned_workflow(self, workflow_data, parent_execution_id):
        workflow = self._create_workflow(workflow_data)
        parent_execution = self._get_execution(parent_execution_id)

        workflow.parent_execution = parent_execution

        self.session.commit()

        return workflow.id, workflow.as_dict(detailed=False)

    def create_workflow(self, workflow_data):
        workflow = self._create_workflow(workflow_data)
        return workflow.id, workflow.as_dict(detailed=False)

    def _create_workflow(self, workflow_data):
        try:
            workflow = self._save_workflow(workflow_data)
        except IntegrityError as e:
            postgres_error = re.search(
                    "Key.*%s.*already exists" % workflow_data['name'],
                    e.orig.message) is not None
            if postgres_error:
                raise exceptions.NonUniqueNameError(
                    "Workflow with name '%s' already exists" % workflow_data['name'])
            else:
                raise exceptions.UnknownIntegrityError('Unknown IntegrityError: %s' % e.message)

        LOG.info('Submitting Celery SubmitNet task for workflow "%s"',
                workflow.name, extra={'workflowName':workflow.name})
        self.submit_net_task.delay(workflow.name)
        return workflow

    def submit_net(self, workflow_name):
        workflow = self._get_workflow_by_name(workflow_name)
        petri_data = workflow.build_petri_net()

        LOG.info('Submitting petri net <%s> for'
                ' workflow "%s"', workflow.net_key, workflow.name,
                extra={'workflowName':workflow.name})
        self.http_task.delay('PUT', self._petri_submit_url(workflow.net_key), **petri_data)

    def _petri_submit_url(self, net_key):
        return petri_url_for('net-detail', net_key=net_key)

    def _save_workflow(self, workflow_data):
        builder = ModelBuilder(workflow_data)

        workflow = builder.build_workflow()
        self.session.add(workflow)
        self.session.commit()

        workflow.root_task.create_input_sources(self.session, [])

        self.session.commit()

        return workflow

    def _get_workflow_eagerly(self, workflow_id):
        workflow = self._get_workflow(workflow_id)

        # Here we load entities and eagerly-load some of their properties.
        # Later, when those entities are iterated through we won't have to issue
        # SQL per-entity.
        m = models
        method_lists = self.session.query(m.MethodList).\
                options(
                        joinedload(m.MethodList.method_list),
                        joinedload(m.MethodList.webhooks),
                ).filter_by(workflow_id=workflow_id).all()

        dags = self.session.query(m.DAG).\
                options(
                        joinedload(m.DAG.children),
                        joinedload(m.DAG.webhooks),
                ).filter_by(workflow_id=workflow_id).all()

        jobs = self.session.query(m.Job).\
                options(joinedload(m.Job.webhooks)).\
                filter_by(workflow_id=workflow_id).all()


        return workflow

    def _get_workflow(self, workflow_id):
        workflow = self.session.query(models.Workflow).get(workflow_id)
        if workflow is not None:
            return workflow
        else:
            raise exceptions.NoSuchEntityError(
                    "Workflow with id %s was not found." % workflow_id)

    def get_workflow(self, workflow_id):
        workflow = self._get_workflow(workflow_id)
        return {
                'name': workflow.name,
                'status': workflow.status,
        }

    def get_workflow_submission_data(self, workflow_id):
        return self._get_workflow_eagerly(workflow_id).as_dict(detailed=False)

    def get_workflow_by_name(self, workflow_name):
        workflow = self._get_workflow_by_name(workflow_name)
        return workflow.id, {
                'name': workflow.name,
                'status': workflow.status,
        }

    def _get_workflow_by_name(self, workflow_name):
        try:
            workflow = self.session.query(models.Workflow).filter_by(
                name=workflow_name).one()
            return workflow
        except NoResultFound:
            raise exceptions.NoSuchEntityError(
                    "Workflow with name %s was not found." % workflow_name)


    def cancel_workflow(self, workflow_id):
        self._get_workflow_eagerly(workflow_id).cancel()
        self.session.commit()

    def get_workflow_status(self, workflow_id):
        return self._get_workflow(workflow_id).status

    def get_workflow_details(self, workflow_id):
        m = models
        method_lists = self.session.query(m.MethodList).\
                options(joinedload(m.MethodList.executions)).\
                filter_by(workflow_id=workflow_id).all()

        dags = self.session.query(m.DAG).\
                options(joinedload(m.DAG.executions)).\
                filter_by(workflow_id=workflow_id).all()

        jobs = self.session.query(m.Job).\
                options(joinedload(m.Job.executions)).\
                filter_by(workflow_id=workflow_id).all()
        return self._get_workflow_eagerly(workflow_id).as_dict(detailed=True)

    def get_workflow_skeleton(self, workflow_id):
        workflow = self._get_workflow(workflow_id)

        # Here we load entities and eagerly-load some of their properties.
        # Later, when those entities are iterated through we won't have to issue
        # SQL per-entity.
        m = models
        method_lists = self.session.query(m.MethodList).\
                options(
                        joinedload(m.MethodList.method_list),
                ).filter_by(workflow_id=workflow_id).all()

        dags = self.session.query(m.DAG).\
                options(
                        joinedload(m.DAG.children),
                ).filter_by(workflow_id=workflow_id).all()

        return workflow.as_skeleton_dict()

    def get_workflow_outputs(self, workflow_id):
        return self._get_workflow(workflow_id).get_outputs()

    def get_workflow_executions(self, workflow_id, since=None):
        query = self.session.query(models.Execution)

        if since is not None:
            query = query.join(models.ExecutionStatusHistory).\
                    filter(models.Execution.workflow_id == workflow_id,
                            models.ExecutionStatusHistory.timestamp > since)
        else:
            query = query.filter(models.Execution.workflow_id == workflow_id)

        executions = query.all()

        if executions:
            timestamp = max([e.update_timestamp for e in executions])
            return [e.as_dict_for_executions_report() for e in executions], timestamp
        else:
            return [], None

    def _get_execution(self, execution_id):
        execution = self.session.query(Execution).get(execution_id)
        if execution is not None:
            return execution
        else:
            raise exceptions.NoSuchEntityError(
                    "Execution with id %s was not found." % execution_id)

    def get_execution(self, execution_id):
        return self._get_execution(execution_id).as_dict(detailed=False)

    def update_execution(self, execution_id, update_data):
        execution = self._get_execution(execution_id)

        try:
            LOG.info('Updating execution (%s) in workflow "%s"',
                    execution_id, execution.workflow.name,
                    extra={'workflowName':execution.workflow.name})
            execution.update(update_data)
        except exceptions.UpdateError:
            # We log here because we have access to workflow.name here
            LOG.exception('Exception while updating execution (%s) '
                    'in workflow "%s"', execution_id,
                    execution.workflow.name,
                    extra={'workflowName':execution.workflow.name})
            raise

        self.session.commit()
        return execution.as_dict(detailed=False)

    def handle_task_callback(self, task_id, callback_type, body_data,
            query_string_data):
        try:
            task = self.session.query(models.Task
                ).filter_by(id=task_id).one()
        except NoResultFound:
            raise exceptions.NoSuchEntityError(
                'Task with id (%s) not found '
                'while handling "%s" callback' % (task_id, callback_type))
        else:
            LOG.info('Got "%s" callback for task (%s:%s) in workflow "%s"',
                callback_type, task.name, task_id, task.workflow.name,
                extra={'workflowName':task.workflow.name})
            task.handle_callback(callback_type, body_data, query_string_data)

    def handle_method_callback(self, method_id, callback_type, body_data,
            query_string_data):
        try:
            method = self.session.query(models.Method
                ).filter_by(id=method_id).one()
        except NoResultFound:
            raise exceptions.NoSuchEntityError(
                'Method with id (%s) not found '
                'while handling "%s" callback' % (method_id, callback_type))
        else:
            LOG.info('Got "%s" callback for %s method (%s:%s) in workflow "%s"',
                callback_type, method.__class__.__name__, method.name,
                method_id, method.workflow.name,
                extra={'workflowName':method.workflow.name})
            method.handle_callback(callback_type, body_data, query_string_data)

    def server_info(self):
        result = get_server_info('ptero_workflow.implementation.celery_app')
        result['databaseRevision'] = self.db_revision
        return result

    def cleanup(self):
        self.session.rollback()

    def delete_workflow_by_name(self, name):
        workflow = self._get_workflow_by_name(name)
        self.delete_workflow(workflow.id)
        return workflow.id

    def delete_workflow(self, workflow_id):
        workflow = self._get_workflow(workflow_id)
        self._delete_workflow(workflow)

    def _delete_workflow(self, workflow):
        LOG.info("Deleting workflow with name (%s) and id (%s)",
                workflow.name, workflow.id,
                extra={'workflowName': workflow.name})
        self.session.delete(workflow)
        self.session.commit()

    def get_workflow_summary(self, workflow_id):
        m = models
        method_lists = self.session.query(m.MethodList).\
                options(
                        joinedload(m.MethodList.method_list),
                ).filter_by(workflow_id=workflow_id).all()

        dags = self.session.query(m.DAG).\
                filter_by(workflow_id=workflow_id).all()

        jobs = self.session.query(m.Job).\
                filter_by(workflow_id=workflow_id).all()

        return self._get_workflow(workflow_id).as_dict_for_summary()

    def submit_job(self, execution_id):
        execution = self._get_execution(execution_id)

        job_id = str(uuid.uuid4())
        execution.data['jobId'] = job_id
        self.session.commit()

        job_url = execution.method.get_job_submit_url(job_id)
        LOG.info('Submitting Job for execution "%s" of workflow '
                '"%s" -- %s', execution.name, execution.workflow.name,
                job_url, extra={'workflowName': execution.workflow.name})

        submit_data = execution.method.get_job_submit_data(execution.id)
        result = self.http_with_result_task.delay('PUT', job_url, **submit_data)

        response_info = result.wait()
        if 'json' in response_info:
            execution.status = scheduled
            url_from_header = response_info['headers']['location']
            execution.data['jobUrl'] = url_from_header
        else:
            error_message = 'Failed to submit job to service. ' +\
                    'Execution id: %s'
            LOG.error(error_message, execution.id,
                    extra={'workflowName': execution.workflow.name})
            execution.status = errored
            execution.data['error_message'] = error_message

            response_url = execution.data[
                    'petri_response_links_for_job']['failure']
            LOG.info('Notifying petri: execution "%s" failed for'
                    ' workflow "%s"', execution.name, execution.workflow.name,
                    extra={'workflowName': execution.workflow.name})
            self.http.delay('PUT', response_url)
        self.session.commit()
