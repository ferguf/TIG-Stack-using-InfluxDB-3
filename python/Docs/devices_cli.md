Network Device Management CLI (main.py)

This document summarizes the capabilities and dependencies of the Network Device Management Command Line Interface (CLI), which is built on the main.py script. This tool provides comprehensive CRUD (Create, Read, Update, Delete) functionality for managing network devices and their associated hardware components within a PostgreSQL database.

1. Capabilities Overview

The CLI offers two primary sets of commands: Device Management and Hardware Component Management, alongside a utility command for bulk data ingestion.

Command

Category

Function

Description

c

Device CRUD

Create

Creates a new device record. Automatically applies defaults (Vendor: Juniper, Model: MX10004, Status: Planned, Health: 1) if the device role is inferred as VAR.

r

Device CRUD

Read

Lists all devices currently stored in the devices table.

u

Device CRUD

Update

Allows modification of any field for an existing device, selected either by index or name. Includes validation for Status and Lifecycle fields.

d

Device CRUD

Delete

Permanently removes a device record by name.

hc

Hardware CRUD

Create

Adds a new hardware component (e.g., Linecard, PSU, Fan) and links it to an existing device.

hr

Hardware CRUD

Read

Lists all hardware components associated with a specific device name.

hu

Hardware CRUD

Update

Modifies the details of an existing hardware component, identified by its unique Serial Number.

hd

Hardware CRUD

Delete

Permanently removes a hardware component, identified by its unique Serial Number.

lb

Utility

Bulk Load

Loads device data from a specified CSV file (add_devices.csv) into the database. It skips any devices whose device_name already exists.

h

Utility

Help

Displays the command menu.

q

Utility

Quit

Exits the CLI application.

2. Key Features

Role-Based Defaults for Creation

When creating a new device, the CLI attempts to parse the Device Name (e.g., VAR.1.DEN1) to determine the device_role. If the role is identified as VAR, the following default values are automatically populated, reducing manual entry:

Vendor: Juniper

Model: MX10004

Availability Zone: Zone 0

Lifecycle Status: Growth

Device Status: Planned

Health: 1 (Good)

Robust Data Validation

The application enforces strong data integrity checks for specific fields:

Field

Allowed Options

Validation Behavior

Device Status

Planned, Active, Capped

Creation/Update is aborted if an invalid status is entered.

Lifecycle Status

Growth, Cap Growth, Cap provisioning, Remove

Creation/Update is aborted if an invalid lifecycle status is entered.

Hardware Health

Healthy, Warning, Critical, Decommissioned

Hardware creation/update is aborted if an invalid status is entered.

Indexed Selection

For update (u) and delete (d) operations, the CLI first lists available devices with an index number, allowing the user to select the target device either by entering the full Device Name or the corresponding index.

3. Dependencies and Structure

The CLI is structured into multiple Python files to maintain clear separation of concerns:

Module Name

Purpose

Key Imports

main.py

The main CLI application. Contains the interactive loop, command handlers (handle_create, handle_update, etc.), and input validation logic.

device_operations (as db), bulk_load_device

device_operations.py

Database Interaction Layer (DB). Contains all functions that directly execute SQL against the PostgreSQL database (e.g., create_device, get_all_devices, update_hardware_component).

port_config, psycopg2

bulk_load_device.py

Bulk Data Logic. Handles reading, validating, and batch-inserting data from the add_devices.csv file into the database.

port_config, csv, psycopg2

port_config.py

Configuration and Connection. Manages the connection settings (e.g., connection string), and provides utilities for establishing, closing, and handling errors for the database connection.

psycopg2

External Python Libraries

psycopg2: Required for connecting to and interacting with the PostgreSQL database.

csv: Used by bulk_load_device.py to read and process CSV files for bulk ingestion.

Database Schema

The CLI is designed to interact with at least two PostgreSQL tables (managed by device_operations.py):

devices: Stores core network device information (Name, Role, Status, Health, etc.).

device_hardware: Stores components associated with a device (Serial Number, Component Type, Health Status, etc.).