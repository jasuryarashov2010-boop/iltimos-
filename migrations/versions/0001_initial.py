"""Idempotent initial schema for Kitobxon V10."""
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL-first, idempotent DDL. This avoids duplicate-index failures on redeploys.
    op.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username VARCHAR(255),
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        title VARCHAR(300) NOT NULL,
        author VARCHAR(300) NOT NULL,
        review TEXT NOT NULL,
        photo_file_id VARCHAR(512),
        normalized_key VARCHAR(700) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'pending',
        reject_reason TEXT,
        published_message_id INTEGER,
        duplicate_of_id INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        message_text TEXT NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'open',
        admin_id BIGINT,
        admin_reply TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS bot_settings (
        key VARCHAR(100) PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """)

    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(255)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(255)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(255)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS user_id BIGINT")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS title VARCHAR(300)")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS author VARCHAR(300)")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS review TEXT")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS photo_file_id VARCHAR(512)")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS normalized_key VARCHAR(700)")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'pending'")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS reject_reason TEXT")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS published_message_id INTEGER")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS duplicate_of_id INTEGER")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS user_id BIGINT")
    op.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS message_text TEXT")
    op.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'open'")
    op.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS admin_id BIGINT")
    op.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS admin_reply TEXT")
    op.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")

    op.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_last_seen_at ON users (last_seen_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_recommendations_status_created ON recommendations (status, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_recommendations_normalized_key ON recommendations (normalized_key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_recommendations_user_id ON recommendations (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_support_tickets_status_created ON support_tickets (status, created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS support_tickets")
    op.execute("DROP TABLE IF EXISTS recommendations")
    op.execute("DROP TABLE IF EXISTS bot_settings")
    op.execute("DROP TABLE IF EXISTS users")
