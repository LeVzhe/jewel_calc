from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Uuid, false, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from utils.text import utcnow


class BaseAlchemy(DeclarativeBase):
    pass


class BaseModel(BaseAlchemy):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    guid: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )


class BaseDataModel(BaseModel):
    __abstract__ = True

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )
