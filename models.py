from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship

from database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    account_id = Column(String, unique=True, index=True)
    account_name = Column(String)
    app_secret_token = Column(String)
    website = Column(String, nullable=True)

    # Define the relationship to Destination
    destinations = relationship("Destination", back_populates="account")

class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    http_method = Column(String)
    headers = Column(JSON)
    account_id = Column(Integer, ForeignKey("accounts.id"))

    # Define the relationship to Account
    account = relationship("Account", back_populates="destinations")
