"""bootstrapping

Revision ID: 177e0b42a8c3
Revises: 
Create Date: 2015-08-05 06:53:38.030974

"""

# revision identifiers, used by Alembic.
revision = '177e0b42a8c3'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import ptero_workflow

def upgrade():
    op.create_table('block',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('parameters', ptero_workflow.implementation.models.json_type.JSON, nullable=True),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_block'))
            )
    op.create_table('converge',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('parameters', ptero_workflow.implementation.models.json_type.JSON, nullable=True),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_converge'))
            )
    op.create_table('dag',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_dag'))
            )
    op.create_table('data_flow_entry',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('link_id', sa.Integer(), nullable=False),
            sa.Column('source_property', sa.Text(), nullable=False),
            sa.Column('destination_property', sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_data_flow_entry')),
            sa.UniqueConstraint('link_id', 'source_property', 'destination_property', name=op.f('uq_data_flow_entry_link_id'))
            )
    op.create_index(op.f('ix_data_flow_entry_link_id'), 'data_flow_entry', ['link_id'], unique=False)
    op.create_table('execution',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('color', sa.Integer(), nullable=False),
            sa.Column('parent_color', sa.Integer(), nullable=True),
            sa.Column('method_id', sa.Integer(), nullable=True),
            sa.Column('task_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.Text(), nullable=False),
            sa.Column('data', ptero_workflow.implementation.models.json_type.MutableJSONDict, nullable=False),
            sa.Column('colors', ptero_workflow.implementation.models.json_type.JSON, nullable=True),
            sa.Column('begins', ptero_workflow.implementation.models.json_type.JSON, nullable=True),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_execution')),
            sa.UniqueConstraint('method_id', 'color', name=op.f('uq_execution_method_id')),
            sa.UniqueConstraint('task_id', 'color', name=op.f('uq_execution_task_id'))
            )
    op.create_index(op.f('ix_execution_color'), 'execution', ['color'], unique=False)
    op.create_index(op.f('ix_execution_method_id'), 'execution', ['method_id'], unique=False)
    op.create_index(op.f('ix_execution_parent_color'), 'execution', ['parent_color'], unique=False)
    op.create_index(op.f('ix_execution_task_id'), 'execution', ['task_id'], unique=False)
    op.create_index(op.f('ix_execution_workflow_id'), 'execution', ['workflow_id'], unique=False)
    op.create_table('execution_status_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('execution_id', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_execution_status_history'))
            )
    op.create_index(op.f('ix_execution_status_history_status'), 'execution_status_history', ['status'], unique=False)
    op.create_table('input_connector',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_input_connector'))
            )
    op.create_table('input_holder',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_input_holder'))
            )
    op.create_table('input_source',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source_id', sa.Integer(), nullable=False),
            sa.Column('destination_id', sa.Integer(), nullable=False),
            sa.Column('source_property', sa.Text(), nullable=False),
            sa.Column('destination_property', sa.Text(), nullable=False),
            sa.Column('parallel_depths', ptero_workflow.implementation.models.json_type.JSON, nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_input_source')),
            sa.UniqueConstraint('destination_id', 'destination_property', name=op.f('uq_input_source_destination_id'))
            )
    op.create_index(op.f('ix_input_source_destination_id'), 'input_source', ['destination_id'], unique=False)
    op.create_index(op.f('ix_input_source_destination_property'), 'input_source', ['destination_property'], unique=False)
    op.create_index(op.f('ix_input_source_source_id'), 'input_source', ['source_id'], unique=False)
    op.create_index(op.f('ix_input_source_source_property'), 'input_source', ['source_property'], unique=False)
    op.create_index(op.f('ix_input_source_workflow_id'), 'input_source', ['workflow_id'], unique=False)
    op.create_table('link',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source_id', sa.Integer(), nullable=False),
            sa.Column('destination_id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_link')),
            sa.UniqueConstraint('source_id', 'destination_id', name=op.f('uq_link_source_id'))
            )
    op.create_index(op.f('ix_link_destination_id'), 'link', ['destination_id'], unique=False)
    op.create_index(op.f('ix_link_source_id'), 'link', ['source_id'], unique=False)
    op.create_table('method',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.Text(), nullable=True),
            sa.Column('index', sa.Integer(), nullable=True),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('type', sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_method')),
            sa.UniqueConstraint('task_id', 'name', name=op.f('uq_method_task_id'))
            )
    op.create_index(op.f('ix_method_index'), 'method', ['index'], unique=False)
    op.create_index(op.f('ix_method_task_id'), 'method', ['task_id'], unique=False)
    op.create_index(op.f('ix_method_type'), 'method', ['type'], unique=False)
    op.create_index(op.f('ix_method_workflow_id'), 'method', ['workflow_id'], unique=False)
    op.create_table('method_list',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_method_list'))
            )
    op.create_table('output_connector',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_output_connector'))
            )
    op.create_table('result',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('color', sa.Integer(), nullable=False),
            sa.Column('parent_color', sa.Integer(), nullable=True),
            sa.Column('data', ptero_workflow.implementation.models.json_type.JSON, nullable=True),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_result')),
            sa.UniqueConstraint('color', 'name', 'task_id', name=op.f('uq_result_color'))
            )
    op.create_index('color', 'result', ['name', 'task_id'], unique=False)
    op.create_index(op.f('ix_result_color'), 'result', ['color'], unique=False)
    op.create_index(op.f('ix_result_name'), 'result', ['name'], unique=False)
    op.create_index(op.f('ix_result_parent_color'), 'result', ['parent_color'], unique=False)
    op.create_index(op.f('ix_result_task_id'), 'result', ['task_id'], unique=False)
    op.create_table('shell_command',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('parameters', ptero_workflow.implementation.models.json_type.JSON, nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_shell_command'))
            )
    op.create_table('task',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('type', sa.Text(), nullable=False),
            sa.Column('is_canceled', sa.Boolean(), nullable=True),
            sa.Column('parallel_by', sa.Text(), nullable=True),
            sa.Column('topological_index', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['parent_id'], ['dag.id'], name=op.f('fk_task_parent_id_dag'), use_alter=True),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_task')),
            sa.UniqueConstraint('parent_id', 'name', name=op.f('uq_task_parent_id'))
            )
    op.create_index(op.f('ix_task_parent_id'), 'task', ['parent_id'], unique=False)
    op.create_index(op.f('ix_task_workflow_id'), 'task', ['workflow_id'], unique=False)
    op.create_table('webhook',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('method_id', sa.Integer(), nullable=True),
            sa.Column('task_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('url', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_webhook'))
            )
    op.create_index(op.f('ix_webhook_method_id'), 'webhook', ['method_id'], unique=False)
    op.create_index(op.f('ix_webhook_name'), 'webhook', ['name'], unique=False)
    op.create_index(op.f('ix_webhook_task_id'), 'webhook', ['task_id'], unique=False)
    op.create_index('method_id', 'webhook', ['name'], unique=False)
    op.create_index('task_id', 'webhook', ['name'], unique=False)
    op.create_table('workflow',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('net_key', sa.Text(), nullable=True),
            sa.Column('root_task_id', sa.Integer(), nullable=True),
            sa.Column('parent_execution_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['root_task_id'], ['task.id'], name=op.f('fk_workflow_root_task_id_task'), use_alter=True),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_workflow'))
            )
    op.create_index(op.f('ix_workflow_name'), 'workflow', ['name'], unique=True)
    op.create_index(op.f('ix_workflow_net_key'), 'workflow', ['net_key'], unique=True)
    op.create_index(op.f('ix_workflow_parent_execution_id'), 'workflow', ['parent_execution_id'], unique=False)

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
    op.create_foreign_key(op.f('fk_shell_command_id_method'), 'shell_command', 'method', ['id'], ['id']),
    op.create_foreign_key(op.f('fk_task_workflow_id_workflow'), 'task', 'workflow', ['workflow_id'], ['id']),
    op.create_foreign_key(op.f('fk_webhook_method_id_method'), 'webhook', 'method', ['method_id'], ['id']),
    op.create_foreign_key(op.f('fk_webhook_task_id_task'), 'webhook', 'task', ['task_id'], ['id'])
    op.create_foreign_key(op.f('fk_workflow_parent_execution_id_execution'), 'workflow', 'execution', ['parent_execution_id'], ['id'])

    op.create_foreign_key(op.f('fk_task_parent_id_dag'), 'task', 'dag', ['parent_id'], ['id'], use_alter=True)
    op.create_foreign_key(op.f('fk_workflow_root_task_id_task'), 'workflow', 'task', ['root_task_id'], ['id'], use_alter=True)




def downgrade():
    raise RuntimeError("Cannot downgrade to an empty database!")
