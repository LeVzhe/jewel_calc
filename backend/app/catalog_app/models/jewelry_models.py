from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog_app.models.component_models import Component
from utils.base_model import BaseAlchemy, BaseDataModel


class Jewelry(BaseDataModel):
    """Готовое изделие. Себестоимость считается из состава, название может повторяться."""

    __tablename__ = "jewelry"
    __table_args__ = (CheckConstraint("sale_price >= 0", name="ck_jewelry_sale_price_non_negative"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sale_price: Mapped[float] = mapped_column(Float, nullable=False)

    parts: Mapped[list[JewelryPart]] = relationship(
        back_populates="jewelry",
        cascade="all, delete-orphan",
        order_by="JewelryPart.position",
        lazy="selectin",
    )
    photos: Mapped[list[JewelryPhoto]] = relationship(
        back_populates="jewelry",
        cascade="all, delete-orphan",
        order_by="JewelryPhoto.position",
        lazy="selectin",
    )

    def __str__(self) -> str:
        return f"{self.id=}, {self.name=}"


class JewelryPart(BaseAlchemy):
    """Строка состава. unit_cost — цена комплектующего в момент добавления."""

    __tablename__ = "jewelry_part"
    __table_args__ = (
        UniqueConstraint("jewelry_id", "component_id", name="uq_jewelry_part_component"),
        UniqueConstraint("jewelry_id", "position", name="uq_jewelry_part_position"),
        CheckConstraint("quantity > 0", name="ck_jewelry_part_quantity_positive"),
        CheckConstraint("unit_cost >= 0", name="ck_jewelry_part_unit_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jewelry_id: Mapped[int] = mapped_column(
        ForeignKey("jewelry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_id: Mapped[int] = mapped_column(
        ForeignKey("component.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)

    jewelry: Mapped[Jewelry] = relationship(back_populates="parts")
    component: Mapped[Component] = relationship(Component, lazy="selectin")


class JewelryPhoto(BaseAlchemy):
    """Один кадр изделия. Первый по position — обложка."""

    __tablename__ = "jewelry_photo"
    __table_args__ = (
        UniqueConstraint("jewelry_id", "position", name="uq_jewelry_photo_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guid: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    jewelry_id: Mapped[int] = mapped_column(
        ForeignKey("jewelry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(nullable=False)
    image: Mapped[str] = mapped_column(String(512), nullable=False)
    image_preview: Mapped[str] = mapped_column(String(512), nullable=False)
    image_on_s3: Mapped[bool] = mapped_column(default=False, server_default=text("false"), nullable=False)
    image_preview_on_s3: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false"),
        nullable=False,
    )

    jewelry: Mapped[Jewelry] = relationship(back_populates="photos")
