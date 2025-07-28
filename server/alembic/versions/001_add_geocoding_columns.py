"""Add geocoding columns to jecc_logs

Revision ID: 001
Revises: 
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns for geocoding
    op.add_column('jecc_logs', sa.Column('latitude', sa.Numeric(10, 8), nullable=True))
    op.add_column('jecc_logs', sa.Column('longitude', sa.Numeric(11, 8), nullable=True))
    op.add_column('jecc_logs', sa.Column('geocoded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jecc_logs', sa.Column('geocoded_address', sa.Text(), nullable=True))
    
    # Add metadata columns
    op.add_column('jecc_logs', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('jecc_logs', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    
    # Create indexes for performance
    op.create_index('ix_jecc_logs_log_date', 'jecc_logs', ['log_date'])
    op.create_index('ix_jecc_logs_cfs_number', 'jecc_logs', ['cfs_number'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_jecc_logs_cfs_number', table_name='jecc_logs')
    op.drop_index('ix_jecc_logs_log_date', table_name='jecc_logs')
    
    # Remove columns
    op.drop_column('jecc_logs', 'updated_at')
    op.drop_column('jecc_logs', 'created_at')
    op.drop_column('jecc_logs', 'geocoded_address')
    op.drop_column('jecc_logs', 'geocoded_at')
    op.drop_column('jecc_logs', 'longitude')
    op.drop_column('jecc_logs', 'latitude')