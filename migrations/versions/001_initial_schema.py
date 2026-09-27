"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'source',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DEGRADED', name='sourcestatus'), nullable=True),
        sa.Column('is_direct', sa.Boolean(), nullable=True),
        sa.Column('parser_contract', sa.String(), nullable=True),
        sa.Column('provenance_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'route_frame',
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('origin', sa.String(), nullable=False),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('stratum', sa.String(), nullable=False),
        sa.Column('inclusion_probability', sa.Float(), nullable=False),
        sa.Column('horvitz_thompson_weight', sa.Float(), nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('route_id')
    )

    op.create_table(
        'collection_run',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('expected_yield_min', sa.Integer(), nullable=True),
        sa.Column('expected_yield_max', sa.Integer(), nullable=True),
        sa.Column('actual_yield', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('SUCCESS', 'FAILED', 'DEGRADED', name='runstatus'), nullable=True),
        sa.Column('is_degraded', sa.Boolean(), nullable=True),
        sa.Column('policy_checks', sa.JSON(), nullable=True),
        sa.Column('robots_evidence_ref', sa.String(), nullable=True),
        sa.Column('request_rate', sa.Float(), nullable=True),
        sa.Column('delay_applied', sa.Float(), nullable=True),
        sa.Column('parser_version', sa.String(), nullable=True),
        sa.Column('error_summary', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'raw_quote',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('collection_run_id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.Column('request_spec_id', sa.String(), nullable=True),
        sa.Column('route', sa.String(), nullable=False),
        sa.Column('departure_date', sa.Date(), nullable=False),
        sa.Column('booking_horizon', sa.Integer(), nullable=False),
        sa.Column('raw_payload_ref', sa.String(), nullable=False),
        sa.Column('response_hash', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('http_metadata', sa.JSON(), nullable=True),
        sa.Column('parser_version', sa.String(), nullable=True),
        sa.Column('policy_evidence_ref', sa.String(), nullable=True),
        sa.Column('timestamps', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['collection_run_id'], ['collection_run.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'cell',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('route', sa.String(), nullable=False),
        sa.Column('carrier', sa.String(), nullable=False),
        sa.Column('cabin', sa.String(), nullable=False),
        sa.Column('fare_product_identity', sa.String(), nullable=False),
        sa.Column('booking_horizon', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('definition_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'observation',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('raw_quote_id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('origin', sa.String(), nullable=False),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('carrier', sa.String(), nullable=False),
        sa.Column('flight_identifier', sa.String(), nullable=True),
        sa.Column('departure_datetime', sa.DateTime(), nullable=False),
        sa.Column('arrival_datetime', sa.DateTime(), nullable=True),
        sa.Column('cabin', sa.String(), nullable=False),
        sa.Column('fare_basis_code', sa.String(), nullable=True),
        sa.Column('rbd', sa.String(), nullable=True),
        sa.Column('fare_product_identity', sa.String(), nullable=False),
        sa.Column('is_refundable', sa.Boolean(), nullable=True),
        sa.Column('baggage_allowance', sa.String(), nullable=True),
        sa.Column('change_fee_flag', sa.Boolean(), nullable=True),
        sa.Column('brand_label', sa.String(), nullable=True),
        sa.Column('base_fare', sa.Float(), nullable=True),
        sa.Column('taxes', sa.Float(), nullable=True),
        sa.Column('fees', sa.Float(), nullable=True),
        sa.Column('all_inclusive_price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('booking_horizon', sa.Integer(), nullable=False),
        sa.Column('cell_id', sa.String(), nullable=False),
        sa.Column('validation_status', sa.String(), nullable=False),
        sa.Column('rejection_reason', sa.String(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=True),
        sa.Column('is_outlier', sa.Boolean(), nullable=True),
        sa.Column('is_surrogate', sa.Boolean(), nullable=True),
        sa.Column('cleaning_rule_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cell_id'], ['cell.id'], ),
        sa.ForeignKeyConstraint(['raw_quote_id'], ['raw_quote.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'cell_price',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cell_id', sa.String(), nullable=False),
        sa.Column('period', sa.Date(), nullable=False),
        sa.Column('representative_price', sa.Float(), nullable=False),
        sa.Column('matched_observation_count', sa.Integer(), nullable=False),
        sa.Column('valid_observation_count', sa.Integer(), nullable=False),
        sa.Column('dispersion', sa.Float(), nullable=True),
        sa.Column('outlier_count', sa.Integer(), nullable=True),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.Column('quality_flags', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['cell_id'], ['cell.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'index_value',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('series_id', sa.String(), nullable=False),
        sa.Column('period', sa.Date(), nullable=False),
        sa.Column('aggregate_level', sa.String(), nullable=False),
        sa.Column('index_value', sa.Float(), nullable=False),
        sa.Column('estimator', sa.String(), nullable=False),
        sa.Column('coverage_grade', sa.String(), nullable=True),
        sa.Column('contributing_cell_count', sa.Integer(), nullable=True),
        sa.Column('observation_count', sa.Integer(), nullable=True),
        sa.Column('thin_cell_share', sa.Float(), nullable=True),
        sa.Column('spliced_share', sa.Float(), nullable=True),
        sa.Column('surrogate_share', sa.Float(), nullable=True),
        sa.Column('dispersion', sa.Float(), nullable=True),
        sa.Column('confidence_interval', sa.JSON(), nullable=True),
        sa.Column('contributing_sources', sa.JSON(), nullable=True),
        sa.Column('publication_status', sa.String(), nullable=False),
        sa.Column('methodology_version', sa.String(), nullable=True),
        sa.Column('weight_version', sa.String(), nullable=True),
        sa.Column('data_vintage', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'index_vintage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('index_value_id', sa.Integer(), nullable=False),
        sa.Column('original_published_value', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('publication_timestamp', sa.DateTime(), nullable=False),
        sa.Column('revision_timestamp', sa.DateTime(), nullable=True),
        sa.Column('revision_reason', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('methodology_version', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['index_value_id'], ['index_value.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'weight',
        sa.Column('route', sa.String(), nullable=False),
        sa.Column('weight_value', sa.Float(), nullable=False),
        sa.Column('is_illustrative', sa.Boolean(), nullable=True),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('source_metadata', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('route')
    )


def downgrade() -> None:
    op.drop_table('weight')
    op.drop_table('index_vintage')
    op.drop_table('index_value')
    op.drop_table('cell_price')
    op.drop_table('observation')
    op.drop_table('cell')
    op.drop_table('raw_quote')
    op.drop_table('collection_run')
    op.drop_table('route_frame')
    op.drop_table('source')
