from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog_app.models.color_models import Color
from app.catalog_app.models.component_type_models import ComponentType
from utils.base_model import BaseAlchemy, BaseDataModel
from utils.constants import ComponentUnit


class Component(BaseDataModel):
    """Позиция каталога: цена за одну единицу, тип, необязательный цвет и фото."""

    __tablename__ = "component"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_key: Mapped[str] = mapped_column(String(512), nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ComponentUnit.PCS.value,
        server_default=text("'шт'"),
    )
    article: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image: Mapped[str] = mapped_column(String(512), nullable=False)
    image_preview: Mapped[str] = mapped_column(String(512), nullable=False)
    image_on_s3: Mapped[bool] = mapped_column(default=False, server_default=text("false"), nullable=False)
    image_preview_on_s3: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    type_id: Mapped[int] = mapped_column(
        ForeignKey("component_type.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    color_id: Mapped[int | None] = mapped_column(
        ForeignKey("color.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    component_type: Mapped[ComponentType] = relationship(ComponentType, lazy="selectin")
    color: Mapped[Color | None] = relationship(Color, lazy="selectin")
    shops: Mapped[list[ComponentShop]] = relationship(
        back_populates="component",
        cascade="all, delete-orphan",
        order_by="ComponentShop.position",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("cost >= 0", name="ck_component_cost_non_negative"),
        CheckConstraint(
            "unit IN ('шт', 'м', 'см', 'г', 'упаковка')",
            name="ck_component_unit",
        ),
        Index(
            "uq_component_active_name_per_type",
            "type_id",
            "name_key",
            unique=True,
            postgresql_where=text("is_archived = false"),
        ),
    )

    def __str__(self) -> str:
        return f"{self.id=}, {self.name=}, {self.type_id=}"


class ComponentShop(BaseAlchemy):
    """Свободная пометка, где позицию покупали или где её можно купить."""

    __tablename__ = "component_shop"
    __table_args__ = (UniqueConstraint("component_id", "position", name="uq_component_shop_position"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    component_id: Mapped[int] = mapped_column(
        ForeignKey("component.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)

    component: Mapped[Component] = relationship(back_populates="shops")
