# Network API Overview

Welcome to the **Network API**. This service provides endpoints for managing **Ports** and **Fabric Services** in a modular, reproducible way. It is built with [FastAPI](https://fastapi.tiangolo.com/) and leverages SQLAlchemy for database operations and Pydantic for schema validation.

---

## ✨ Features

- **Ports Management**
  - Create, read, update, and delete network ports
  - Symmetric CRUD endpoints for onboarding clarity
- **Fabric Services**
  - Manage fabric service definitions
  - Full lifecycle operations (create, list, update, delete)
- **Static Documentation**
  - Markdown files rendered as HTML via `/docs/{page_name}`
  - Acts as a static site generator for API onboarding


## 📚 Endpoints Summary

### Ports
- `GET /ports/` → List all ports
- `POST /ports/` → Create a new port
- `PUT /ports/{port_id}` → Update an existing port
- `DELETE /ports/{port_id}` → Delete a port by ID

### Fabric Services
- `GET /fabric_services/` → List all fabric services
- `POST /fabric_services/` → Create a new fabric service
- `PUT /fabric_services/{service_id}` → Update an existing fabric service
- `DELETE /fabric_services/{service_id}` → Delete a fabric service by ID

---

## ⚙️ Usage Examples

### Create a Fabric Service
```http
POST /fabric_services/
Content-Type: application/json

{
  "name": "ServiceA",
  "description": "Core fabric service"
}

[View Device API Design](/md/api_design/customer)

[View ports API Design](/md/api_design/device)

[View network Links API Design](/md/api_design/network_link)

[View hardware API Design](/md/api_design/hardware)

[View port Optics API Design](/md/api_design/port_optic)

[View Customer API Design](/md/api_design/customer)

[View Fabric Service API Design](/md/api_design/fabric_service)

[View Fabric Connection API Design](/md/api_design/fabric_connction)

[View Route Target API Design](/md/api_design/route_target)

[View LRIC API Design](/md/api_design/lric)

[View Patch Panels and Cross Connects API Design](/md/api_design/patch_panel)

[View topology API Design](/md/api_design/topology)

[View Materials and BOMs API Design](/md/api_design/materials_bom)
