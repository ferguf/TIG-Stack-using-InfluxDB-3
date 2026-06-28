from sqlalchemy.orm import Session
from scripts.api_model import GalileoNodes, GalileoLinks

class GalileoService:
    """
    Service layer for Galileo domain logic. 
    Encapsulates database access and business constraints.
    """
    
    @staticmethod
    def get_all_nodes(db: Session):
        """Fetch and validate all Galileo nodes."""
        nodes = db.query(GalileoNodes).all()
        # Domain-specific filtering logic
        return [node for node in nodes if node is not None]

    @staticmethod
    def get_all_links(db: Session):
        """Fetch all Galileo inter-city fiber links."""
        return db.query(GalileoLinks).all()

    # You can easily add complex domain logic here later, 
    # such as 'snap_node_to_grid' or 'calculate_path_latency'