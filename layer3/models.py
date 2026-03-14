from sqlalchemy import String, Integer, Float, ForeignKey, Column, Boolean
from sqlalchemy.orm import relationship
from db import Base

class Model(Base):
    __tablename__ = 'models'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    current_version_id = Column(String)
    versions = relationship('Version', back_populates='model')

class Version(Base):
    __tablename__ = 'versions'
    id = Column(String, primary_key=True)
    version_tag = Column(String, nullable=False)
    framework = Column(String, nullable=False)
    model_id = Column(String, ForeignKey("models.id"))
    current_version = Column(Boolean, nullable=True)
    model = relationship('Model', back_populates='versions')
