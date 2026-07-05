"""Initial database schema — all core tables for the Spotify Discovery Engine.

Revision ID: 001
Revises: None
Create Date: 2026-07-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # --- raw_reviews ---
    op.create_table(
        'raw_reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source', sa.String(50), nullable=False, index=True),
        sa.Column('external_id', sa.String(255), unique=True, index=True),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('title', sa.Text, nullable=True),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('author_hash', sa.String(64), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('app_version', sa.String(50), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('engagement_score', sa.Integer, nullable=True),
        sa.Column('raw_url', sa.Text, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('is_relevant', sa.Boolean, nullable=True),
        sa.Column('exclusion_reason', sa.String(255), nullable=True),
        sa.Column('body_hash', sa.String(64), nullable=True, index=True),
        sa.Column('source_weight', sa.Float, nullable=True),
        sa.Column('recency_score', sa.Float, nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        # Reddit extras
        sa.Column('subreddit', sa.String(100), nullable=True),
        sa.Column('post_title', sa.Text, nullable=True),
        sa.Column('post_score', sa.Integer, nullable=True),
        sa.Column('comment_score', sa.Integer, nullable=True),
        sa.Column('is_comment', sa.Boolean, server_default='false'),
        sa.Column('parent_post_id', sa.String(255), nullable=True),
        # Forum extras
        sa.Column('reply_count', sa.Integer, nullable=True),
        sa.Column('kudos_count', sa.Integer, nullable=True),
        sa.Column('thread_status', sa.String(100), nullable=True),
        # Twitter extras
        sa.Column('like_count', sa.Integer, nullable=True),
        sa.Column('retweet_count', sa.Integer, nullable=True),
    )

    # --- classified_reviews ---
    op.create_table(
        'classified_reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('raw_review_id', UUID(as_uuid=True), sa.ForeignKey('raw_reviews.id'), nullable=False, unique=True, index=True),
        sa.Column('is_discovery_relevant', sa.Boolean, nullable=True),
        sa.Column('primary_complaint_category', sa.String(100), nullable=True, index=True),
        sa.Column('secondary_complaint_category', sa.String(100), nullable=True),
        sa.Column('user_segment_signal', sa.String(100), nullable=True, index=True),
        sa.Column('sentiment', sa.String(50), nullable=True, index=True),
        sa.Column('sentiment_score', sa.Float, nullable=True),
        sa.Column('discovery_intent', sa.String(20), nullable=True),
        sa.Column('repetition_behavior_mentioned', sa.Boolean, nullable=True),
        sa.Column('key_frustration_phrase', sa.Text, nullable=True),
        sa.Column('unmet_need', sa.Text, nullable=True),
        sa.Column('jtbd_statement', sa.Text, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('detected_language', sa.String(10), nullable=True),
        sa.Column('source_weight', sa.Float, nullable=True),
        sa.Column('recency_score', sa.Float, nullable=True),
        sa.Column('classified_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('classification_model', sa.String(50), nullable=True),
        sa.Column('classification_failed', sa.Boolean, server_default='false'),
        sa.Column('embedding_pending', sa.Boolean, server_default='true'),
    )

    # Add vector column separately (Alembic doesn't natively handle pgvector)
    op.execute('ALTER TABLE classified_reviews ADD COLUMN embedding vector(1536)')

    # --- themes ---
    op.create_table(
        'themes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cluster_id', sa.Integer, unique=True, nullable=False, index=True),
        sa.Column('theme_name', sa.String(255), nullable=False),
        sa.Column('theme_description', sa.Text, nullable=True),
        sa.Column('representative_quote', sa.Text, nullable=True),
        sa.Column('review_count', sa.Integer, server_default='0'),
        sa.Column('cross_source_count', sa.Integer, server_default='0'),
        sa.Column('confidence_level', sa.String(20), nullable=True),
        sa.Column('trend_direction', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # --- review_theme_mapping ---
    op.create_table(
        'review_theme_mapping',
        sa.Column('review_id', UUID(as_uuid=True), sa.ForeignKey('classified_reviews.id'), primary_key=True),
        sa.Column('theme_id', UUID(as_uuid=True), sa.ForeignKey('themes.id'), primary_key=True),
        sa.Column('similarity_score', sa.Float, nullable=True),
    )

    # --- synthesis_cache ---
    op.create_table(
        'synthesis_cache',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cache_key', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )

    # --- query_log ---
    op.create_table(
        'query_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('result_count', sa.Integer, nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('queried_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.execute('ALTER TABLE query_log ADD COLUMN query_embedding vector(1536)')

    # --- quote_collections ---
    op.create_table(
        'quote_collections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # --- collection_items ---
    op.create_table(
        'collection_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('collection_id', UUID(as_uuid=True), sa.ForeignKey('quote_collections.id'), nullable=False, index=True),
        sa.Column('classified_review_id', UUID(as_uuid=True), sa.ForeignKey('classified_reviews.id'), nullable=False, index=True),
        sa.Column('note', sa.Text, nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # --- pipeline_runs ---
    op.create_table(
        'pipeline_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_name', sa.String(100), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        sa.Column('entries_processed', sa.Integer, server_default='0'),
        sa.Column('entries_created', sa.Integer, server_default='0'),
        sa.Column('entries_failed', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('details', JSONB, nullable=True),
    )

    # Create indexes for common query patterns
    op.create_index('ix_raw_reviews_source_published', 'raw_reviews', ['source', 'published_at'])
    op.create_index('ix_classified_category_segment', 'classified_reviews', ['primary_complaint_category', 'user_segment_signal'])


def downgrade() -> None:
    op.drop_index('ix_classified_category_segment')
    op.drop_index('ix_raw_reviews_source_published')
    op.drop_table('pipeline_runs')
    op.drop_table('collection_items')
    op.drop_table('quote_collections')
    op.drop_table('query_log')
    op.drop_table('synthesis_cache')
    op.drop_table('review_theme_mapping')
    op.drop_table('themes')
    op.drop_table('classified_reviews')
    op.drop_table('raw_reviews')
