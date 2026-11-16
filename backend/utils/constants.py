from enum import StrEnum


class ComponentUnit(StrEnum):
    PCS = "шт"
    METER = "м"
    CENTIMETER = "см"
    GRAM = "г"
    PACK = "упаковка"


class R2Folders(StrEnum):
    COMPONENT = "jewel_calc/components"
    JEWELRY = "jewel_calc/jewelry"


class SkipReason(StrEnum):
    NOT_FOUND = "not found"
    ALREADY_ARCHIVED = "already archived"
    ALREADY_ACTIVE = "already active"
    SYSTEM_TYPE = "system type"
    USED_BY_COMPONENTS = "used by active components"
    TYPE_ARCHIVED = "type is archived"
    NAME_TAKEN = "name already used"
