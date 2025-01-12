from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import relationship

from ..db import Base


class WalletModel(Base):
    __tablename__ = 'wallets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String)
    name = Column(String)

    user_id = Column(String, ForeignKey('users.telegram_id'))
    settings_id = Column(Integer, ForeignKey('settings.id'), nullable=True, default=None)

    user = relationship("UserModel", lazy='joined', uselist=False, back_populates='wallets')
    settings = relationship("SettingsModel", lazy='joined', uselist=False, back_populates='wallet', single_parent=True)

    __table_args__ = (
        UniqueConstraint(address, user_id),
    )
