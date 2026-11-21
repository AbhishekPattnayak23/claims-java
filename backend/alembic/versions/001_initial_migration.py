"""Initial migration

Create all core domain tables for Solmar Workflow Automation Platform.

Revision ID: 001_initial_migration
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_migration'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index('ix_users_email', ['email'], unique=True)
        batch_op.create_index('ix_users_username', ['username'], unique=True)

    # Create role_permissions table
    op.create_table('role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_name')
    )
    with op.batch_alter_table('role_permissions', schema=None) as batch_op:
        batch_op.create_index('ix_role_permissions_role_name', ['role_name'], unique=True)

    # Create workflow_definitions table
    op.create_table('workflow_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('definition_json', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('workflow_definitions', schema=None) as batch_op:
        batch_op.create_index('ix_workflow_definitions_name', ['name'], unique=False)

    # Create workflow_instances table
    op.create_table('workflow_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_definition_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('started_by', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_completion_at', sa.DateTime(), nullable=True),
        sa.Column('actual_completion_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['started_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_definition_id'], ['workflow_definitions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('workflow_instances', schema=None) as batch_op:
        batch_op.create_index('ix_workflow_instances_started_at', ['started_at'], unique=False)
        batch_op.create_index('ix_workflow_instances_status', ['status'], unique=False)
        batch_op.create_index('ix_workflow_instances_workflow_definition_id', ['workflow_definition_id'], unique=False)

    # Create audit_trail table
    op.create_table('audit_trail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('audit_trail', schema=None) as batch_op:
        batch_op.create_index('ix_audit_trail_entity_type', ['entity_type'], unique=False)
        batch_op.create_index('ix_audit_trail_performed_at', ['performed_at'], unique=False)

    # Create approval_requests table
    op.create_table('approval_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_instance_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('decision', sa.String(length=50), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('required_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('escalated_to', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['escalated_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_instance_id'], ['workflow_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('approval_requests', schema=None) as batch_op:
        batch_op.create_index('ix_approval_requests_completed_at', ['completed_at'], unique=False)
        batch_op.create_index('ix_approval_requests_status', ['status'], unique=False)
        batch_op.create_index('ix_approval_requests_workflow_instance_id', ['workflow_instance_id'], unique=False)

    # Create task_assignments table
    op.create_table('task_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_instance_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_instance_id'], ['workflow_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('task_assignments', schema=None) as batch_op:
        batch_op.create_index('ix_task_assignments_assigned_to', ['assigned_to'], unique=False)
        batch_op.create_index('ix_task_assignments_due_at', ['due_at'], unique=False)
        batch_op.create_index('ix_task_assignments_status', ['status'], unique=False)
        batch_op.create_index('ix_task_assignments_workflow_instance_id', ['workflow_instance_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order to respect foreign key constraints
    with op.batch_alter_table('task_assignments', schema=None) as batch_op:
        batch_op.drop_index('ix_task_assignments_workflow_instance_id')
        batch_op.drop_index('ix_task_assignments_status')
        batch_op.drop_index('ix_task_assignments_due_at')
        batch_op.drop_index('ix_task_assignments_assigned_to')

    op.drop_table('task_assignments')

    with op.batch_alter_table('approval_requests', schema=None) as batch_op:
        batch_op.drop_index('ix_approval_requests_workflow_instance_id')
        batch_op.drop_index('ix_approval_requests_status')
        batch_op.drop_index('ix_approval_requests_completed_at')

    op.drop_table('approval_requests')

    with op.batch_alter_table('audit_trail', schema=None) as batch_op:
        batch_op.drop_index('ix_audit_trail_performed_at')
        batch_op.drop_index('ix_audit_trail_entity_type')

    op.drop_table('audit_trail')

    with op.batch_alter_table('workflow_instances', schema=None) as batch_op:
        batch_op.drop_index('ix_workflow_instances_workflow_definition_id')
        batch_op.drop_index('ix_workflow_instances_status')
        batch_op.drop_index('ix_workflow_instances_started_at')

    op.drop_table('workflow_instances')

    with op.batch_alter_table('workflow_definitions', schema=None) as batch_op:
        batch_op.drop_index('ix_workflow_definitions_name')

    op.drop_table('workflow_definitions')

    with op.batch_alter_table('role_permissions', schema=None) as batch_op:
        batch_op.drop_index('ix_role_permissions_role_name')

    op.drop_table('role_permissions')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_username')
        batch_op.drop_index('ix_users_email')

    op.drop_table('users')