from sqlalchemy.orm import Session
from uuid import UUID
from scripts.api_model import PatchPanel # Assuming this exists in api_model
from scripts.api_schema import PatchPanelIn

class PatchPanelService:
    @staticmethod
    def get_by_id(db: Session, port_id: UUID):
        return db.query(PatchPanel).filter(PatchPanel.port_id == port_id).first()

    @staticmethod
    def get_by_device(db: Session, device_id: UUID):
        return db.query(PatchPanel).filter(PatchPanel.device_id == device_id).all()

    @staticmethod
    def create(db: Session, data: PatchPanelIn):
        new_panel = PatchPanel(**data.model_dump())
        db.add(new_panel)
        db.commit()
        db.refresh(new_panel)
        return new_panel

    @staticmethod
    def update(db: Session, port_id: UUID, data: PatchPanelIn):
        panel = db.query(PatchPanel).filter(PatchPanel.port_id == port_id).first()
        if not panel:
            return None
        for key, value in data.model_dump().items():
            setattr(panel, key, value)
        db.commit()
        db.refresh(panel)
        return panel