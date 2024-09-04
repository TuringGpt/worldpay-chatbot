"""Permission Framework

Revision ID: 27c6ecc08586
Revises: 2666d766cb9b
Create Date: 2023-05-24 18:45:17.244495

"""
import fastapi_users_db_sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "27c6ecc08586"
down_revision = "2666d766cb9b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Truncate the index_attempt table
    op.execute("TRUNCATE TABLE index_attempt")

    bind = op.get_bind()
    inspector = inspect(bind)

    # Check if the 'connector' table already exists
    if not inspector.has_table("connector"):
        op.create_table(
            "connector",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "source",
                sa.Enum(
                    "SLACK",
                    "WEB",
                    "GOOGLE_DRIVE",
                    "GITHUB",
                    "CONFLUENCE",
                    name="documentsource",
                    native_enum=False,
                ),
                nullable=False,
            ),
            sa.Column(
                "input_type",
                sa.Enum(
                    "LOAD_STATE",
                    "POLL",
                    "EVENT",
                    name="inputtype",
                    native_enum=False,
                ),
                nullable=True,
            ),
            sa.Column(
                "connector_specific_config",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column("refresh_freq", sa.Integer(), nullable=True),
            sa.Column(
                "time_created",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "time_updated",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("disabled", sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # Check if the 'credential' table already exists
    if not inspector.has_table("credential"):
        op.create_table(
            "credential",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "credential_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
            ),
            sa.Column(
                "user_id",
                fastapi_users_db_sqlalchemy.generics.GUID(),
                nullable=True,
            ),
            sa.Column("public_doc", sa.Boolean(), nullable=False),
            sa.Column(
                "time_created",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "time_updated",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["user.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    # Check if the 'connector_credential_pair' table already exists
    if not inspector.has_table("connector_credential_pair"):
        op.create_table(
            "connector_credential_pair",
            sa.Column("connector_id", sa.Integer(), nullable=False),
            sa.Column("credential_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["connector_id"],
                ["connector.id"],
            ),
            sa.ForeignKeyConstraint(
                ["credential_id"],
                ["credential.id"],
            ),
            sa.PrimaryKeyConstraint("connector_id", "credential_id"),
        )

    # Check if the 'connector_id' column exists in the 'index_attempt' table
    existing_columns = [col["name"] for col in inspector.get_columns("index_attempt")]
    
    if "connector_id" not in existing_columns:
        op.add_column(
            "index_attempt",
            sa.Column("connector_id", sa.Integer(), nullable=True),
        )

    if "credential_id" not in existing_columns:
        op.add_column(
            "index_attempt",
            sa.Column("credential_id", sa.Integer(), nullable=True),
        )

    # Add foreign key constraints if they don't exist
    constraints = inspector.get_foreign_keys("index_attempt")

    if not any(c["name"] == "fk_index_attempt_credential_id" for c in constraints):
        op.create_foreign_key(
            "fk_index_attempt_credential_id",
            "index_attempt",
            "credential",
            ["credential_id"],
            ["id"],
        )

    if not any(c["name"] == "fk_index_attempt_connector_id" for c in constraints):
        op.create_foreign_key(
            "fk_index_attempt_connector_id",
            "index_attempt",
            "connector",
            ["connector_id"],
            ["id"],
        )

    # Drop columns if they exist
    if "connector_specific_config" in existing_columns:
        op.drop_column("index_attempt", "connector_specific_config")
    
    if "source" in existing_columns:
        op.drop_column("index_attempt", "source")
    
    if "input_type" in existing_columns:
        op.drop_column("index_attempt", "input_type")


def downgrade() -> None:
    # Truncate the index_attempt table
    op.execute("TRUNCATE TABLE index_attempt")

    # Add the columns back
    op.add_column(
        "index_attempt",
        sa.Column("input_type", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "index_attempt",
        sa.Column("source", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "index_attempt",
        sa.Column(
            "connector_specific_config",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
    )

    # Check if the constraint exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    constraints = inspector.get_foreign_keys("index_attempt")

    if any(
        constraint["name"] == "fk_index_attempt_credential_id"
        for constraint in constraints
    ):
        op.drop_constraint(
            "fk_index_attempt_credential_id", "index_attempt", type_="foreignkey"
        )

    if any(
        constraint["name"] == "fk_index_attempt_connector_id"
        for constraint in constraints
    ):
        op.drop_constraint(
            "fk_index_attempt_connector_id", "index_attempt", type_="foreignkey"
        )

    # Drop columns
    op.drop_column("index_attempt", "credential_id")
    op.drop_column("index_attempt", "connector_id")
    op.drop_table("connector_credential_pair")
    op.drop_table("credential")
    op.drop_table("connector")

