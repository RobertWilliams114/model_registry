from sqlalchemy import String, ForeignKey, Column, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from registry.db import Base

class Model(Base):
    __tablename__ = 'models'
    id = Column(String, primary_key=True)
    owner_team = Column(String)
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
    artifact_uri = Column(String)

class DeploymentRecord(Base):
    __tablename__ = 'deployments'
    id = Column(String, primary_key=True)
    model_id = Column(String, ForeignKey("models.id"))
    version_id = Column(String, ForeignKey("versions.id"))
    status = Column(String)
    endpoint_url = Column(String, nullable=True)
    container_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
