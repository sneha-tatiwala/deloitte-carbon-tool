# CCTS Advisory Opportunity — Submission Note
**To:** [Partner/Senior Manager Name], Sustainability & Climate Practice, Deloitte India
**From:** Sneha Tatiwala, Boston University (snehaa@bu.edu)
**Date:** April 2026

---

## The Finding

India's CCTS full trading launch is mid-2026. Of the approximately 490 obligated industrial units entering their first compliance period, the majority do not yet have a BEE-approved Monitoring Plan — the prerequisite for receiving or transferring Carbon Credit Certificates. Accredited Carbon Verification Agencies (ACVAs) under ISO 14064 are the bottleneck: India requires an estimated 750+ ACVAs at launch; fewer than 50 currently operate. The window to establish MRV infrastructure before the compliance deadline is narrowing.

This creates a specific advisory opportunity: firms with existing audit infrastructure and sector expertise in cement, steel, and aluminium are positioned to capture the MRV setup market before undifferentiated entrants can scale capacity. Deloitte India's audit practice covers all nine CCTS sectors. The constraint is not capability — it is whether covered entities understand their compliance position clearly enough to act.

## What I Built

A prototype CCTS compliance and policy intelligence tool that addresses this gap directly. It takes a company's sector, annual production, and emission intensity, and returns: compliance status (over/under/at threshold), CCC surplus or deficit in tonnes CO₂e, financial exposure at the three price collar scenarios (₹150/₹250/₹600/tCO₂e), and a sector peer benchmark. A what-if scenario module allows users to model the compliance impact of specific intensity reductions before committing to abatement investment.

The calculation engine is built in Python with 52 unit tests, and mirrors Deloitte India's own CCTS commentary (Inderjeet Singh, 2024) on the compliance mechanics. A Phase 2 statistical analysis of the aggregate cement sector compliance gap is attached separately.

The tool is built to demonstrate what a client-facing prospect conversation tool for Deloitte India's Sustainability & Climate Practice could look like — not as a finished product, but as evidence of what the analytical thinking behind one would require.

## Why This Is Relevant Now

The CCTS compliance period is active. The 490 covered entities will need MRV setup, compliance gap assessment, and CCC procurement or monetisation advisory within the next six to twelve months. The companies that do not yet know whether they are over- or under-compliers are the same ones most in need of the initial conversation. This tool is designed to initiate that conversation.

## The Ask

A 20-minute call to discuss where this fits in Deloitte India's CCTS client engagement approach, and what a student with this research depth could contribute to the practice over a summer.

---

*Attachments: (1) Phase 2 PDF — CCTS Compliance Gap Analysis, India Cement Sector; (2) GitHub repository with calculator.py, test suite, and full methodology.*
