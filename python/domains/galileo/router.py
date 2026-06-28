import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from scripts.api_session import get_db
# Import the new service
from domains.galileo.service import GalileoService
from scripts.api_schema import GalileoNodesOut, GalileoLinksOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/galileo", tags=["galileo"])

@router.get("/nodes", response_model=List[GalileoNodesOut])
def get_galileo_nodes(db: Session = Depends(get_db)):
    """
    Fetches the Harry Beck grid-snapped nodes via GalileoService.
    """
    try:
        # Now calls the Domain Service instead of a generic script
        return GalileoService.get_all_nodes(db)
    except Exception as e:
        logger.error(f"Error in get_galileo_nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/links", response_model=List[GalileoLinksOut])
def get_galileo_links(db: Session = Depends(get_db)):
    """
    Fetches the Harry Beck inter-city fiber links via GalileoService.
    """
    try:
        return GalileoService.get_all_links(db)
    except Exception as e:
        logger.error(f"Error in get_galileo_links: {e}")
        raise HTTPException(status_code=500, detail=str(e))