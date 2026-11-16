"""jewelry

Revision ID: b7e2a91c4d08
Revises: c4a1e8b07d21
Create Date: 2026-11-17 00:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e2a91c4d08"
down_revision: Union[str, Sequence[str], None] = "c4a1e8b07d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jewelry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guid", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_key", sa.String(length=512), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid"),
    )

    op.create_table(
        "jewelry_part",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("jewelry_id", sa.Integer(), nullable=False),
        sa.Column("component_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_cost", sa.Float(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_jewelry_part_quantity_positive"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_jewelry_part_unit_cost_non_negative"),
        sa.ForeignKeyConstraint(["component_id"], ["component.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["jewelry_id"], ["jewelry.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jewelry_id", "component_id", name="uq_jewelry_part_component"),
        sa.UniqueConstraint("jewelry_id", "position", name="uq_jewelry_part_position"),
    )
    op.create_index("ix_jewelry_part_component_id", "jewelry_part", ["component_id"])
    op.create_index("ix_jewelry_part_jewelry_id", "jewelry_part", ["jewelry_id"])

    op.create_table(
        "jewelry_photo",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guid", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("jewelry_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("image", sa.String(length=512), nullable=False),
        sa.Column("image_preview", sa.String(length=512), nullable=False),
        sa.Column("image_on_s3", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("image_preview_on_s3", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["jewelry_id"], ["jewelry.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid"),
        sa.UniqueConstraint("jewelry_id", "position", name="uq_jewelry_photo_position"),
    )
    op.create_index("ix_jewelry_photo_jewelry_id", "jewelry_photo", ["jewelry_id"])


def downgrade() -> None:
    op.drop_index("ix_jewelry_photo_jewelry_id", table_name="jewelry_photo")
    op.drop_table("jewelry_photo")
    op.drop_index("ix_jewelry_part_jewelry_id", table_name="jewelry_part")
    op.drop_index("ix_jewelry_part_component_id", table_name="jewelry_part")
    op.drop_table("jewelry_part")
    op.drop_table("jewelry")
