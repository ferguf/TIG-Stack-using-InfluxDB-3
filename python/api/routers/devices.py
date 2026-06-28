import uuid as uuid
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from typing import List 
from sqlalchemy.orm import Session
from scripts import api_operation
from scripts.api_schema import DeviceDetailsOut, DeviceIn, DeviceLocationIn, DeviceLocationOut, DeviceLocationUpdate, DeviceOut, DeviceUpdate, HardwareDocumentIn, HardwareDocumentOut, HardwareDocumentUpdate, HardwareSpecsIn, HardwareSpecsOut, HardwareSpecsUpdate, LRICCostModelIn, LRICCostModelOut, LRICCostModelUpdate, PortOut
from scripts.api_session import get_db

from scripts.api_model import Device
router = APIRouter(prefix="/devices", tags=["devices"])

# GET all devices
@router.get("/", response_model=List[DeviceOut])
def get_devices():
    try:
        devices = api_operation.get_devices()
        if not devices:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "No devices found",
                    "reason": "The database returned an empty result set",
                    "hint": "Add devices before querying"
                }
            )
        return devices
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error retrieving devices",
                "message": str(e)
            }
        )


    return devices


# GET device by ID
@router.get("/name/{device_name}", response_model=DeviceOut)
def get_device_by_name(device_name: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_name == device_name).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut.model_validate(device)

@router.get("/{device_id}", response_model=DeviceOut)
def get_device_by_id(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut.model_validate(device)

@router.get("/location/{location_code}", response_model=List[DeviceOut])
def get_devices_by_location(location_code: str):
    """
    Router endpoint to fetch devices at a specific site.
    """
    try:
        devices = api_operation.get_devices_by_location(location_code)
        
        if not devices:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"No devices found for location: {location_code}",
                    "reason": "The query returned an empty result set for this site code",
                    "hint": "Ensure the location code is correct and devices are assigned to it"
                }
            )
        return devices
        
    except HTTPException as http_exc:
        # Re-raise the 404 we just created
        raise http_exc
    except Exception as e:
        # Handle unexpected DB or Server errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error retrieving devices by location",
                "message": str(e)
            }
        )

# GET devices by network
@router.get("/network/{network}", response_model=List[DeviceDetailsOut])
def get_devices_by_network(network: str):
    """
    Retrieves devices filtered by network (e.g., AS209, AS3356, MetRON).
    """
    try:
        # normalize input (important for consistency)
        network = network.upper()

        devices = api_operation.get_devices_by_network(network)

        if not devices:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"No devices found for network: {network}",
                    "reason": "The query returned an empty result set",
                    "hint": "Verify the network value (e.g., AS209, AS3356, MetRON)"
                }
            )

        return devices

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error retrieving devices by network",
                "message": str(e)
            }
        )

# POST create device
@router.post(
    "/",
    response_model=DeviceOut,
    summary="Create a new device"
)
def post_device(data: DeviceIn, db: Session = Depends(get_db)):
    new_device = api_operation.post_device(db, data)
    return DeviceOut.model_validate(new_device)


# PUT update device
@router.put("/{device_id}", response_model=DeviceOut)
def update_device(device_id: str, update: DeviceUpdate):
    try:
        updated_device = api_operation.put_device(device_id, update.dict())
        if not updated_device:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Device not found or update failed",
                    "reason": f"Invalid device_id {device_id} or duplicate field values",
                    "hint": "Verify device_id exists and unique fields are not duplicated"
                }
            )
        return updated_device
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error during device update",
                "message": str(e)
            }
        )

# DELETE device
@router.delete("/{device_id}", response_model=dict)
def delete_device(device_id: str):
    try:
        success = api_operation.delete_device_by_id(device_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Device deletion failed",
                    "reason": f"Device with name {device_id} not found",
                    "hint": "Verify the device_name exists before deletion"
                }
            )
        return {"message": f"Device {device_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error during device deletion",
                "message": str(e)
            }
        )

@router.get("/hardware/", response_model=List[HardwareSpecsOut], summary="List all Hardware Specifications")
def list_hardware_specs(db: Session = Depends(get_db)):
    specs = api_operation.get_hardware_specs(db)
    if not specs:
        raise HTTPException(status_code=404, detail={"error": "No hardware specifications found"})
    return specs

