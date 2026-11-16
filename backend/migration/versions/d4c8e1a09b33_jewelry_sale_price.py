"""jewelry sale price

Revision ID: d4c8e1a09b33
Revises: b7e2a91c4d08
Create Date: 2026-11-17 01:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4c8e1a09b33"
down_revision: Union[str, Sequence[str], None] = "b7e2a91c4d08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jewelry", sa.Column("sale_price", sa.Float(), nullable=True))
    op.execute(
        """
        UPDATE jewelry AS piece
        SET sale_price = COALESCE((
            SELECT ROUND(SUM(ROUND((part.quantity * component.cost)::numeric, 2)) * 1.3, 2)
            FROM jewelry_part AS part
            JOIN component ON component.id = part.component_id
            WHERE part.jewelry_id = piece.id
        ), 0)
        """
    )
    op.alter_column("jewelry", "sale_price", nullable=False)
    op.create_check_constraint("ck_jewelry_sale_price_non_negative", "jewelry", "sale_price >= 0")


def downgrade() -> None:
    op.drop_constraint("ck_jewelry_sale_price_non_negative", "jewelry", type_="check")
    op.drop_column("jewelry", "sale_price")
