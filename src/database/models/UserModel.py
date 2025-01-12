from typing import List

from sqlalchemy import String, Column, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, relationship
from .SettingsModel import SettingsModel

from ..db import Base


class UserModel(Base):
    __tablename__ = "users"

    telegram_id = Column(String, primary_key=True)
    username = Column(String)
    subscriber = Column(Boolean, default=False, nullable=False)
    phone = Column(String, nullable=True, default=None)

    settings_id = Column(Integer, ForeignKey('settings.id'), nullable=True, default=None)

    settings: Mapped[SettingsModel] = relationship("SettingsModel", back_populates="user", uselist=False,
                                             lazy="selectin", cascade="all, delete-orphan",
                                             single_parent=True)
    wallets: Mapped[List["WalletModel"]] = relationship('WalletModel',
                                                        lazy="selectin",
                                                        back_populates='user',
                                                        cascade="all, delete-orphan"
                                                        )