# GET hardware spec by ID
@router.get("/hardware/{hardware_id}", response_model=HardwareSpecsOut, summary="Get a Hardware Specification by ID")
def get_hardware_spec_by_id(hardware_id: UUID, db: Session = Depends(get_db)):
    spec = api_operation.get_hardware_spec_by_id(db, hardware_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Hardware Specification not found")
    return spec

# POST create hardware spec
@router.post("/hardware/", response_model=HardwareSpecsOut, status_code=201, summary="Create a new Hardware Specification")
def create_hardware_spec(data: HardwareSpecsIn, db: Session = Depends(get_db)):
    try:
        new_spec = api_operation.post_hardware_spec(db, data)
        return new_spec
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Data validation failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error creating hardware specification", "message": str(e)})

# PUT update hardware spec
@router.put("/hardware/{hardware_id}", response_model=HardwareSpecsOut, summary="Update Hardware Specification details")
def update_hardware_spec(hardware_id: UUID, update: HardwareSpecsUpdate, db: Session = Depends(get_db)):
    try:
        updated_spec = api_operation.put_hardware_spec(db, hardware_id, update)
        if not updated_spec:
            raise HTTPException(status_code=404, detail="Hardware Specification not found")
        return updated_spec
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Update failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error updating hardware specification", "message": str(e)})

# DELETE hardware spec
@router.delete("/hardware/{hardware_id}", response_model=dict, summary="Delete a Hardware Specification")
def delete_hardware_spec(hardware_id: UUID, db: Session = Depends(get_db)):
    try:
        success = api_operation.delete_hardware_spec_by_id(db, hardware_id)
        if not success:
            raise HTTPException(status_code=404, detail={"error": f"Hardware Specification {hardware_id} not found"})
        return {"message": f"Hardware Specification {hardware_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Deletion failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error deleting hardware specification", "message": str(e)})
    
@router.get("/hardware_docs/", response_model=List[HardwareDocumentOut], summary="List all Hardware Documents")
def list_hardware_documents(db: Session = Depends(get_db)):
    docs = api_operation.get_hardware_documents(db)
    if not docs:
        raise HTTPException(status_code=404, detail={"error": "No hardware documents found"})
    return docs

# GET documents by parent hardware_id
@router.get("/hardware_docs/by-spec/{hardware_id}", response_model=List[HardwareDocumentOut], summary="List Documents by Hardware Spec ID")
def list_docs_by_spec(hardware_id: UUID, db: Session = Depends(get_db)):
    docs = api_operation.get_hardware_documents_by_spec(db, hardware_id)
    if not docs:
        raise HTTPException(status_code=404, detail={"error": f"No documents found for hardware ID {hardware_id}"})
    return docs

# GET hardware document by ID
@router.get("/hardware_docs/{document_id}", response_model=HardwareDocumentOut, summary="Get a Hardware Document by ID")
def get_hardware_document_by_id(document_id: UUID, db: Session = Depends(get_db)):
    doc = api_operation.get_hardware_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Hardware Document not found")
    return doc

# POST create hardware document
@router.post("/hardware_docs/", response_model=HardwareDocumentOut, status_code=201, summary="Create a new Hardware Document")
def create_hardware_document(data: HardwareDocumentIn, db: Session = Depends(get_db)):
    try:
        new_doc = api_operation.post_hardware_document(db, data)
        return new_doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Data validation failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error creating document", "message": str(e)})

# PUT update hardware document
@router.put("/hardware_docs/{document_id}", response_model=HardwareDocumentOut, summary="Update Hardware Document details")
def update_hardware_document(document_id: UUID, update: HardwareDocumentUpdate, db: Session = Depends(get_db)):
    try:
        updated_doc = api_operation.put_hardware_document(db, document_id, update)
        if not updated_doc:
            raise HTTPException(status_code=404, detail="Hardware Document not found")
        return updated_doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Update failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error updating document", "message": str(e)})

