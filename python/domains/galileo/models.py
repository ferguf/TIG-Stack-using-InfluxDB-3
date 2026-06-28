from sqlalchemy import Column, String, Float, Integer
from core.database import Base

class GalileoNodes(Base):
    __tablename__ = "galileo_nodes"
    node_id = Column(String, primary_key=True)
    name = Column(String)
    x = Column(Float)
    y = Column(Float)

class GalileoLinks(Base):
    __tablename__ = "galileo_links"
    link_id = Column(String, primary_key=True)
    source_id = Column(String)
    target_id = Column(String)