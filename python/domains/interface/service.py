from sqlalchemy.orm import Session
from uuid import UUID
from scripts.api_model import Interface, InterfaceDetail
from scripts.api_schema import InterfaceIn, InterfaceUpdate

class InterfaceService:
    @staticmethod
    def get_all(db: Session):
        return db.query(Interface).all()

    @staticmethod
    def get_by_id(db: Session, interface_id: UUID):
        return db.query(Interface).filter(Interface.interface_id == interface_id).first()

    @staticmethod
    def get_by_device(db: Session, device_id: UUID):
        return db.query(Interface).filter(Interface.device_id == device_id).all()

    @staticmethod
    def create(db: Session, data: InterfaceIn):
        new_int = Interface(**data.model_dump())
        db.add(new_int)
        db.commit()
        db.refresh(new_int)
        return new_int

    @staticmethod
    def get_detail(db: Session, interface_id: UUID):
        return db.query(InterfaceDetail).filter(InterfaceDetail.interface_id == interface_id).first()