import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys, os

# Reuse your existing imports
from scripts.api_session import get_db
# Import your new Galileo Models and Schemas
from scripts import api_operation
from scripts.api_model import GalileoNodes, GalileoLinks
from scripts.api_schema import GalileoNodesOut, GalileoLinksOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/galileo", tags=["galileo"])
@router.get("/nodes", response_model=List[GalileoNodesOut])
def get_galileo_nodes(db: Session = Depends(get_db)):
    """
    Fetches the Harry Beck grid-snapped nodes.
    Filters out any null records to prevent validation errors.
    """
    try:
        # 1. Fetch from the operations layer
        nodes = api_operation.get_galileo_nodes(db)
        
        # 2. Filter out None results (The Fix)
        validated_nodes = [node for node in nodes if node is not None]
        
        return validated_nodes
        
    except Exception as e:
        logger.error(f"Error in get_galileo_nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/links", response_model=List[GalileoLinksOut])
def get_galileo_links(db: Session = Depends(get_db)):
    """
    Fetches the Harry Beck inter-city fiber links.
    Provides the snapped A-to-B coordinates for Plotly.
    """
    try:
        links = db.query(GalileoLinks).all()
        return links
    except Exception as e:
        logger.error(f"Error fetching Galileo links: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")