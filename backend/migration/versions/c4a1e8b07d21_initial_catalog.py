"""initial catalog

Revision ID: c4a1e8b07d21
Revises:
Create Date: 2026-11-16 23:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a1e8b07d21"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROOT_TYPES = ("Фурнитура", "Упаковка", "Нить")
COLORS = (
    "Серебро",
    "Золото",
    "Розовое золото",
    "Античное серебро",
    "Античное золото",
    "Медь",
    "Бронза",
    "Чёрный",
    "Белый",
    "Прозрачный",
)


def upgrade() -> None:
    op.create_table(
        "component_type",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guid", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_key", sa.String(length=512), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("(parent_id IS NULL) = is_system", name="ck_component_type_root_is_system"),
        sa.ForeignKeyConstraint(["parent_id"], ["component_type.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid"),
    )
    op.create_index("ix_component_type_parent_id", "component_type", ["parent_id"])
    op.create_index(
        "uq_component_type_root_name",
        "component_type",
        ["name_key"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )
    op.create_index(
        "uq_component_type_child_name",
        "component_type",
        ["parent_id", "name_key"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NOT NULL"),
    )

    op.create_table(
        "color",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guid", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("name_key", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid"),
    )
    op.create_index("uq_color_name_lower", "color", ["name_key"], unique=True)

    op.create_table(
        "component",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guid", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_key", sa.String(length=512), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), server_default=sa.text("'шт'"), nullable=False),
        sa.Column("article", sa.String(length=128), nullable=True),
        sa.Column("image", sa.String(length=512), nullable=False),
        sa.Column("image_preview", sa.String(length=512), nullable=False),
        sa.Column("image_on_s3", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("image_preview_on_s3", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("color_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("cost >= 0", name="ck_component_cost_non_negative"),
        sa.CheckConstraint(
            "unit IN ('шт', 'м', 'см', 'г', 'упаковка')",
            name="ck_component_unit",
        ),
        sa.ForeignKeyConstraint(["color_id"], ["color.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["type_id"], ["component_type.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid"),
    )
    op.create_index("ix_component_color_id", "component", ["color_id"])
    op.create_index("ix_component_type_id", "component", ["type_id"])
    op.create_index(
        "uq_component_active_name_per_type",
        "component",
        ["type_id", "name_key"],
        unique=True,
        postgresql_where=sa.text("is_archived = false"),
    )

    op.create_table(
        "component_shop",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("component_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=500), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["component_id"], ["component.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("component_id", "position", name="uq_component_shop_position"),
    )

    type_table = sa.table(
        "component_type",
        sa.column("name", sa.String),
        sa.column("name_key", sa.String),
        sa.column("parent_id", sa.Integer),
        sa.column("is_system", sa.Boolean),
    )
    op.bulk_insert(
        type_table,
        [
            {"name": name, "name_key": name.casefold(), "parent_id": None, "is_system": True}
            for name in ROOT_TYPES
        ],
    )

    color_table = sa.table(
        "color",
        sa.column("name", sa.String),
        sa.column("name_key", sa.String),
    )
    op.bulk_insert(
        color_table,
        [{"name": name, "name_key": name.casefold()} for name in COLORS],
    )


def downgrade() -> None:
    op.drop_table("component_shop")
    op.drop_table("component")
    op.drop_table("color")
    op.drop_table("component_type")
