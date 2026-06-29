# Future Roadmap

This document outlines planned future improvements and functional expansions for the AI Resource Management Platform.

---

## 1. Vector Collection Enhancements
- **CRM Pipeline Vectors**: Index Hubspot CRM solution descriptions into Qdrant vector collections. This will support semantic project compatibility lookups for tentative pipeline wins.
- **Skill Taxonomy Mapping**: Implement hierarchy mappings to resolve conceptual subskills (e.g. recognizing that "React" implies "JavaScript" and "Frontend") directly in search similarity scoring.

---

## 2. Interactive Allocations Workflows
- **Write-Back Allocations**: Introduce database mutation endpoints `POST /api/allocations` enabling the frontend to write new assignments directly back to PostgreSQL.
- **Active Conflict Warnings**: Warn staffing managers in real-time if a proposed allocation conflicts with existing active project timelines.

---

## 3. Real-Time Dashboard Feeds
- **Websockets Notifications**: Push immediate alerts to the topbar notifications bells whenever project delay indices exceed thresholds.
- **Dynamic Training Integration**: Suggest skills certification programs to unallocated benched resources matching recurring pipeline deficits.
