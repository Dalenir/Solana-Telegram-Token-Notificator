from sqlalchemy import Integer, Column, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from database.db import Base


class SettingsModel(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, autoincrement=True)

    min_trade = Column(Integer)
    max_trade = Column(Integer)

    min_cap = Column(Float)
    max_cap = Column(Float)

    user = relationship("UserModel", lazy='joined', uselist=False, back_populates='settings')
    wallet = relationship("WalletModel", lazy='joined', uselist=False, back_populates='settings')
