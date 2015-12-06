"""cascade_deletes

Revision ID: 4f5b26bea9d
Revises: 1f093e84c2b5
Create Date: 2015-12-06 08:22:06.090988

"""

# revision identifiers, used by Alembic.
revision = '4f5b26bea9d'
down_revision = '1f093e84c2b5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint(op.f('fk_block_id_method'), 'block')
    op.drop_constraint(op.f('fk_converge_id_method'), 'converge')
    op.drop_constraint(op.f('fk_dag_id_method'), 'dag')
    op.drop_constraint(op.f('fk_data_flow_entry_link_id_link'), 'data_flow_entry')
    op.drop_constraint(op.f('fk_execution_method_id_method'), 'execution')
    op.drop_constraint(op.f('fk_execution_task_id_task'), 'execution')
    op.drop_constraint(op.f('fk_execution_workflow_id_workflow'), 'execution')

    op.drop_constraint(op.f('fk_execution_status_history_execution_id_execution'), 'execution_status_history')
    op.drop_constraint(op.f('fk_input_connector_id_task'), 'input_connector')
    op.drop_constraint(op.f('fk_input_holder_id_task'), 'input_holder')
    op.drop_constraint(op.f('fk_input_source_destination_id_task'), 'input_source')
    op.drop_constraint(op.f('fk_input_source_source_id_task'), 'input_source')
    op.drop_constraint(op.f('fk_input_source_workflow_id_workflow'), 'input_source')
    op.drop_constraint(op.f('fk_link_destination_id_task'), 'link')
    op.drop_constraint(op.f('fk_link_source_id_task'), 'link')
    op.drop_constraint(op.f('fk_method_task_id_task'), 'method')
    op.drop_constraint(op.f('fk_method_workflow_id_workflow'), 'method')
    op.drop_constraint(op.f('fk_method_list_id_task'), 'method_list')
    op.drop_constraint(op.f('fk_output_connector_id_task'), 'output_connector')
    op.drop_constraint(op.f('fk_result_task_id_task'), 'result')
    op.drop_constraint(op.f('fk_job_id_method'), 'job')
    op.drop_constraint(op.f('fk_task_workflow_id_workflow'), 'task')
    op.drop_constraint(op.f('fk_webhook_method_id_method'), 'webhook')
    op.drop_constraint(op.f('fk_webhook_task_id_task'), 'webhook')
    op.drop_constraint(op.f('fk_workflow_parent_execution_id_execution'), 'workflow')

    op.drop_constraint(op.f('fk_task_parent_id_dag'), 'task')
    op.drop_constraint(op.f('fk_workflow_root_task_id_task'), 'workflow')


    op.create_foreign_key(op.f('fk_block_id_method'), 'block', 'method', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_converge_id_method'), 'converge', 'method', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_dag_id_method'), 'dag', 'method', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_data_flow_entry_link_id_link'), 'data_flow_entry', 'link', ['link_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_execution_method_id_method'), 'execution', 'method', ['method_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_execution_task_id_task'), 'execution', 'task', ['task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_execution_workflow_id_workflow'), 'execution', 'workflow', ['workflow_id'], ['id'], ondelete='CASCADE')

    op.create_foreign_key(op.f('fk_execution_status_history_execution_id_execution'), 'execution_status_history', 'execution', ['execution_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_input_connector_id_task'), 'input_connector', 'task', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_input_holder_id_task'), 'input_holder', 'task', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_input_source_destination_id_task'), 'input_source', 'task', ['destination_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_input_source_source_id_task'), 'input_source', 'task', ['source_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_input_source_workflow_id_workflow'), 'input_source', 'workflow', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_link_destination_id_task'), 'link', 'task', ['destination_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_link_source_id_task'), 'link', 'task', ['source_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_method_task_id_task'), 'method', 'task', ['task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_method_workflow_id_workflow'), 'method', 'workflow', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_method_list_id_task'), 'method_list', 'task', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_output_connector_id_task'), 'output_connector', 'task', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_result_task_id_task'), 'result', 'task', ['task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_job_id_method'), 'job', 'method', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_task_workflow_id_workflow'), 'task', 'workflow', ['workflow_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_webhook_method_id_method'), 'webhook', 'method', ['method_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_webhook_task_id_task'), 'webhook', 'task', ['task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_workflow_parent_execution_id_execution'), 'workflow', 'execution', ['parent_execution_id'], ['id'], ondelete='CASCADE')

    op.create_foreign_key(op.f('fk_task_parent_id_dag'), 'task', 'dag', ['parent_id'], ['id'], use_alter=True, ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_workflow_root_task_id_task'), 'workflow', 'task', ['root_task_id'], ['id'], use_alter=True, ondelete='CASCADE')


def downgrade():
    op.drop_constraint(op.f('fk_block_id_method'), 'block')
    op.drop_constraint(op.f('fk_converge_id_method'), 'converge')
    op.drop_constraint(op.f('fk_dag_id_method'), 'dag')
    op.drop_constraint(op.f('fk_data_flow_entry_link_id_link'), 'data_flow_entry')
    op.drop_constraint(op.f('fk_execution_method_id_method'), 'execution')
    op.drop_constraint(op.f('fk_execution_task_id_task'), 'execution')
    op.drop_constraint(op.f('fk_execution_workflow_id_workflow'), 'execution')

    op.drop_constraint(op.f('fk_execution_status_history_execution_id_execution'), 'execution_status_history')
    op.drop_constraint(op.f('fk_input_connector_id_task'), 'input_connector')
    op.drop_constraint(op.f('fk_input_holder_id_task'), 'input_holder')
    op.drop_constraint(op.f('fk_input_source_destination_id_task'), 'input_source')
    op.drop_constraint(op.f('fk_input_source_source_id_task'), 'input_source')
    op.drop_constraint(op.f('fk_input_source_workflow_id_workflow'), 'input_source')
    op.drop_constraint(op.f('fk_link_destination_id_task'), 'link')
    op.drop_constraint(op.f('fk_link_source_id_task'), 'link')
    op.drop_constraint(op.f('fk_method_task_id_task'), 'method')
    op.drop_constraint(op.f('fk_method_workflow_id_workflow'), 'method')
    op.drop_constraint(op.f('fk_method_list_id_task'), 'method_list')
    op.drop_constraint(op.f('fk_output_connector_id_task'), 'output_connector')
    op.drop_constraint(op.f('fk_result_task_id_task'), 'result')
    op.drop_constraint(op.f('fk_job_id_method'), 'job')
    op.drop_constraint(op.f('fk_task_workflow_id_workflow'), 'task')
    op.drop_constraint(op.f('fk_webhook_method_id_method'), 'webhook')
    op.drop_constraint(op.f('fk_webhook_task_id_task'), 'webhook')
    op.drop_constraint(op.f('fk_workflow_parent_execution_id_execution'), 'workflow')

    op.drop_constraint(op.f('fk_task_parent_id_dag'), 'task')
    op.drop_constraint(op.f('fk_workflow_root_task_id_task'), 'workflow')


    op.create_foreign_key(op.f('fk_block_id_method'), 'block', 'method', ['id'], ['id'])
    op.create_foreign_key(op.f('fk_converge_id_method'), 'converge', 'method', ['id'], ['id'])
    op.create_foreign_key(op.f('fk_dag_id_method'), 'dag', 'method', ['id'], ['id'])
    op.create_foreign_key(op.f('fk_data_flow_entry_link_id_link'), 'data_flow_entry', 'link', ['link_id'], ['id'])
    op.create_foreign_key(op.f('fk_execution_method_id_method'), 'execution', 'method', ['method_id'], ['id']),
    op.create_foreign_key(op.f('fk_execution_task_id_task'), 'execution', 'task', ['task_id'], ['id']),
    op.create_foreign_key(op.f('fk_execution_workflow_id_workflow'), 'execution', 'workflow', ['workflow_id'], ['id']),

    op.create_foreign_key(op.f('fk_execution_status_history_execution_id_execution'), 'execution_status_history', 'execution', ['execution_id'], ['id']),
    op.create_foreign_key(op.f('fk_input_connector_id_task'), 'input_connector', 'task', ['id'], ['id']),
    op.create_foreign_key(op.f('fk_input_holder_id_task'), 'input_holder', 'task', ['id'], ['id']),
    op.create_foreign_key(op.f('fk_input_source_destination_id_task'), 'input_source', 'task', ['destination_id'], ['id']),
    op.create_foreign_key(op.f('fk_input_source_source_id_task'), 'input_source', 'task', ['source_id'], ['id']),
    op.create_foreign_key(op.f('fk_input_source_workflow_id_workflow'), 'input_source', 'workflow', ['workflow_id'], ['id']),
    op.create_foreign_key(op.f('fk_link_destination_id_task'), 'link', 'task', ['destination_id'], ['id']),
    op.create_foreign_key(op.f('fk_link_source_id_task'), 'link', 'task', ['source_id'], ['id']),
    op.create_foreign_key(op.f('fk_method_task_id_task'), 'method', 'task', ['task_id'], ['id']),
    op.create_foreign_key(op.f('fk_method_workflow_id_workflow'), 'method', 'workflow', ['workflow_id'], ['id']),
    op.create_foreign_key(op.f('fk_method_list_id_task'), 'method_list', 'task', ['id'], ['id']),
    op.create_foreign_key(op.f('fk_output_connector_id_task'), 'output_connector', 'task', ['id'], ['id']),
    op.create_foreign_key(op.f('fk_result_task_id_task'), 'result', 'task', ['task_id'], ['id']),
    op.create_foreign_key(op.f('fk_job_id_method'), 'job', 'method', ['id'], ['id']),
    op.create_foreign_key(op.f('fk_task_workflow_id_workflow'), 'task', 'workflow', ['workflow_id'], ['id']),
    op.create_foreign_key(op.f('fk_webhook_method_id_method'), 'webhook', 'method', ['method_id'], ['id']),
    op.create_foreign_key(op.f('fk_webhook_task_id_task'), 'webhook', 'task', ['task_id'], ['id'])
    op.create_foreign_key(op.f('fk_workflow_parent_execution_id_execution'), 'workflow', 'execution', ['parent_execution_id'], ['id'])

    op.create_foreign_key(op.f('fk_task_parent_id_dag'), 'task', 'dag', ['parent_id'], ['id'], use_alter=True)
    op.create_foreign_key(op.f('fk_workflow_root_task_id_task'), 'workflow', 'task', ['root_task_id'], ['id'], use_alter=True)
