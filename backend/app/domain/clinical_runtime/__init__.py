# app/domain/clinical_runtime/__init__.py
"""
Production clinical runtime pipeline (HNP -> Evidence -> Ontology -> Functional
Assessment -> Terminal Status -> Recertification).

This package is being built incrementally, one bounded/reviewable commit at a
time, per the Production Runtime Integration Directive. Do not treat the mere
existence of a module here as proof that a pipeline stage is connected to a
production call path -- only an executable integration/E2E test proves that.

Implemented so far:
    - contracts: shared typed data contracts (Commit 1)

Not yet implemented (tracked, not silently assumed complete):
    - Evidence Harvester production service (Commit 2)
    - Ontology Runtime service (Commit 3)
    - Functional Assessment Service (PPS/KPS/NYHA/ECOG/FAST/ADL) (Commit 4)
    - Terminal Status runtime (Commit 5)
    - Recertification runtime (Commit 6)
    - HNP orchestration + persistence (Commit 7)
    - Observability, feature flags, operational controls (Commit 8)
    - Integration / E2E / release validation (Commit 9)
"""
