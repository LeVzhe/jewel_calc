from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from utils.base_model import BaseDataModel


class ComponentType(BaseDataModel):
    """Корень каталога или прямой потомок одного из трёх корней."""

    __tablename__ = "component_type"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_key: Mapped[str] = mapped_column(String(512), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("component_type.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    is_system: Mapped[bool] = mapped_column(default=False, server_default=text("false"), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(parent_id IS NULL) = is_system",
            name="ck_component_type_root_is_system",
        ),
        Index(
            "uq_component_type_root_name",
            "name_key",
            unique=True,
            postgresql_where=text("parent_id IS NULL"),
        ),
        Index(
            "uq_component_type_child_name",
            "parent_id",
            "name_key",
            unique=True,
            postgresql_where=text("parent_id IS NOT NULL"),
        ),
    )

    def __str__(self) -> str:
        return f"{self.id=}, {self.name=}, {self.parent_id=}"
