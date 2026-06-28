import os
import sys
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "..", "..", "scripts")
sys.path.append(SCRIPTS_DIR)

import scripts.api_operation as api_operation
from scripts.api_schema import CrossConnectIn, CrossConnectOut, CrossConnectUpdate
from scripts.cli_base import get_db
# Assume api_operation, CrossConnectOut, CrossConnectIn, CrossConnectUpdate, get_db are imported

router = APIRouter(
    prefix="/cross_connects",
    tags=["Cross Connects"],
    responses={404: {"description": "Not found"}},
)

# GET all cross connects
@router.get("/", response_model=List[CrossConnectOut], summary="List all Cross Connects")
def list_cross_connects(db: Session = Depends(get_db)):
    connects = api_operation.get_cross_connects(db)
    if not connects:
        raise HTTPException(status_code=404, detail={"error": "No cross connects found"})
    return connects

# GET cross connect by ID
@router.get("/{connect_id}", response_model=CrossConnectOut, summary="Get a Cross Connect by ID")
def get_connect_by_id(connect_id: UUID, db: Session = Depends(get_db)):
    connect = api_operation.get_cross_connect_by_id(db, connect_id)
    if not connect:
        raise HTTPException(status_code=404, detail="Cross Connect not found")
    return connect

# POST create cross connect
@router.post("/", response_model=CrossConnectOut, status_code=201, summary="Create a new Cross Connect")
def create_cross_connect(data: CrossConnectIn, db: Session = Depends(get_db)):
    try:
        new_connect = api_operation.post_cross_connect(db, data)
        return new_connect
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Data validation failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error creating cross connect", "message": str(e)})

# PUT update cross connect
@router.put("/{connect_id}", response_model=CrossConnectOut, summary="Update Cross Connect details")
def update_cross_connect(connect_id: UUID, update: CrossConnectUpdate, db: Session = Depends(get_db)):
    try:
        updated_connect = api_operation.put_cross_connect(db, connect_id, update)
        if not updated_connect:
            raise HTTPException(status_code=404, detail="Cross Connect not found")
        return updated_connect
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Update failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error updating cross connect", "message": str(e)})

# DELETE cross connect
@router.delete("/{connect_id}", response_model=dict, summary="Delete a Cross Connect")
def delete_cross_connect(connect_id: UUID, db: Session = Depends(get_db)):
    try:
        success = api_operation.delete_cross_connect_by_id(db, connect_id)
        if not success:
            raise HTTPException(status_code=404, detail={"error": f"Cross Connect {connect_id} not found"})
        return {"message": f"Cross Connect {connect_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error deleting cross connect", "message": str(e)})