# DELETE hardware document
@router.delete("/hardware_docs/{document_id}", response_model=dict, summary="Delete a Hardware Document")
def delete_hardware_document(document_id: UUID, db: Session = Depends(get_db)):
    try:
        success = api_operation.delete_hardware_document_by_id(db, document_id)
        if not success:
            raise HTTPException(status_code=404, detail={"error": f"Hardware Document {document_id} not found"})
        return {"message": f"Hardware Document {document_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error deleting document", "message": str(e)})
    
# GET all LRIC cost models
@router.get("/lric/", response_model=List[LRICCostModelOut], summary="List all LRIC Cost Models")
def list_lric_models(db: Session = Depends(get_db)):
    models = api_operation.get_lric_models(db)
    if not models:
        raise HTTPException(status_code=404, detail={"error": "No LRIC Cost Models found"})
    return models

# GET LRIC cost model by ID
@router.get("/lric/{cost_model_id}", response_model=LRICCostModelOut, summary="Get a LRIC Cost Model by ID")
def get_lric_model_by_id(cost_model_id: UUID, db: Session = Depends(get_db)):
    model = api_operation.get_lric_model_by_id(db, cost_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="LRIC Cost Model not found")
    return model

# POST create LRIC cost model
@router.post("/lric/", response_model=LRICCostModelOut, status_code=201, summary="Create a new LRIC Cost Model")
def create_lric_model(data: LRICCostModelIn, db: Session = Depends(get_db)):
    try:
        new_model = api_operation.post_lric_model(db, data)
        return new_model
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Data validation failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error creating LRIC model", "message": str(e)})

# PUT update LRIC cost model
@router.put("/lric/{cost_model_id}", response_model=LRICCostModelOut, summary="Update LRIC Cost Model details")
def update_lric_model(cost_model_id: UUID, update: LRICCostModelUpdate, db: Session = Depends(get_db)):
    try:
        updated_model = api_operation.put_lric_model(db, cost_model_id, update)
        if not updated_model:
            raise HTTPException(status_code=404, detail="LRIC Cost Model not found")
        return updated_model
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Update failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error updating LRIC model", "message": str(e)})

# DELETE LRIC cost model
@router.delete("/lric/{cost_model_id}", response_model=dict, summary="Delete a LRIC Cost Model")
def delete_lric_model(cost_model_id: UUID, db: Session = Depends(get_db)):
    try:
        success = api_operation.delete_lric_model_by_id(db, cost_model_id)
        if not success:
            raise HTTPException(status_code=404, detail={"error": f"LRIC Cost Model {cost_model_id} not found"})
        return {"message": f"LRIC Cost Model {cost_model_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Deletion failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error deleting LRIC model", "message": str(e)})
    
@router.get("/location/{device_id}", response_model=DeviceLocationOut, summary="Get Location for a specific Device")
def get_device_location(device_id: UUID, db: Session = Depends(get_db)):
    location = api_operation.get_device_location_by_id(db, device_id)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location record not found for device ID {device_id}")
    return location

# POST create a new location record
@router.post("/location/", response_model=DeviceLocationOut, status_code=201, summary="Create new Device Location record")
def create_device_location(data: DeviceLocationIn, db: Session = Depends(get_db)):
    try:
        new_location = api_operation.post_device_location(db, data)
        return new_location
    except ValueError as e:
        # Catches IntegrityError (e.g., trying to create a location for a device that already has one)
        raise HTTPException(status_code=400, detail={"error": "Creation failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error creating location", "message": str(e)})

# PUT update an existing location record
@router.put("/location/{device_id}", response_model=DeviceLocationOut, summary="Update an existing Device Location record")
def update_device_location(device_id: UUID, update: DeviceLocationUpdate, db: Session = Depends(get_db)):
    try:
        updated_location = api_operation.put_device_location(db, device_id, update)
        if not updated_location:
            raise HTTPException(status_code=404, detail="Device Location record not found")
        return updated_location
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Update failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error updating location", "message": str(e)})

# DELETE location record
@router.delete("/location/{device_id}", response_model=dict, summary="Delete a Device Location record")
def delete_device_location(device_id: UUID, db: Session = Depends(get_db)):
    try:
        success = api_operation.delete_device_location_by_id(db, device_id)
        if not success:
            raise HTTPException(status_code=404, detail={"error": f"Location record for device {device_id} not found"})
        return {"message": f"Device Location record for device {device_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Unexpected error deleting location", "message": str(e)})