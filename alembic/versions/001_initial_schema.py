"""Initial schema: users, projects, logs."""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None


def upgrade() -> None:
    """Create initial tables."""

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('oauth_provider', sa.String(50), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('subscription_tier', sa.String(50), server_default='free'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('source_video_path', sa.String(500), nullable=True),
        sa.Column('source_music_path', sa.String(500), nullable=True),
        sa.Column('output_video_path', sa.String(500), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('policy_findings', sa.JSON(), nullable=True),
        sa.Column('youtube_video_id', sa.String(255), nullable=True),
        sa.Column('instagram_media_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])
    op.create_index('ix_projects_youtube_video_id', 'projects', ['youtube_video_id'])

    op.create_table(
        'processing_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), server_default='info'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_processing_logs_event_type', 'processing_logs', ['event_type'])
    op.create_index('ix_processing_logs_timestamp', 'processing_logs', ['timestamp'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('ix_processing_logs_timestamp')
    op.drop_index('ix_processing_logs_event_type')
    op.drop_table('processing_logs')

    op.drop_index('ix_projects_youtube_video_id')
    op.drop_index('ix_projects_created_at')
    op.drop_table('projects')

    op.drop_index('ix_users_email')
    op.drop_table('users')
