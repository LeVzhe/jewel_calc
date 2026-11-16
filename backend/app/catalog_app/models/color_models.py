from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from utils.base_model import BaseDataModel


class Color(BaseDataModel):
    """Цвет комплектующего. Фото остаётся основным видом, цвет — подпись для фильтра."""

    __tablename__ = "color"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    name_key: Mapped[str] = mapped_column(String(256), nullable=False)

    __table_args__ = (Index("uq_color_name_lower", "name_key", unique=True),)

    def __str__(self) -> str:
        return f"{self.id=}, {self.name=}"
