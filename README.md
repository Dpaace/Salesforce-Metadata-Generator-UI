# Salesforce Master Data Registration and Metadata Deployment Tool

This project is designed to automate the process of registering master data into Salesforce and dynamically generating and deploying metadata such as custom objects, fields, layouts, tabs, and profile permissions. It provides a complete solution via a web interface backed by a Python Flask API that interacts with Salesforce through REST and Metadata APIs.

---

## Overview

The goal of this tool is to eliminate the manual effort required to set up Salesforce metadata and populate it with structured master data. It supports both standard and custom objects, handles field-level security and layout updates, and allows importing large CSV files efficiently.

This system supports:
- Metadata generation for new custom objects and fields
- Field injection into existing standard Salesforce objects
- Layout merging to reflect new fields
- Profile permission updates for visibility and access
- OAuth 2.0 integration for secure Salesforce API access
- Bulk record upload using composite API from multiple CSVs
- Real-time progress tracking and deployment status feedback

---

## Key Features

### Metadata Generation
- Create new custom objects with defined fields
- Add custom fields to standard Salesforce objects (e.g., Account, Contact)
- Generate layouts that include all defined fields
- Include fields in profiles with full access permissions

### Metadata Deployment
- Deploy generated metadata using Salesforce Metadata API
- Monitor deployment status with polling and real-time updates
- Automatically redirect users upon successful deployment

### Record Upload
- Upload CSV data to multiple objects in a single session
- Support for bulk upload using Salesforce REST API (`/composite/tree`)
- Progress tracking, batch handling, and error reporting
- Modular and extensible design for additional validation or logging

---

## Tech Stack

**Frontend**
- HTML5
- Tailwind CSS
- Vanilla JavaScript

**Backend**
- Python 3.10.0
- Flask Framework

**Salesforce Integration**
- OAuth 2.0 for Authentication
- REST API for record import
- Metadata API for object/field/layout deployment

---

## Directory Structure

## Project Directory Structure

- `app.py` — Main Flask backend application
- `requirements.txt` — Python dependency list
- `retrieve_layout.py` — SOAP-based layout metadata retrieval and field merging for custom object
- `retrieve_standard_layout.py` — SOAP-based layout metadata retrieval and field merging for standard object
- `README.md` — Project documentation

**utils/**
- `generate_metadata.py` — Logic for generating custom object metadata
- `standard_generator.py` — Logic for adding fields to standard Salesforce objects

**templates/**
- `oauth.html` — OAuth login screen
- `redirect.html` — Redirect handler after authentication
- `custom.html` — UI for creating custom metadata
- `standard.html` — UI for injecting fields into standard objects
- `upload.html` — Multi-object CSV uploader
- `deploying.html` — Deployment status and countdown screen
- `select.html` — Main menu to select functionality










