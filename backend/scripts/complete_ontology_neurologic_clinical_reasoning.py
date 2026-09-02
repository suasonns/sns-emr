# scripts/complete_ontology_neurologic_clinical_reasoning.py
"""
Neurologic Clinical-Reasoning Ontology Completion.

Builds the universal Tier 4 (OntologyDiseaseVariant) / Tier 5
applicability (OntologyConceptVariantApplicability) knowledge layer on
top of the already-merged Neurologic Phase 2 baseline (PR #34, #35), for
the six approved Neurologic diseases:

    Stroke
    Hemiplegia
    Hemiparesis
    Contracture
    Dementia Due To Alzheimer's Disease
    Senile Degeneration of Brain

This script does NOT redesign the disease hierarchy, does NOT create a
new canonical disease, and does NOT modify any Tier 1-3 row (body
system / disease family / disease). It adds:

    Tier 4 -- OntologyDiseaseVariant rows: mechanism, hemisphere,
        dominance, laterality, cortical location, vascular territory,
        deep/subcortical structure, brainstem level, cerebellar
        location, disease phase, residual-deficit state, severity
        class, and physiological-phenotype (consciousness) variants,
        recursively nested via parent_variant_id where the manifest
        specifies a sub-classification (e.g. Cardioembolic Stroke is a
        child of Embolic Stroke, which is a child of Ischemic Stroke).

    Tier 5 -- new atomic OntologyDiseaseSymptom / OntologyDiseaseFinding
        / OntologyDiseaseComplication rows for localization-specific
        concepts the Phase 2 baseline did not yet carry (e.g. Abulia,
        Astereognosis, Cranial-Nerve Deficit, Vasospasm), inserted with
        the SAME idempotent _populate_simple_domain helper already used
        by expand_ontology_phase2_neurologic.py (imported, not
        duplicated).

    Applicability -- OntologyConceptVariantApplicability edges linking
        each Tier 5 concept (existing Phase 2 rows AND the new rows
        above) to the Tier 4 variant(s) it clinically supports, using
        only the ten already-approved applicability_type values
        (APPLIES_TO, EXPECTED_WITH, STRONGLY_ASSOCIATED_WITH,
        MAY_OCCUR_WITH, SUPPORTS_DIFFERENTIATION, CONTRAINDICATED_FOR,
        TREATMENT_SPECIFIC_TO, PROGNOSTIC_FOR, END_STAGE_SUPPORT_FOR,
        HOSPICE_SUPPORT_FOR). The manifest's generic "X MAY_BE_
        ASSOCIATED_WITH Y" pattern between a Tier 4 variant and a Tier 5
        concept is expressed as MAY_OCCUR_WITH; differentiation-only
        knowledge (dementia-pattern review, Hemiplegia-vs-Hemiparesis,
        Senile Degeneration of Brain vs. Alzheimer's) is expressed as
        SUPPORTS_DIFFERENTIATION; negative/exclusionary knowledge
        (hemorrhagic Stroke must never receive thrombolysis) is
        expressed as CONTRAINDICATED_FOR; poor-prognosis volume/imaging
        findings are expressed as PROGNOSTIC_FOR; disease-specific
        treatment stratification (e.g. mechanical thrombectomy is
        specific to large-vessel ischemic occlusion) is expressed as
        TREATMENT_SPECIFIC_TO.

No new relationship_type is invented on OntologyRelationship anywhere in
this script -- only the already-committed/persisted vocabulary
(MAY_CAUSE, MAY_CONTRIBUTE_TO) is reused, and only for genuine
disease-to-disease edges, never for variant/concept associations (those
use the applicability table, per the approved schema).

Every new Tier 4 variant AND every new/existing Tier 5 concept receives
an OntologyEvidenceRule row (Tier 4 rows use concept_type=
"DISEASE_VARIANT"; Tier 5 rows reuse the existing evidence-rule
population already defined in expand_ontology_phase2_neurologic.py,
which is idempotent and safe to call again here). patient_fact_requires_
evidence is always True.

Idempotent throughout: every system/family/disease/variant/concept row
is resolved by stable normalized name (never a hardcoded UUID);
re-running this script inserts nothing new; nothing is ever hard-deleted;
no other body system, disease, or patient/staff table is touched.

Run with: .\\.venv\\Scripts\\python.exe scripts\\complete_ontology_neurologic_clinical_reasoning.py
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

# See expand_ontology_phase2_neurologic.py for why this explicit import is
# needed before any query touches the full ORM mapper registry.
import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyConceptVariantApplicability,
    OntologyDisease,
    OntologyDiseaseFamily,
    OntologyDiseaseValidationResult,
    OntologyDiseaseVariant,
    OntologyEvidenceRule,
)

# Reuse the already-committed Phase 2 module for disease-name constants,
# the CONCEPT_DOMAINS registry, the generic simple-domain populate helper,
# and the evidence-rule populator -- never duplicated here.
from scripts.expand_ontology_phase2_neurologic import (
    ALZ,
    CONCEPT_DOMAINS,
    CONTRACTURE,
    HEMIPARESIS,
    HEMIPLEGIA,
    SDB,
    STROKE,
    _populate_simple_domain,
    populate_evidence_rules,
)

ALL_DISEASE_NAMES = [STROKE, HEMIPLEGIA, HEMIPARESIS, CONTRACTURE, ALZ, SDB]

CONCEPT_TYPE_MODEL_MAP: Dict[str, Tuple[type, str]] = {
    concept_type: (model_cls, name_attr) for model_cls, concept_type, name_attr, _req in CONCEPT_DOMAINS
}


# ---------------------------------------------------------------------------
# NEW TIER 5 ATOMIC CONCEPTS -- localization-specific symptoms, findings, and
# complications the Phase 2 baseline did not yet carry. Reuses the same
# _populate_simple_domain helper and unique-constraint semantics as Phase 2 --
# a name already present for a disease is left unchanged, never duplicated.
# ---------------------------------------------------------------------------

# (symptom_name, description, hospice_relevance, severity_scale)
NEW_SYMPTOMS: Dict[str, List[Tuple[str, str, str, str]]] = {
    STROKE: [
        ("Memory Impairment", "Difficulty forming or recalling new information following the stroke.",
         "Contributes to safety risk and care-planning complexity.", "Mild-Moderate"),
        ("Impaired Executive Function", "Reduced ability to plan, organize, or reason through tasks.",
         "Limits independent decision-making capacity.", "Moderate"),
        ("Impaired Judgment", "Reduced insight into risk or consequence of actions.",
         "Raises safety-supervision needs.", "Moderate"),
        ("Abulia", "Reduced spontaneous initiation of speech, movement, or thought.",
         "Associated with frontal-lobe and anterior-circulation involvement.", "Moderate"),
        ("Apathy", "Diminished motivation or emotional responsiveness.",
         "May be mistaken for depression; affects rehabilitation participation.", "Mild-Moderate"),
        ("Behavioral Disinhibition", "Socially inappropriate or impulsive behavior.",
         "Associated with frontal-lobe involvement; increases caregiver burden.", "Moderate"),
        ("Personality or Behavioral Change", "Change from the patient's prior baseline temperament or conduct.",
         "Reported by family; supports frontal-lobe localization review.", "Mild-Moderate"),
        ("Impaired Attention", "Reduced ability to sustain or direct focus.",
         "Complicates assessment and rehabilitation participation.", "Mild-Moderate"),
        ("Urinary Incontinence", "New loss of bladder control following the stroke.",
         "Associated with anterior cerebral artery and large-territory involvement.", "Moderate"),
        ("Astereognosis", "Inability to identify an object by touch alone.",
         "Supports parietal-lobe localization review.", "Mild"),
        ("Agraphesthesia", "Inability to identify a shape traced on the skin.",
         "Supports parietal-lobe localization review.", "Mild"),
        ("Apraxia", "Loss of ability to perform previously learned skilled movements despite intact strength.",
         "Supports parietal-lobe/dominant-hemisphere localization review.", "Moderate"),
        ("Anosognosia", "Lack of awareness of one's own deficit.",
         "Associated with non-dominant-parietal involvement; increases safety risk.", "Moderate"),
        ("Left-Right Disorientation", "Difficulty distinguishing left from right on command.",
         "Supports dominant-parietal localization review.", "Mild"),
        ("Acalculia", "Acquired difficulty performing calculations.",
         "Supports dominant-parietal localization review.", "Mild"),
        ("Agraphia", "Acquired difficulty writing.",
         "Supports dominant-parietal localization review.", "Mild-Moderate"),
        ("Visual Agnosia", "Inability to recognize visually presented objects despite intact vision.",
         "Supports occipital-lobe localization review.", "Moderate"),
        ("Visual Hallucination", "Perceiving visual images that are not present.",
         "Supports occipital-lobe/posterior-cerebral-artery localization review.", "Mild-Moderate"),
        ("Autonomic Instability", "Fluctuation in heart rate, blood pressure, or temperature regulation.",
         "Associated with insular and brainstem involvement.", "Moderate-Severe"),
        ("Altered Taste", "New change in taste perception.",
         "Supports insular localization review.", "Mild"),
        ("Nystagmus", "Involuntary rhythmic eye movement.",
         "Supports vertebrobasilar/cerebellar/brainstem localization review.", "Mild-Moderate"),
        ("Cranial-Nerve Deficit", "New deficit in one or more cranial nerve distributions.",
         "Supports brainstem localization review.", "Moderate"),
        ("Quadriparesis", "Weakness involving all four limbs.",
         "Associated with bilateral brainstem (basilar-territory) involvement; poor-prognosis indicator.",
         "Severe"),
        ("Quadriplegia", "Complete paralysis involving all four limbs.",
         "Associated with bilateral brainstem (basilar-territory) involvement; poor-prognosis indicator.",
         "Severe"),
        ("Central Post-Stroke Pain", "Chronic pain syndrome following a thalamic or central lesion.",
         "Supports thalamic localization review; significant symptom-burden driver.", "Moderate-Severe"),
        ("Thunderclap Headache", "Abrupt, maximal-intensity headache at onset.",
         "Classic presentation of subarachnoid hemorrhage.", "Severe"),
        ("Neck Stiffness", "Resistance to passive neck flexion.",
         "Supports subarachnoid hemorrhage (meningeal irritation) review.", "Moderate"),
        ("Photophobia", "Discomfort in bright light.",
         "Supports subarachnoid hemorrhage (meningeal irritation) review.", "Mild-Moderate"),
    ],
    ALZ: [
        ("Loss of Meaningful Verbal Communication", "Progressive decline to loss of purposeful, comprehensible "
         "speech.", "Core FAST Stage 7 / advanced-disease marker.", "Severe"),
    ],
    CONTRACTURE: [
        ("Painful Muscle Spasm", "Involuntary, painful muscle contraction associated with spasticity-driven "
         "contracture.", "Distinct from generalized positioning discomfort; specifically reflects a "
         "spasticity-etiology mechanism.", "Moderate"),
    ],
    SDB: [
        ("Communication Decline", "Progressive, non-focal decline in expressive or receptive communication.",
         "Supports general-decline assessment distinct from Alzheimer's-specific language staging.",
         "Moderate-Severe"),
        ("Continence Decline", "Progressive loss of bladder or bowel control as part of generalized decline.",
         "Supports general-decline/end-stage assessment.", "Moderate-Severe"),
    ],
}

# (finding_name, finding_description)
NEW_FINDINGS: Dict[str, List[Tuple[str, str]]] = {
    STROKE: [
        ("Contralateral Motor Weakness", "Weakness on the side of the body opposite the cerebral lesion."),
        ("Contralateral Sensory Loss", "Diminished sensation on the side of the body opposite the cerebral "
         "lesion."),
        ("Gaze Preference Toward Lesion", "Conjugate eye deviation toward the side of a large cerebral lesion."),
        ("Pure Motor Hemiparesis", "Isolated motor deficit without sensory, visual, or cognitive findings, "
         "classic for a lacunar internal-capsule/pontine lesion."),
        ("Pure Sensory Deficit", "Isolated sensory deficit without motor findings, classic for a lacunar "
         "thalamic lesion."),
        ("Cortical Sensory Deficit", "Impaired higher-order sensory discrimination (e.g. two-point "
         "discrimination) with preserved primary sensation, localizing to cortex."),
        ("Constructional Apraxia", "Impaired ability to draw or construct simple figures on exam, associated "
         "with non-dominant-parietal involvement."),
        ("Finger Agnosia", "Inability to identify individual fingers on command, part of the dominant-parietal "
         "(Gerstmann) constellation."),
        ("Cortical Blindness", "Bilateral visual loss with preserved pupillary light reflex, localizing to "
         "bilateral occipital cortex."),
        ("Ptosis", "Drooping of the upper eyelid, associated with oculomotor-nerve (midbrain) involvement."),
        ("Impaired Horizontal Gaze", "Reduced or absent voluntary horizontal eye movement, associated with "
         "pontine involvement."),
        ("Vertical-Gaze Abnormality", "Impaired voluntary vertical eye movement, associated with midbrain "
         "involvement."),
        ("Truncal Ataxia", "Instability of trunk control on exam, localizing to cerebellar vermis involvement."),
        ("Dysmetria", "Overshoot or undershoot on finger-to-nose/heel-to-shin testing, localizing to "
         "cerebellar hemisphere involvement."),
        ("Cerebral Edema", "Swelling of brain tissue on imaging surrounding an infarct or hemorrhage."),
        ("Midline Shift", "Displacement of midline brain structures on imaging, indicating mass effect."),
        ("Intraventricular Extension", "Extension of hemorrhage into the ventricular system on imaging."),
    ],
}

# (complication_name, description, common_occurrence, clinical_significance)
NEW_COMPLICATIONS: Dict[str, List[Tuple[str, str, str, str]]] = {
    STROKE: [
        ("Vasospasm", "Delayed narrowing of cerebral vessels following subarachnoid hemorrhage.",
         "Common", "Risk of secondary ischemic injury; requires monitoring after subarachnoid hemorrhage."),
        ("Delayed Cerebral Ischemia", "New ischemic injury occurring days after subarachnoid hemorrhage, "
         "often related to vasospasm.", "Common", "Major driver of secondary morbidity after subarachnoid "
         "hemorrhage."),
        ("Rebleeding", "Recurrent hemorrhage from an unsecured aneurysmal source.",
         "Uncommon", "High-mortality complication prior to aneurysm-securing intervention."),
        ("Obstructive Hydrocephalus", "CSF-outflow obstruction from mass effect or intraventricular blood.",
         "Common in cerebellar/intraventricular hemorrhage", "May require urgent ventricular drainage; "
         "informs shunt-candidacy discussion."),
        ("Herniation", "Displacement of brain tissue due to elevated intracranial pressure or mass effect.",
         "Uncommon but life-threatening", "Represents a terminal-trajectory complication in large-territory "
         "or hemorrhagic stroke."),
    ],
}


# ---------------------------------------------------------------------------
# TIER 4: DISEASE VARIANTS
# (disease_name, variant_name, variant_dimension, parent_variant_name_or_None,
#  description)
# Processed in the order below -- a parent variant is always defined before
# any child that references it via parent_variant_name.
# ---------------------------------------------------------------------------
VariantDef = Tuple[str, str, str, Optional[str], str]

VARIANT_DEFS: List[VariantDef] = [
    # --- STROKE: MECHANISM ---------------------------------------------
    (STROKE, "Ischemic Stroke", "MECHANISM", None,
     "Cerebral infarction from arterial occlusion (thrombotic, embolic, or small-vessel)."),
    (STROKE, "Thrombotic Stroke", "MECHANISM", "Ischemic Stroke",
     "In-situ arterial thrombosis, often atherosclerosis-related."),
    (STROKE, "Embolic Stroke", "MECHANISM", "Ischemic Stroke",
     "Distal arterial occlusion by an embolus originating elsewhere."),
    (STROKE, "Cardioembolic Stroke", "MECHANISM", "Embolic Stroke",
     "Embolic stroke with a cardiac embolic source (e.g. atrial fibrillation, valvular disease)."),
    (STROKE, "Large-Artery Atherosclerotic Stroke", "MECHANISM", "Ischemic Stroke",
     "Ischemic stroke from atherosclerotic large-artery stenosis or occlusion."),
    (STROKE, "Small-Vessel Occlusive Stroke", "MECHANISM", "Ischemic Stroke",
     "Ischemic stroke from occlusion of a small penetrating artery."),
    (STROKE, "Lacunar Stroke", "MECHANISM", "Small-Vessel Occlusive Stroke",
     "Small subcortical infarct from small-vessel occlusion producing a recognized lacunar syndrome."),
    (STROKE, "Cryptogenic Stroke", "MECHANISM", "Ischemic Stroke",
     "Ischemic stroke with no identified mechanism despite standard evaluation."),
    (STROKE, "Hemorrhagic Stroke", "MECHANISM", None,
     "Bleeding into or around brain tissue; must remain clinically distinct from ischemic stroke, including "
     "for treatment purposes (thrombolysis is never appropriate for hemorrhagic stroke)."),
    (STROKE, "Intracerebral Hemorrhage", "MECHANISM", "Hemorrhagic Stroke",
     "Bleeding within brain parenchyma."),
    (STROKE, "Subarachnoid Hemorrhage", "MECHANISM", "Hemorrhagic Stroke",
     "Bleeding into the subarachnoid space, commonly aneurysmal."),
    (STROKE, "Hemorrhagic Transformation", "MECHANISM", "Hemorrhagic Stroke",
     "Secondary hemorrhage into a previously ischemic infarct."),

    # --- STROKE: HEMISPHERE / DOMINANCE / LATERALITY --------------------
    (STROKE, "Left-Hemisphere Stroke", "HEMISPHERE", None,
     "Stroke involving the left cerebral hemisphere."),
    (STROKE, "Right-Hemisphere Stroke", "HEMISPHERE", None,
     "Stroke involving the right cerebral hemisphere."),
    (STROKE, "Bilateral Cerebral Stroke", "HEMISPHERE", None,
     "Stroke involving both cerebral hemispheres."),
    (STROKE, "Dominant-Hemisphere Stroke", "DOMINANCE", None,
     "Stroke involving the hemisphere that is language-dominant for this patient (not assumed from "
     "laterality alone -- requires documented dominance)."),
    (STROKE, "Non-Dominant-Hemisphere Stroke", "DOMINANCE", None,
     "Stroke involving the hemisphere that is not language-dominant for this patient."),
    (STROKE, "Left-Sided Neurologic Deficit", "LATERALITY", None,
     "Neurologic deficit affecting the left side of the body."),
    (STROKE, "Right-Sided Neurologic Deficit", "LATERALITY", None,
     "Neurologic deficit affecting the right side of the body."),

    # --- STROKE: CEREBRAL LOBE (CORTICAL_LOCATION) ----------------------
    (STROKE, "Frontal-Lobe Stroke", "CORTICAL_LOCATION", None,
     "Stroke involving the frontal lobe."),
    (STROKE, "Temporal-Lobe Stroke", "CORTICAL_LOCATION", None,
     "Stroke involving the temporal lobe."),
    (STROKE, "Parietal-Lobe Stroke", "CORTICAL_LOCATION", None,
     "Stroke involving the parietal lobe."),
    (STROKE, "Dominant-Parietal Stroke", "CORTICAL_LOCATION", "Parietal-Lobe Stroke",
     "Parietal-lobe stroke involving the language-dominant hemisphere."),
    (STROKE, "Non-Dominant-Parietal Stroke", "CORTICAL_LOCATION", "Parietal-Lobe Stroke",
     "Parietal-lobe stroke involving the non-language-dominant hemisphere."),
    (STROKE, "Occipital-Lobe Stroke", "CORTICAL_LOCATION", None,
     "Stroke involving the occipital lobe."),
    (STROKE, "Insular Stroke", "CORTICAL_LOCATION", None,
     "Stroke involving the insular cortex."),

    # --- STROKE: VASCULAR TERRITORY --------------------------------------
    (STROKE, "Anterior Cerebral Artery Stroke", "VASCULAR_TERRITORY", None,
     "Stroke in the anterior cerebral artery territory."),
    (STROKE, "Middle Cerebral Artery Stroke", "VASCULAR_TERRITORY", None,
     "Stroke in the middle cerebral artery territory."),
    (STROKE, "Large MCA Stroke", "SEVERITY_CLASS", "Middle Cerebral Artery Stroke",
     "Large-volume middle cerebral artery territory infarct with substantial mass-effect risk."),
    (STROKE, "Posterior Cerebral Artery Stroke", "VASCULAR_TERRITORY", None,
     "Stroke in the posterior cerebral artery territory."),
    (STROKE, "Internal Carotid Artery Stroke", "VASCULAR_TERRITORY", None,
     "Stroke from internal carotid artery occlusion, typically producing a large anterior-circulation "
     "deficit."),
    (STROKE, "Vertebral Artery Stroke", "VASCULAR_TERRITORY", None,
     "Stroke in the vertebral artery territory."),
    (STROKE, "Basilar Artery Stroke", "VASCULAR_TERRITORY", None,
     "Stroke in the basilar artery territory, high risk for bilateral brainstem deficit and coma."),
    (STROKE, "Anterior Circulation Stroke", "VASCULAR_TERRITORY", None,
     "Stroke in the carotid/MCA/ACA distribution."),
    (STROKE, "Posterior Circulation Stroke", "VASCULAR_TERRITORY", None,
     "Stroke in the vertebrobasilar/PCA distribution."),
    (STROKE, "Vertebrobasilar Stroke", "VASCULAR_TERRITORY", "Posterior Circulation Stroke",
     "Stroke involving the vertebrobasilar system specifically."),

    # --- STROKE: DEEP / SUBCORTICAL --------------------------------------
    (STROKE, "Internal Capsule Stroke", "SUBCORTICAL_LOCATION", None,
     "Stroke involving the internal capsule, classically producing pure motor hemiparesis."),
    (STROKE, "Thalamic Stroke", "DEEP_STRUCTURE", None,
     "Stroke involving the thalamus, classically producing pure sensory deficit."),
    (STROKE, "Basal Ganglia Stroke", "DEEP_STRUCTURE", None,
     "Stroke involving the basal ganglia."),
    (STROKE, "Caudate Stroke", "DEEP_STRUCTURE", "Basal Ganglia Stroke",
     "Stroke involving the caudate nucleus."),
    (STROKE, "Putaminal Hemorrhage", "DEEP_STRUCTURE", "Intracerebral Hemorrhage",
     "Intracerebral hemorrhage centered in the putamen, the most common site of hypertensive hemorrhage."),
    (STROKE, "Thalamic Hemorrhage", "DEEP_STRUCTURE", "Intracerebral Hemorrhage",
     "Intracerebral hemorrhage centered in the thalamus."),
    (STROKE, "Lobar Hemorrhage", "ANATOMICAL_LOCATION", "Intracerebral Hemorrhage",
     "Intracerebral hemorrhage centered in cortical/subcortical lobar white matter, associated with "
     "amyloid angiopathy in older adults."),

    # --- STROKE: BRAINSTEM ------------------------------------------------
    (STROKE, "Brainstem Stroke", "BRAINSTEM_LEVEL", None,
     "Stroke involving the brainstem, high risk for consciousness/respiratory/autonomic compromise."),
    (STROKE, "Midbrain Stroke", "BRAINSTEM_LEVEL", "Brainstem Stroke",
     "Stroke involving the midbrain."),
    (STROKE, "Pontine Stroke", "BRAINSTEM_LEVEL", "Brainstem Stroke",
     "Stroke involving the pons."),
    (STROKE, "Medullary Stroke", "BRAINSTEM_LEVEL", "Brainstem Stroke",
     "Stroke involving the medulla."),

    # --- STROKE: CEREBELLAR ------------------------------------------------
    (STROKE, "Cerebellar Stroke", "CEREBELLAR_LOCATION", None,
     "Stroke involving the cerebellum, risk of mass effect and obstructive hydrocephalus."),
    (STROKE, "Cerebellar-Hemisphere Stroke", "CEREBELLAR_LOCATION", "Cerebellar Stroke",
     "Stroke involving a cerebellar hemisphere, classically producing limb ataxia."),
    (STROKE, "Cerebellar-Vermis Stroke", "CEREBELLAR_LOCATION", "Cerebellar Stroke",
     "Stroke involving the cerebellar vermis, classically producing truncal ataxia."),

    # --- STROKE: SEVERITY / MULTIFOCAL STATE ------------------------------
    (STROKE, "Large-Territory Stroke", "SEVERITY_CLASS", None,
     "Stroke involving a large volume of brain tissue, associated with edema/herniation risk."),
    (STROKE, "Malignant Cerebral Infarction", "SEVERITY_CLASS", "Large-Territory Stroke",
     "Large-territory infarct with life-threatening edema and herniation risk."),
    (STROKE, "Large Anterior Infarction", "SEVERITY_CLASS", "Large-Territory Stroke",
     "Large-volume infarction in the anterior circulation."),
    (STROKE, "Bihemispheric Infarction", "SEVERITY_CLASS", None,
     "Infarction involving both cerebral hemispheres."),
    (STROKE, "Multiple Cerebral Infarctions", "SEVERITY_CLASS", None,
     "More than one discrete infarct, whether synchronous or from recurrent events."),

    # --- STROKE: DISEASE PHASE ---------------------------------------------
    (STROKE, "Acute Stroke", "DISEASE_PHASE", None,
     "Stroke within the initial evolving clinical window."),
    (STROKE, "Evolving Stroke", "DISEASE_PHASE", None,
     "Stroke with a clinical deficit still progressing."),
    (STROKE, "Established Stroke", "DISEASE_PHASE", None,
     "Stroke with a stable, no-longer-evolving deficit."),
    (STROKE, "Historical Stroke", "DISEASE_PHASE", None,
     "A prior stroke event, documented in history; does not by itself establish that any given deficit is "
     "currently active."),
    (STROKE, "Recurrent Stroke", "DISEASE_PHASE", None,
     "A new stroke event in a patient with a prior stroke history."),

    # --- STROKE: RESIDUAL DEFICIT STATE -------------------------------------
    (STROKE, "Residual Deficit Following Stroke", "RESIDUAL_DEFICIT_STATE", None,
     "Persistent neurologic impairment remaining after the acute event."),
    (STROKE, "Resolved Deficit", "RESIDUAL_DEFICIT_STATE", None,
     "A previously present deficit that has since resolved."),
    (STROKE, "Progressive Neurologic Decline", "RESIDUAL_DEFICIT_STATE", None,
     "Ongoing decline in neurologic status not explained by a single acute event."),

    # --- STROKE: CONSCIOUSNESS / PHYSIOLOGICAL PHENOTYPE ---------------------
    (STROKE, "Coma", "PHYSIOLOGICAL_PHENOTYPE", None,
     "Unresponsive state with absent verbal, eye-opening, and purposeful motor response."),
    (STROKE, "Persistent Coma", "PHYSIOLOGICAL_PHENOTYPE", "Coma",
     "Coma persisting beyond the acute period."),
    (STROKE, "Minimally Conscious State", "PHYSIOLOGICAL_PHENOTYPE", None,
     "Severely altered consciousness with minimal but definite evidence of awareness."),
    (STROKE, "Vegetative State", "PHYSIOLOGICAL_PHENOTYPE", None,
     "Wakefulness without behavioral evidence of awareness."),
    (STROKE, "Persistent Vegetative State", "PHYSIOLOGICAL_PHENOTYPE", "Vegetative State",
     "Vegetative state persisting beyond the acute period."),
    (STROKE, "Locked-In Syndrome", "PHYSIOLOGICAL_PHENOTYPE", None,
     "Preserved consciousness with quadriplegia and anarthria from ventral pontine involvement; must never "
     "be treated as coma."),

    # --- DEMENTIA PATTERN DIFFERENTIATION (attached to Alzheimer's disease
    #     for differential-review purposes only; none of these create a new
    #     canonical disease row) ------------------------------------------
    (ALZ, "Alzheimer's Pattern", "PATHOLOGICAL_SUBTYPE", None,
     "Insidious onset, progressive episodic-memory-led multidomain decline, progressing through FAST "
     "stages; the pattern this disease represents."),
    (ALZ, "Vascular-Pattern Review", "PATHOLOGICAL_SUBTYPE", None,
     "Stepwise decline with focal neurologic deficits and imaging evidence of vascular disease -- a "
     "differential pattern to review against, not a diagnosis this ontology asserts."),
    (ALZ, "Lewy-Body-Pattern Review", "PATHOLOGICAL_SUBTYPE", None,
     "Fluctuating cognition, recurrent visual hallucinations, REM-sleep behavior symptoms, spontaneous "
     "parkinsonism, and neuroleptic sensitivity -- a differential pattern to review against."),
    (ALZ, "Frontotemporal-Pattern Review", "PATHOLOGICAL_SUBTYPE", None,
     "Early behavioral disinhibition, apathy, loss of empathy, compulsive behavior, and early language "
     "impairment with relatively preserved early episodic memory -- a differential pattern to review "
     "against."),
    (ALZ, "Delirium Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Acute onset, fluctuating course, impaired attention, and a possible reversible precipitant -- must be "
     "differentiated from a progressive dementia pattern before any dementia-specific conclusion is drawn."),

    # --- SENILE DEGENERATION OF BRAIN DIFFERENTIATION ------------------------
    (SDB, "General Decline Pattern", "PATHOLOGICAL_SUBTYPE", None,
     "Generalized, non-focal cognitive and functional decline not attributed to a specific named dementia "
     "etiology; the pattern this disease represents."),
    (SDB, "Alzheimer's Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from Alzheimer's disease; Alzheimer-specific "
     "FAST staging and hospice criteria are never automatically applied to Senile Degeneration of Brain."),
    (SDB, "Vascular Dementia Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from a stepwise, infarct-driven vascular "
     "dementia pattern."),
    (SDB, "Mixed Dementia Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from a documented mixed-etiology dementia."),
    (SDB, "Lewy Body Dementia Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from a Lewy-body pattern (fluctuating "
     "cognition, hallucinations, spontaneous parkinsonism)."),
    (SDB, "Frontotemporal Dementia Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from an early-behavioral-change "
     "frontotemporal pattern."),
    (SDB, "Delirium Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from acute, fluctuating, reversible "
     "delirium."),
    (SDB, "Medication-Related Cognitive Impairment Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from cognitive impairment attributable to "
     "medication effect."),
    (SDB, "Metabolic Encephalopathy Differentiation", "PATHOLOGICAL_SUBTYPE", None,
     "Review prompt distinguishing this general-decline disease from a reversible metabolic encephalopathy."),

    # --- HEMIPLEGIA / HEMIPARESIS: LATERALITY, DOMINANCE, ORIGIN -------------
    (HEMIPLEGIA, "Left Hemiplegia", "LATERALITY", None, "Complete/near-complete paralysis of the left side."),
    (HEMIPLEGIA, "Right Hemiplegia", "LATERALITY", None, "Complete/near-complete paralysis of the right side."),
    (HEMIPLEGIA, "Bilateral Weakness", "LATERALITY", None, "Weakness affecting both sides of the body."),
    (HEMIPLEGIA, "Dominant-Side Functional Loss", "DOMINANCE", None,
     "Functional loss involving the patient's dominant side."),
    (HEMIPLEGIA, "Non-Dominant-Side Functional Loss", "DOMINANCE", None,
     "Functional loss involving the patient's non-dominant side."),
    (HEMIPLEGIA, "Cerebral Lesion Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a cerebral (cortical/subcortical) lesion as the origin of the hemiplegia -- not "
     "assumed without patient-specific evidence."),
    (HEMIPLEGIA, "Brainstem Lesion Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a brainstem lesion as the origin of the hemiplegia."),
    (HEMIPLEGIA, "Spinal Cord Lesion Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a spinal cord lesion as the origin of the hemiplegia."),
    (HEMIPLEGIA, "Peripheral-Nerve Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a peripheral-nerve disorder as the origin of the hemiplegia."),
    (HEMIPLEGIA, "Neuromuscular Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a neuromuscular disorder as the origin of the hemiplegia."),

    (HEMIPARESIS, "Left Hemiparesis", "LATERALITY", None, "Partial weakness of the left side."),
    (HEMIPARESIS, "Right Hemiparesis", "LATERALITY", None, "Partial weakness of the right side."),
    (HEMIPARESIS, "Bilateral Weakness", "LATERALITY", None, "Weakness affecting both sides of the body."),
    (HEMIPARESIS, "Dominant-Side Functional Loss", "DOMINANCE", None,
     "Functional loss involving the patient's dominant side."),
    (HEMIPARESIS, "Non-Dominant-Side Functional Loss", "DOMINANCE", None,
     "Functional loss involving the patient's non-dominant side."),
    (HEMIPARESIS, "Cerebral Lesion Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a cerebral (cortical/subcortical) lesion as the origin of the hemiparesis -- not "
     "assumed without patient-specific evidence."),
    (HEMIPARESIS, "Brainstem Lesion Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a brainstem lesion as the origin of the hemiparesis."),
    (HEMIPARESIS, "Spinal Cord Lesion Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a spinal cord lesion as the origin of the hemiparesis."),
    (HEMIPARESIS, "Peripheral-Nerve Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a peripheral-nerve disorder as the origin of the hemiparesis."),
    (HEMIPARESIS, "Neuromuscular Origin Review", "ANATOMICAL_LOCATION", None,
     "Review prompt for a neuromuscular disorder as the origin of the hemiparesis."),
    (HEMIPARESIS, "Hemiplegia Differentiation", "SEVERITY_CLASS", None,
     "Review prompt confirming this is a partial-weakness (hemiparesis) pattern, not the complete/"
     "near-complete paralysis pattern of Hemiplegia -- the two are never treated as interchangeable."),

    # --- CONTRACTURE: ETIOLOGY, LOCATION, SEVERITY ---------------------------
    (CONTRACTURE, "Upper-Motor-Neuron Injury Etiology", "MECHANISM", None,
     "Contracture arising from upper-motor-neuron injury (e.g. following stroke)."),
    (CONTRACTURE, "Spasticity Etiology", "MECHANISM", None, "Contracture arising from spasticity."),
    (CONTRACTURE, "Immobility Etiology", "MECHANISM", None, "Contracture arising from prolonged immobility."),
    (CONTRACTURE, "Prolonged Positioning Etiology", "MECHANISM", None,
     "Contracture arising from prolonged static positioning."),
    (CONTRACTURE, "Pain-Limited Movement Etiology", "MECHANISM", None,
     "Contracture arising from movement avoidance due to pain."),
    (CONTRACTURE, "Joint Disease Etiology", "MECHANISM", None,
     "Contracture arising from underlying joint disease."),
    (CONTRACTURE, "Soft-Tissue Shortening Etiology", "MECHANISM", None,
     "Contracture arising from soft-tissue shortening."),
    (CONTRACTURE, "Shoulder Contracture", "ANATOMICAL_LOCATION", None, "Contracture at the shoulder."),
    (CONTRACTURE, "Elbow Contracture", "ANATOMICAL_LOCATION", None, "Contracture at the elbow."),
    (CONTRACTURE, "Wrist Contracture", "ANATOMICAL_LOCATION", None, "Contracture at the wrist."),
    (CONTRACTURE, "Hand Contracture", "ANATOMICAL_LOCATION", None, "Contracture at the hand."),
    (CONTRACTURE, "Hip Contracture", "ANATOMICAL_LOCATION", None, "Contracture at the hip."),
    (CONTRACTURE, "Knee Contracture", "ANATOMICAL_LOCATION", None, "Contracture at the knee."),
    (CONTRACTURE, "Ankle Contracture", "ANATOMICAL_LOCATION", None, "Contracture at the ankle."),
    (CONTRACTURE, "Mild Range-of-Motion Limitation", "SEVERITY_CLASS", None,
     "Mild reduction in passive range of motion."),
    (CONTRACTURE, "Moderate Range-of-Motion Limitation", "SEVERITY_CLASS", None,
     "Moderate reduction in passive range of motion."),
    (CONTRACTURE, "Fixed Contracture", "SEVERITY_CLASS", None,
     "Fixed, non-reducible loss of passive range of motion."),
    (CONTRACTURE, "Multi-Joint Contracture", "SEVERITY_CLASS", None,
     "Contracture involving more than one joint."),
]


# ---------------------------------------------------------------------------
# TIER 5 <-> TIER 4 APPLICABILITY EDGES
# (disease_name, concept_type, concept_name, variant_name, applicability_type,
#  description)
# concept_name must already exist for that disease/concept_type -- either
# from the Phase 2 baseline or from NEW_SYMPTOMS/NEW_FINDINGS/
# NEW_COMPLICATIONS above (populated before this list is processed).
# ---------------------------------------------------------------------------
ApplicabilityDef = Tuple[str, str, str, str, str, str]

APPLICABILITY_DEFS: List[ApplicabilityDef] = [
    # --- Frontal lobe ---
    *[(STROKE, "SYMPTOM", name, "Frontal-Lobe Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for frontal-lobe involvement; a review prompt, not a confirmed localization.")
      for name in [
          "Impaired Executive Function", "Impaired Judgment", "Abulia", "Apathy",
          "Behavioral Disinhibition", "Personality or Behavioral Change", "Impaired Attention",
          "Urinary Incontinence",
      ]],
    (STROKE, "FINDING", "Contralateral Motor Weakness", "Frontal-Lobe Stroke", "MAY_OCCUR_WITH",
     "Expected exam finding for frontal-lobe motor cortex involvement."),
    (STROKE, "SYMPTOM", "Facial Weakness", "Frontal-Lobe Stroke", "MAY_OCCUR_WITH",
     "Expected symptom pattern for frontal-lobe involvement."),
    (STROKE, "SYMPTOM", "Expressive Aphasia", "Dominant-Hemisphere Stroke", "MAY_OCCUR_WITH",
     "Broca (expressive) aphasia is only expected when the dominant hemisphere is documented as involved -- "
     "never inferred from left-hemisphere laterality alone."),

    # --- Temporal lobe ---
    *[(STROKE, "SYMPTOM", name, "Temporal-Lobe Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for temporal-lobe involvement; a review prompt, not a confirmed localization.")
      for name in ["Memory Impairment", "Seizure", "Confusion"]],
    (STROKE, "SYMPTOM", "Receptive Aphasia", "Dominant-Hemisphere Stroke", "MAY_OCCUR_WITH",
     "Wernicke (receptive) aphasia is only expected when the dominant hemisphere is documented as involved -- "
     "never automatically inferred from every temporal-lobe lesion."),
    (STROKE, "FINDING", "Visual Field Deficit", "Temporal-Lobe Stroke", "MAY_OCCUR_WITH",
     "Contralateral superior quadrantanopia may occur with temporal-lobe optic-radiation involvement."),

    # --- Parietal lobe ---
    *[(STROKE, "SYMPTOM", name, "Parietal-Lobe Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for parietal-lobe involvement; a review prompt, not a confirmed localization.")
      for name in ["Astereognosis", "Agraphesthesia", "Apraxia"]],
    (STROKE, "SYMPTOM", "Unilateral Sensory Loss", "Parietal-Lobe Stroke", "MAY_OCCUR_WITH",
     "Cortical sensory loss expected with parietal-lobe involvement."),
    (STROKE, "FINDING", "Cortical Sensory Deficit", "Parietal-Lobe Stroke", "MAY_OCCUR_WITH",
     "Higher-order sensory discrimination deficit expected with parietal-lobe involvement."),
    *[(STROKE, "SYMPTOM", name, "Dominant-Parietal Stroke", "SUPPORTS_DIFFERENTIATION",
       "Distinguishes dominant- from non-dominant-parietal presentation; requires documented dominance.")
      for name in ["Acalculia", "Agraphia", "Left-Right Disorientation"]],
    (STROKE, "FINDING", "Finger Agnosia", "Dominant-Parietal Stroke", "SUPPORTS_DIFFERENTIATION",
     "Part of the dominant-parietal (Gerstmann) constellation; supports differentiation from non-dominant "
     "presentation."),
    (STROKE, "SYMPTOM", "Unilateral Neglect", "Non-Dominant-Parietal Stroke", "SUPPORTS_DIFFERENTIATION",
     "Contralateral neglect is the classic non-dominant-parietal presentation, distinguishing it from the "
     "dominant-parietal pattern."),
    (STROKE, "SYMPTOM", "Anosognosia", "Non-Dominant-Parietal Stroke", "SUPPORTS_DIFFERENTIATION",
     "Lack of deficit awareness is a classic non-dominant-parietal presentation."),
    (STROKE, "FINDING", "Constructional Apraxia", "Non-Dominant-Parietal Stroke", "SUPPORTS_DIFFERENTIATION",
     "Constructional apraxia is a classic non-dominant-parietal presentation."),

    # --- Occipital lobe ---
    (STROKE, "FINDING", "Visual Field Deficit", "Occipital-Lobe Stroke", "MAY_OCCUR_WITH",
     "Homonymous hemianopia is the hallmark occipital-lobe finding; requires visual-field or imaging "
     "evidence, never asserted without it."),
    (STROKE, "SYMPTOM", "Vision Loss", "Occipital-Lobe Stroke", "MAY_OCCUR_WITH",
     "Cortical visual impairment is an expected symptom pattern for occipital-lobe involvement."),
    (STROKE, "SYMPTOM", "Visual Agnosia", "Occipital-Lobe Stroke", "MAY_OCCUR_WITH",
     "Impaired visual recognition is an expected occipital-lobe pattern."),
    (STROKE, "SYMPTOM", "Visual Hallucination", "Occipital-Lobe Stroke", "MAY_OCCUR_WITH",
     "Visual hallucination is an expected occipital-lobe/PCA-territory pattern."),
    (STROKE, "FINDING", "Cortical Blindness", "Occipital-Lobe Stroke", "MAY_OCCUR_WITH",
     "Cortical blindness requires bilateral occipital involvement -- never asserted from a unilateral "
     "lesion."),

    # --- Insula ---
    *[(STROKE, "SYMPTOM", name, "Insular Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for insular involvement.")
      for name in ["Dysphagia", "Dysarthria", "Autonomic Instability", "Altered Taste"]],

    # --- Hemisphere laterality mapping ---
    *[(STROKE, "SYMPTOM", name, "Left-Hemisphere Stroke", "MAY_OCCUR_WITH",
       "Right-sided deficit expected with left-hemisphere involvement (contralateral pattern).")
      for name in ["Hemiparesis", "Hemiplegia", "Unilateral Sensory Loss"]],
    *[(STROKE, "SYMPTOM", name, "Right-Hemisphere Stroke", "MAY_OCCUR_WITH",
       "Left-sided deficit expected with right-hemisphere involvement (contralateral pattern).")
      for name in ["Hemiparesis", "Hemiplegia", "Unilateral Sensory Loss"]],
    (STROKE, "SYMPTOM", "Unilateral Neglect", "Right-Hemisphere Stroke", "MAY_OCCUR_WITH",
     "Neglect is expected with right- (typically non-dominant-) hemisphere involvement, but is never "
     "automatically inferred from every right-sided stroke without exam evidence."),
    (STROKE, "SYMPTOM", "Aphasia", "Left-Hemisphere Stroke", "MAY_OCCUR_WITH",
     "Aphasia is expected when the left hemisphere is language-dominant, but dominance is never assumed "
     "from laterality alone -- requires documented or clinically supported dominance."),
    (STROKE, "FINDING", "Visual Field Deficit", "Left-Hemisphere Stroke", "MAY_OCCUR_WITH",
     "Right homonymous hemianopia may occur with left-hemisphere involvement."),
    (STROKE, "FINDING", "Visual Field Deficit", "Right-Hemisphere Stroke", "MAY_OCCUR_WITH",
     "Left homonymous hemianopia may occur with right-hemisphere involvement."),

    # --- Vascular territory: MCA ---
    *[(STROKE, "SYMPTOM", name, "Middle Cerebral Artery Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for middle cerebral artery territory involvement.")
      for name in ["Dysarthria", "Dysphagia", "Unilateral Sensory Loss"]],
    (STROKE, "SYMPTOM", "Aphasia", "Middle Cerebral Artery Stroke", "MAY_OCCUR_WITH",
     "Expected with dominant-hemisphere MCA involvement."),
    (STROKE, "SYMPTOM", "Unilateral Neglect", "Middle Cerebral Artery Stroke", "MAY_OCCUR_WITH",
     "Expected with non-dominant-hemisphere MCA involvement."),
    (STROKE, "FINDING", "Gaze Preference Toward Lesion", "Middle Cerebral Artery Stroke", "MAY_OCCUR_WITH",
     "Expected exam finding with large MCA-territory involvement."),
    *[(STROKE, "COMPLICATION", name, "Large MCA Stroke", "MAY_OCCUR_WITH",
       "Mass-effect complication expected with large MCA-territory infarction.")
      for name in ["Herniation"]],
    (STROKE, "FINDING", "Cerebral Edema", "Large MCA Stroke", "MAY_OCCUR_WITH",
     "Expected imaging finding with large MCA-territory infarction."),
    (STROKE, "FINDING", "Midline Shift", "Large MCA Stroke", "PROGNOSTIC_FOR",
     "Midline shift on imaging is a poor-prognosis indicator for large MCA-territory infarction."),
    (STROKE, "SYMPTOM", "Altered Level of Consciousness", "Large MCA Stroke", "PROGNOSTIC_FOR",
     "Declining consciousness with a large MCA infarct is a poor-prognosis indicator."),

    # --- ACA ---
    *[(STROKE, "SYMPTOM", name, "Anterior Cerebral Artery Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for anterior cerebral artery territory involvement.")
      for name in ["Abulia", "Apathy", "Urinary Incontinence"]],

    # --- PCA ---
    *[(STROKE, "SYMPTOM", name, "Posterior Cerebral Artery Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for posterior cerebral artery territory involvement.")
      for name in ["Memory Impairment", "Visual Agnosia"]],
    (STROKE, "FINDING", "Visual Field Deficit", "Posterior Cerebral Artery Stroke", "MAY_OCCUR_WITH",
     "Contralateral homonymous hemianopia expected with PCA-territory involvement."),

    # --- Internal carotid artery ---
    (STROKE, "SYMPTOM", "Vision Loss", "Internal Carotid Artery Stroke", "MAY_OCCUR_WITH",
     "Monocular visual loss (amaurosis fugax pattern) expected with internal carotid artery involvement."),
    (STROKE, "SYMPTOM", "Altered Level of Consciousness", "Internal Carotid Artery Stroke", "MAY_OCCUR_WITH",
     "Reduced consciousness expected with a large internal-carotid-territory infarction."),

    # --- Vertebrobasilar / basilar ---
    *[(STROKE, "SYMPTOM", name, "Vertebrobasilar Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for vertebrobasilar territory involvement.")
      for name in ["Vertigo", "Nystagmus", "Diplopia", "Dysarthria", "Dysphagia", "Ataxia/Imbalance"]],
    *[(STROKE, "SYMPTOM", name, "Basilar Artery Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for basilar artery territory involvement, high risk for bilateral deficit.")
      for name in ["Quadriparesis", "Quadriplegia", "Dysarthria", "Dysphagia"]],
    (STROKE, "FINDING", "Impaired Horizontal Gaze", "Basilar Artery Stroke", "MAY_OCCUR_WITH",
     "Expected exam finding with basilar-territory (pontine) involvement."),
    (STROKE, "SYMPTOM", "Altered Level of Consciousness", "Basilar Artery Stroke", "PROGNOSTIC_FOR",
     "Coma with basilar-territory involvement is a poor-prognosis indicator."),

    # --- Deep / subcortical ---
    (STROKE, "FINDING", "Pure Motor Hemiparesis", "Internal Capsule Stroke", "STRONGLY_ASSOCIATED_WITH",
     "Pure motor hemiparesis without cortical signs is the classic internal-capsule (lacunar) pattern."),
    (STROKE, "SYMPTOM", "Dysarthria", "Internal Capsule Stroke", "MAY_OCCUR_WITH",
     "Dysarthria-clumsy hand syndrome may occur with internal-capsule involvement."),
    (STROKE, "FINDING", "Pure Sensory Deficit", "Thalamic Stroke", "STRONGLY_ASSOCIATED_WITH",
     "Pure sensory deficit without motor findings is the classic thalamic (lacunar) pattern."),
    (STROKE, "SYMPTOM", "Central Post-Stroke Pain", "Thalamic Stroke", "MAY_OCCUR_WITH",
     "Central post-stroke pain is a recognized thalamic-lesion sequela."),
    (STROKE, "SYMPTOM", "Memory Impairment", "Thalamic Stroke", "MAY_OCCUR_WITH",
     "Memory impairment may occur with thalamic involvement."),
    *[(STROKE, "SYMPTOM", name, "Basal Ganglia Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for basal-ganglia involvement.")
      for name in ["Dysarthria", "Impaired Executive Function"]],
    (STROKE, "FINDING", "Contralateral Motor Weakness", "Basal Ganglia Stroke", "MAY_OCCUR_WITH",
     "Contralateral motor deficit expected with basal-ganglia involvement."),

    # --- Lacunar syndromes ---
    (STROKE, "FINDING", "Pure Motor Hemiparesis", "Lacunar Stroke", "STRONGLY_ASSOCIATED_WITH",
     "One of the recognized lacunar syndromes."),
    (STROKE, "FINDING", "Pure Sensory Deficit", "Lacunar Stroke", "STRONGLY_ASSOCIATED_WITH",
     "One of the recognized lacunar syndromes."),
    (STROKE, "SYMPTOM", "Ataxia/Imbalance", "Lacunar Stroke", "MAY_OCCUR_WITH",
     "Ataxic hemiparesis is a recognized lacunar syndrome."),
    (STROKE, "SYMPTOM", "Dysarthria", "Lacunar Stroke", "MAY_OCCUR_WITH",
     "Dysarthria-clumsy hand syndrome is a recognized lacunar syndrome."),

    # --- Brainstem ---
    *[(STROKE, "SYMPTOM", name, "Brainstem Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for brainstem involvement.")
      for name in ["Dysarthria", "Dysphagia", "Diplopia", "Vertigo", "Nystagmus", "Ataxia/Imbalance"]],
    (STROKE, "SYMPTOM", "Cranial-Nerve Deficit", "Brainstem Stroke", "MAY_OCCUR_WITH",
     "Cranial-nerve dysfunction is a hallmark brainstem finding."),
    (STROKE, "SYMPTOM", "Altered Level of Consciousness", "Brainstem Stroke", "MAY_OCCUR_WITH",
     "Impaired consciousness may occur with brainstem involvement."),
    (STROKE, "FINDING", "Ptosis", "Midbrain Stroke", "MAY_OCCUR_WITH",
     "Oculomotor-nerve dysfunction is an expected midbrain finding."),
    (STROKE, "FINDING", "Vertical-Gaze Abnormality", "Midbrain Stroke", "MAY_OCCUR_WITH",
     "Vertical-gaze impairment is an expected midbrain finding."),
    (STROKE, "SYMPTOM", "Facial Weakness", "Pontine Stroke", "MAY_OCCUR_WITH",
     "Facial weakness is an expected pontine finding."),
    (STROKE, "FINDING", "Impaired Horizontal Gaze", "Pontine Stroke", "MAY_OCCUR_WITH",
     "Horizontal-gaze impairment is an expected pontine finding."),
    (STROKE, "SYMPTOM", "Dysphagia", "Medullary Stroke",
     "MAY_OCCUR_WITH", "Dysphagia is an expected medullary finding."),
    (STROKE, "SYMPTOM", "Vertigo", "Medullary Stroke", "MAY_OCCUR_WITH",
     "Vertigo is an expected medullary finding."),

    # --- Locked-in syndrome (must never be treated as coma) ---
    (STROKE, "SYMPTOM", "Quadriplegia", "Locked-In Syndrome", "STRONGLY_ASSOCIATED_WITH",
     "Quadriplegia with preserved consciousness defines locked-in syndrome, distinguishing it from coma."),
    (STROKE, "FINDING", "Impaired Horizontal Gaze", "Locked-In Syndrome", "SUPPORTS_DIFFERENTIATION",
     "Impaired horizontal gaze with preserved vertical gaze/blinking distinguishes locked-in syndrome from "
     "coma, in which no purposeful response is present at all."),

    # --- Cerebellar ---
    *[(STROKE, "SYMPTOM", name, "Cerebellar Stroke", "MAY_OCCUR_WITH",
       "Expected review pattern for cerebellar involvement.")
      for name in ["Vertigo", "Nausea", "Vomiting", "Ataxia/Imbalance", "Dysarthria", "Sudden Severe Headache"]],
    (STROKE, "FINDING", "Truncal Ataxia", "Cerebellar-Vermis Stroke", "STRONGLY_ASSOCIATED_WITH",
     "Truncal ataxia is the classic cerebellar-vermis presentation."),
    (STROKE, "FINDING", "Dysmetria", "Cerebellar-Hemisphere Stroke", "STRONGLY_ASSOCIATED_WITH",
     "Limb dysmetria is the classic cerebellar-hemisphere presentation."),
    (STROKE, "COMPLICATION", "Obstructive Hydrocephalus", "Cerebellar Stroke", "MAY_OCCUR_WITH",
     "Cerebellar edema can compress the fourth ventricle, producing obstructive hydrocephalus."),

    # --- Ischemic vs. hemorrhagic treatment stratification (safety-critical
    #     negative knowledge) ---
    (STROKE, "TREATMENT", "Thrombolytic Therapy", "Ischemic Stroke",
     "TREATMENT_SPECIFIC_TO", "Thrombolysis is specific to ischemic stroke within the treatment window."),
    (STROKE, "TREATMENT", "Thrombolytic Therapy", "Hemorrhagic Stroke",
     "CONTRAINDICATED_FOR", "Thrombolysis is never appropriate for hemorrhagic stroke; ischemic-specific "
     "treatment knowledge must never be attached to a hemorrhagic-stroke context."),
    (STROKE, "TREATMENT", "Mechanical Thrombectomy", "Large-Artery Atherosclerotic Stroke",
     "TREATMENT_SPECIFIC_TO", "Mechanical thrombectomy is specific to large-vessel ischemic occlusion."),
    (STROKE, "TREATMENT", "Mechanical Thrombectomy", "Cardioembolic Stroke",
     "TREATMENT_SPECIFIC_TO", "Mechanical thrombectomy is specific to large-vessel ischemic occlusion, "
     "including cardioembolic large-vessel occlusion."),

    # --- Hemorrhagic poor-prognosis / hospice-significant findings ---
    (STROKE, "FINDING", "Intraventricular Extension", "Intracerebral Hemorrhage", "PROGNOSTIC_FOR",
     "Intraventricular extension of hemorrhage is a recognized poor-prognosis indicator."),
    (STROKE, "FINDING", "Midline Shift", "Intracerebral Hemorrhage", "PROGNOSTIC_FOR",
     "Significant midline shift is a recognized poor-prognosis indicator."),
    (STROKE, "COMPLICATION", "Obstructive Hydrocephalus", "Intracerebral Hemorrhage", "HOSPICE_SUPPORT_FOR",
     "Obstructive hydrocephalus with shunt non-candidacy or shunt decline can support hospice-eligibility "
     "review under the general poor-prognosis hemorrhagic-stroke pattern."),
    (STROKE, "SYMPTOM", "Thunderclap Headache", "Subarachnoid Hemorrhage", "STRONGLY_ASSOCIATED_WITH",
     "Thunderclap headache is the hallmark subarachnoid-hemorrhage presentation."),
    (STROKE, "SYMPTOM", "Neck Stiffness", "Subarachnoid Hemorrhage", "MAY_OCCUR_WITH",
     "Meningeal irritation is an expected subarachnoid-hemorrhage finding."),
    (STROKE, "SYMPTOM", "Photophobia", "Subarachnoid Hemorrhage", "MAY_OCCUR_WITH",
     "Meningeal irritation is an expected subarachnoid-hemorrhage finding."),
    (STROKE, "COMPLICATION", "Vasospasm", "Subarachnoid Hemorrhage", "MAY_OCCUR_WITH",
     "Vasospasm is a recognized delayed complication of subarachnoid hemorrhage."),
    (STROKE, "COMPLICATION", "Delayed Cerebral Ischemia", "Subarachnoid Hemorrhage", "PROGNOSTIC_FOR",
     "Delayed cerebral ischemia following subarachnoid hemorrhage is a poor-prognosis indicator."),
    (STROKE, "COMPLICATION", "Rebleeding", "Subarachnoid Hemorrhage", "PROGNOSTIC_FOR",
     "Rebleeding prior to aneurysm-securing intervention is a high-mortality poor-prognosis indicator."),

    # --- Historical / residual deficit safeguards ---
    (STROKE, "SYMPTOM", "Hemiparesis", "Historical Stroke", "SUPPORTS_DIFFERENTIATION",
     "A historical stroke diagnosis does not, by itself, establish that a documented deficit is currently "
     "active -- current status requires independent patient-specific evidence."),
    (STROKE, "SYMPTOM", "Hemiparesis", "Residual Deficit Following Stroke", "MAY_OCCUR_WITH",
     "Residual hemiparesis is a recognized post-stroke residual-deficit pattern."),
    (STROKE, "SYMPTOM", "Hemiplegia", "Residual Deficit Following Stroke", "MAY_OCCUR_WITH",
     "Residual hemiplegia is a recognized post-stroke residual-deficit pattern."),
    (STROKE, "SYMPTOM", "Dysphagia", "Residual Deficit Following Stroke", "MAY_OCCUR_WITH",
     "Residual dysphagia is a recognized post-stroke residual-deficit pattern."),

    # --- Dementia-pattern differentiation edges (Alzheimer's disease) ---
    (ALZ, "SYMPTOM", "Progressive Memory Loss", "Alzheimer's Pattern", "STRONGLY_ASSOCIATED_WITH",
     "Progressive episodic-memory-led decline is the core Alzheimer's pattern."),
    (ALZ, "SYMPTOM", "Language Decline (Aphasia)", "Alzheimer's Pattern", "MAY_OCCUR_WITH",
     "Language decline is an expected Alzheimer's-pattern finding as disease progresses."),
    (ALZ, "SYMPTOM", "Apraxia", "Alzheimer's Pattern", "MAY_OCCUR_WITH",
     "Apraxia is an expected Alzheimer's-pattern finding as disease progresses."),
    (ALZ, "SYMPTOM", "Agnosia", "Alzheimer's Pattern", "MAY_OCCUR_WITH",
     "Agnosia is an expected Alzheimer's-pattern finding as disease progresses."),
    (ALZ, "FINDING", "FAST Stage 7", "Alzheimer's Pattern", "END_STAGE_SUPPORT_FOR",
     "FAST Stage 7 supports Alzheimer's-specific end-stage/hospice-eligibility review."),
    (ALZ, "SYMPTOM", "Behavioral/Psychological Symptoms", "Vascular-Pattern Review",
     "SUPPORTS_DIFFERENTIATION", "Focal deficits and stepwise decline (not gradual episodic-memory-led "
     "decline) support a vascular-pattern differential review."),
    (ALZ, "SYMPTOM", "Disorientation", "Delirium Differentiation", "SUPPORTS_DIFFERENTIATION",
     "Acute, fluctuating onset must be differentiated from a progressive dementia pattern before any "
     "dementia-specific conclusion is drawn."),

    # --- Senile Degeneration of Brain differentiation edges ---
    (SDB, "SYMPTOM", "Progressive Forgetfulness", "General Decline Pattern", "STRONGLY_ASSOCIATED_WITH",
     "Generalized, non-focal forgetfulness is the core Senile Degeneration of Brain pattern."),
    (SDB, "SYMPTOM", "Global Cognitive Slowing", "General Decline Pattern", "MAY_OCCUR_WITH",
     "Global, non-focal cognitive slowing is an expected general-decline finding."),
    (SDB, "FINDING", "Diffuse Cognitive Impairment on Screening", "Alzheimer's Differentiation",
     "SUPPORTS_DIFFERENTIATION", "A diffuse, non-focal screening pattern -- without Alzheimer's-specific "
     "staging evidence -- supports keeping this disease distinct from Dementia Due To Alzheimer's Disease; "
     "Alzheimer-specific FAST staging and hospice criteria are never automatically applied here."),
    (SDB, "SYMPTOM", "Reduced Alertness/Arousal", "General Decline Pattern", "HOSPICE_SUPPORT_FOR",
     "Progressively reduced alertness supports general-decline hospice-eligibility review using "
     "non-Alzheimer-specific general-decline criteria."),

    # --- Hemiplegia vs. Hemiparesis differentiation ---
    (HEMIPLEGIA, "SYMPTOM", "Complete Unilateral Paralysis", "Left Hemiplegia", "MAY_OCCUR_WITH",
     "Complete/near-complete paralysis pattern on the left side."),
    (HEMIPLEGIA, "SYMPTOM", "Complete Unilateral Paralysis", "Right Hemiplegia", "MAY_OCCUR_WITH",
     "Complete/near-complete paralysis pattern on the right side."),
    (HEMIPARESIS, "SYMPTOM", "Partial Unilateral Weakness", "Left Hemiparesis", "MAY_OCCUR_WITH",
     "Partial weakness pattern on the left side."),
    (HEMIPARESIS, "SYMPTOM", "Partial Unilateral Weakness", "Right Hemiparesis", "MAY_OCCUR_WITH",
     "Partial weakness pattern on the right side."),
    (HEMIPARESIS, "SYMPTOM", "Partial Unilateral Weakness", "Hemiplegia Differentiation",
     "SUPPORTS_DIFFERENTIATION", "Confirms the partial-weakness pattern of Hemiparesis is distinct from, "
     "and never interchangeable with, the complete/near-complete paralysis pattern of Hemiplegia."),

    # --- Contracture: etiology / location / severity / consequences ---
    (CONTRACTURE, "SYMPTOM", "Fixed Joint Limitation", "Upper-Motor-Neuron Injury Etiology", "MAY_OCCUR_WITH",
     "Contracture following upper-motor-neuron injury (e.g. post-stroke spasticity)."),
    (CONTRACTURE, "SYMPTOM", "Painful Muscle Spasm", "Spasticity Etiology", "MAY_OCCUR_WITH",
     "Spasticity-driven contracture presentation."),
    (CONTRACTURE, "FINDING", "Reduced Passive Range of Motion", "Fixed Contracture", "STRONGLY_ASSOCIATED_WITH",
     "Reduced, non-reducible passive range of motion defines a fixed contracture."),
    (CONTRACTURE, "SYMPTOM", "Skin Fold Maceration", "Fixed Contracture", "MAY_OCCUR_WITH",
     "Skin breakdown risk increases with fixed, persistently flexed joint contracture."),
    (CONTRACTURE, "SYMPTOM", "Pain With Passive Movement", "Hip Contracture", "MAY_OCCUR_WITH",
     "Pain on passive movement is expected at a contracted hip."),
    (CONTRACTURE, "SYMPTOM", "Pain With Passive Movement", "Knee Contracture", "MAY_OCCUR_WITH",
     "Pain on passive movement is expected at a contracted knee."),
]


# ---------------------------------------------------------------------------
# Population functions
# ---------------------------------------------------------------------------


def _resolve_diseases(db: Session) -> Dict[str, OntologyDisease]:
    resolved: Dict[str, OntologyDisease] = {}
    missing: List[str] = []
    for name in ALL_DISEASE_NAMES:
        disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            missing.append(name)
        else:
            resolved[name] = disease
    if missing:
        raise RuntimeError(
            "Neurologic Clinical Reasoning Completion requires these six diseases to already exist "
            f"(from the merged Phase 2 baseline) and was unable to resolve: {missing}. Aborting without "
            "any writes."
        )
    return resolved


def populate_new_concepts(db: Session, diseases: Dict[str, OntologyDisease]) -> Dict[str, int]:
    from app.models.ontology_disease_blueprint import OntologyDiseaseComplication, OntologyDiseaseFinding, OntologyDiseaseSymptom

    return {
        "new_symptoms_inserted": _populate_simple_domain(
            db, OntologyDiseaseSymptom, NEW_SYMPTOMS, diseases,
            ["symptom_name"], ["symptom_name", "description", "hospice_relevance", "severity_scale"],
        ),
        "new_findings_inserted": _populate_simple_domain(
            db, OntologyDiseaseFinding, NEW_FINDINGS, diseases,
            ["finding_name"], ["finding_name", "finding_description"],
        ),
        "new_complications_inserted": _populate_simple_domain(
            db, OntologyDiseaseComplication, NEW_COMPLICATIONS, diseases,
            ["complication_name"],
            ["complication_name", "description", "common_occurrence", "clinical_significance"],
        ),
    }


def populate_variants(
    db: Session, diseases: Dict[str, OntologyDisease]
) -> Tuple[int, Dict[Tuple[str, str], OntologyDiseaseVariant]]:
    inserted = 0
    variant_by_key: Dict[Tuple[str, str], OntologyDiseaseVariant] = {}
    for disease_name, variant_name, dimension, parent_name, description in VARIANT_DEFS:
        disease = diseases[disease_name]
        normalized = variant_name.strip().lower()
        existing = (
            db.query(OntologyDiseaseVariant)
            .filter_by(disease_id=disease.id, variant_dimension=dimension, normalized_name=normalized)
            .one_or_none()
        )
        if existing is not None:
            variant_by_key[(disease_name, variant_name)] = existing
            continue
        parent_variant = variant_by_key.get((disease_name, parent_name)) if parent_name else None
        variant = OntologyDiseaseVariant(
            id=uuid.uuid4(),
            disease_id=disease.id,
            parent_variant_id=parent_variant.id if parent_variant else None,
            variant_name=variant_name,
            normalized_name=normalized,
            variant_dimension=dimension,
            description=description,
            evidence_requirement=(
                "Requires patient-record evidence (imaging, exam, or documented clinical course) before "
                "this variant/context is ever treated as a confirmed patient-specific fact."
            ),
        )
        db.add(variant)
        db.flush()
        variant_by_key[(disease_name, variant_name)] = variant
        inserted += 1
    return inserted, variant_by_key


def _resolve_concept_id(db: Session, disease_id, concept_type: str, name: str):
    model_cls, name_attr = CONCEPT_TYPE_MODEL_MAP[concept_type]
    filter_kwargs = {"disease_id": disease_id, name_attr: name}
    row = db.query(model_cls).filter_by(**filter_kwargs).one_or_none()
    return row.id if row is not None else None


def populate_applicability(
    db: Session, diseases: Dict[str, OntologyDisease], variant_by_key: Dict[Tuple[str, str], OntologyDiseaseVariant]
) -> Tuple[int, List[str]]:
    inserted = 0
    unresolved: List[str] = []
    for disease_name, concept_type, concept_name, variant_name, applicability_type, description in (
        APPLICABILITY_DEFS
    ):
        disease = diseases[disease_name]
        variant = variant_by_key.get((disease_name, variant_name))
        if variant is None:
            unresolved.append(f"variant not found: {disease_name} / {variant_name}")
            continue
        concept_id = _resolve_concept_id(db, disease.id, concept_type, concept_name)
        if concept_id is None:
            unresolved.append(f"concept not found: {disease_name} / {concept_type} / {concept_name}")
            continue
        existing = (
            db.query(OntologyConceptVariantApplicability)
            .filter_by(
                concept_type=concept_type,
                concept_id=concept_id,
                variant_id=variant.id,
                applicability_type=applicability_type,
            )
            .one_or_none()
        )
        if existing is not None:
            continue
        db.add(
            OntologyConceptVariantApplicability(
                id=uuid.uuid4(),
                disease_id=disease.id,
                concept_type=concept_type,
                concept_id=concept_id,
                variant_id=variant.id,
                applicability_type=applicability_type,
                description=description,
                evidence_requirement=(
                    "General ontology applicability knowledge only; requires independent patient-record "
                    "evidence before ever being treated as a documented patient-specific finding."
                ),
            )
        )
        inserted += 1
    db.flush()
    return inserted, unresolved


def populate_variant_evidence_rules(db: Session, diseases: Dict[str, OntologyDisease]) -> int:
    inserted = 0
    disease_ids = {d.id for d in diseases.values()}
    variants = db.query(OntologyDiseaseVariant).filter(OntologyDiseaseVariant.disease_id.in_(disease_ids)).all()
    for variant in variants:
        if not variant.active:
            continue
        existing = (
            db.query(OntologyEvidenceRule)
            .filter_by(concept_type="DISEASE_VARIANT", concept_id=variant.id)
            .one_or_none()
        )
        if existing is not None:
            continue
        db.add(
            OntologyEvidenceRule(
                id=uuid.uuid4(),
                concept_type="DISEASE_VARIANT",
                concept_id=variant.id,
                evidence_source="Standard neuroanatomy/cerebrovascular clinical literature "
                "(mechanism, territory, localization, phase, and consciousness-state knowledge).",
                evidence_type="DISEASE_VARIANT",
                confidence="moderate",
                review_trigger="RN_REVIEW",
                patient_fact_requires_evidence=True,
                notes=(
                    f"Evidence rule for Tier 4 DISEASE_VARIANT '{variant.variant_name}' "
                    f"(dimension={variant.variant_dimension}); this variant/clinical-context knowledge "
                    "requires patient-record evidence before ever being treated as a confirmed "
                    "patient-specific localization, mechanism, laterality, or phase."
                ),
            )
        )
        inserted += 1
    db.flush()
    return inserted


def _run_duplicate_and_integrity_checks(db: Session, disease: OntologyDisease) -> List[Tuple[str, str, str, int, int]]:
    checks: List[Tuple[str, str, str, int, int]] = []

    # DUPLICATE: no duplicate normalized variant within the same disease+dimension
    variants = db.query(OntologyDiseaseVariant).filter_by(disease_id=disease.id).all()
    seen: Dict[Tuple[str, str], int] = {}
    for v in variants:
        key = (v.variant_dimension, v.normalized_name)
        seen[key] = seen.get(key, 0) + 1
    dups = {k: c for k, c in seen.items() if c > 1}
    status = "FAIL" if dups else "PASS"
    checks.append((
        "DUPLICATE", status,
        f"ontology_disease_variant duplicates: {dups}" if dups else
        "No duplicate normalized variants within any dimension for this disease.",
        len(dups), 0,
    ))

    # RELATIONSHIP_INTEGRITY: no duplicate applicability edge
    edges = db.query(OntologyConceptVariantApplicability).filter_by(disease_id=disease.id).all()
    edge_seen: Dict[Tuple[str, object, object, str], int] = {}
    for e in edges:
        key = (e.concept_type, e.concept_id, e.variant_id, e.applicability_type)
        edge_seen[key] = edge_seen.get(key, 0) + 1
    edge_dups = {k: c for k, c in edge_seen.items() if c > 1}
    status = "FAIL" if edge_dups else "PASS"
    checks.append((
        "RELATIONSHIP_INTEGRITY", status,
        f"ontology_concept_variant_applicability duplicate edges: {len(edge_dups)}" if edge_dups else
        "No duplicate applicability edges for this disease.",
        len(edge_dups), 0,
    ))

    return checks


def populate_validation_results(db: Session, diseases: Dict[str, OntologyDisease]) -> int:
    inserted = 0
    for disease in diseases.values():
        checks = _run_duplicate_and_integrity_checks(db, disease)
        for validation_type, status, details, error_count, warning_count in checks:
            existing = (
                db.query(OntologyDiseaseValidationResult)
                .filter_by(disease_id=disease.id, validation_type=validation_type)
                .one_or_none()
            )
            if existing is not None:
                existing.validation_status = status
                existing.details = details
                existing.error_count = error_count
                existing.warning_count = warning_count
                existing.validator_version = "clinical-reasoning-v1"
                continue
            db.add(
                OntologyDiseaseValidationResult(
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    validation_type=validation_type,
                    validation_status=status,
                    details=details,
                    error_count=error_count,
                    warning_count=warning_count,
                    validator_version="clinical-reasoning-v1",
                )
            )
            inserted += 1
    db.flush()
    return inserted


DEFAULT_ACCEPTANCE_EXPORT_PATH = (
    Path(__file__).resolve().parent.parent / "artifacts" / "neurologic_five_tier_acceptance_baseline.json"
)


def _concept_lookup(db: Session) -> Dict[Tuple[str, uuid.UUID], Dict[str, object]]:
    """Build a {(concept_type, concept_id): {name, domain}} map covering every
    row in every CONCEPT_DOMAINS-registered table, scoped to nothing in
    particular (concept ids are globally unique per table) so any
    applicability row's concept_type/concept_id can be resolved to its
    stored name -- read-only, no writes."""
    lookup: Dict[Tuple[str, uuid.UUID], Dict[str, object]] = {}
    for model_cls, concept_type, name_attr, _requires_evidence in CONCEPT_DOMAINS:
        name_col = getattr(model_cls, name_attr)
        for row_id, row_name in db.query(model_cls.id, name_col).all():
            lookup[(concept_type, row_id)] = {"name": row_name, "domain": concept_type}
    return lookup


def _variant_parent_path(
    variant: OntologyDiseaseVariant, variants_by_id: Dict[uuid.UUID, OntologyDiseaseVariant]
) -> List[str]:
    """Return the chain of variant names from the root ancestor down to
    (and including) this variant. Detects/breaks cycles defensively (a
    cycle would otherwise infinite-loop) rather than ever raising."""
    chain: List[str] = []
    seen: set = set()
    current: Optional[OntologyDiseaseVariant] = variant
    while current is not None and current.id not in seen:
        chain.append(current.variant_name)
        seen.add(current.id)
        current = variants_by_id.get(current.parent_variant_id) if current.parent_variant_id else None
    chain.reverse()
    return chain


def export_five_tier_acceptance_baseline(db: Session) -> Dict[str, object]:
    """Generate the five-tier Neurologic acceptance baseline directly from
    the populated database (never hand-authored). Read-only -- issues no
    writes. Includes every active Tier 4 variant and every active Tier 5
    applicability edge for the six approved Neurologic diseases, plus a
    grouped-by-hierarchy view (Body System -> Disease Family -> Canonical
    Disease -> Variant Dimension -> Tier 4 Variant -> Tier 5 Domain ->
    Tier 5 Atomic Concept)."""
    diseases = _resolve_diseases(db)
    concept_lookup = _concept_lookup(db)

    all_variants: List[OntologyDiseaseVariant] = (
        db.query(OntologyDiseaseVariant)
        .filter(OntologyDiseaseVariant.disease_id.in_([d.id for d in diseases.values()]))
        .all()
    )
    variants_by_id: Dict[uuid.UUID, OntologyDiseaseVariant] = {v.id: v for v in all_variants}

    all_edges: List[OntologyConceptVariantApplicability] = (
        db.query(OntologyConceptVariantApplicability)
        .filter(OntologyConceptVariantApplicability.disease_id.in_([d.id for d in diseases.values()]))
        .all()
    )
    edges_by_variant: Dict[uuid.UUID, List[OntologyConceptVariantApplicability]] = {}
    for edge in all_edges:
        edges_by_variant.setdefault(edge.variant_id, []).append(edge)

    export_variants: List[Dict[str, object]] = []
    export_applicability: List[Dict[str, object]] = []
    grouped: Dict[str, object] = {}

    for disease_name, disease in diseases.items():
        family: OntologyDiseaseFamily = disease.disease_family
        system: OntologyBodySystem = family.body_system

        system_node = grouped.setdefault(
            system.system_name, {"disease_families": {}}
        )
        family_node = system_node["disease_families"].setdefault(
            family.family_name, {"diseases": {}}
        )
        disease_node = family_node["diseases"].setdefault(
            disease_name, {"variant_dimensions": {}}
        )

        disease_variants = [v for v in all_variants if v.disease_id == disease.id]
        for variant in disease_variants:
            parent_path = _variant_parent_path(variant, variants_by_id)
            full_path_tier4 = [system.system_name, family.family_name, disease_name] + parent_path

            variant_record = {
                "id": str(variant.id),
                "disease_id": str(variant.disease_id),
                "parent_variant_id": str(variant.parent_variant_id) if variant.parent_variant_id else None,
                "variant_name": variant.variant_name,
                "normalized_name": variant.normalized_name,
                "variant_dimension": variant.variant_dimension,
                "variant_code": variant.variant_code,
                "description": variant.description,
                "clinical_significance": variant.clinical_significance,
                "hospice_relevance": variant.hospice_relevance,
                "evidence_requirement": variant.evidence_requirement,
                "source_reference": variant.source_reference,
                "active": variant.active,
                "path": full_path_tier4,
            }
            export_variants.append(variant_record)

            dim_node = disease_node["variant_dimensions"].setdefault(
                variant.variant_dimension, {"variants": {}}
            )
            variant_node = dim_node["variants"].setdefault(
                variant.variant_name, {"variant": variant_record, "tier5_domains": {}}
            )

            for edge in edges_by_variant.get(variant.id, []):
                concept_info = concept_lookup.get((edge.concept_type, edge.concept_id))
                concept_name = concept_info["name"] if concept_info else None
                full_path_tier5 = full_path_tier4 + [edge.concept_type, concept_name]

                edge_record = {
                    "id": str(edge.id),
                    "disease_id": str(edge.disease_id),
                    "concept_type": edge.concept_type,
                    "concept_id": str(edge.concept_id),
                    "concept_name": concept_name,
                    "concept_domain": edge.concept_type,
                    "variant_id": str(edge.variant_id),
                    "variant_name": variant.variant_name,
                    "variant_dimension": variant.variant_dimension,
                    "applicability_type": edge.applicability_type,
                    "description": edge.description,
                    "evidence_requirement": edge.evidence_requirement,
                    "active": edge.active,
                    "path": full_path_tier5,
                }
                export_applicability.append(edge_record)

                domain_node = variant_node["tier5_domains"].setdefault(edge.concept_type, {"concepts": {}})
                domain_node["concepts"].setdefault(concept_name or edge.concept_id.hex, edge_record)

    return {
        "diseases": sorted(diseases.keys()),
        "tier4_variant_count": len(export_variants),
        "tier5_applicability_count": len(export_applicability),
        "variants": export_variants,
        "applicability": export_applicability,
        "grouped": grouped,
    }


def write_acceptance_baseline_export(db: Session, path: Optional[Path] = None) -> Path:
    """Generate the acceptance baseline export and write it to disk as
    pretty-printed JSON. Returns the path written to."""
    target = path or DEFAULT_ACCEPTANCE_EXPORT_PATH
    payload = export_five_tier_acceptance_baseline(db)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    return target


def run(db: Session) -> Dict[str, object]:
    """Run the full Neurologic Clinical Reasoning Completion build against
    the given session. Does not commit -- caller controls the transaction
    boundary. Safe to call repeatedly; returns 0 new rows on a fully
    idempotent re-run for every counter."""
    diseases = _resolve_diseases(db)

    new_concept_counts = populate_new_concepts(db, diseases)
    variants_inserted, variant_by_key = populate_variants(db, diseases)
    applicability_inserted, unresolved = populate_applicability(db, diseases, variant_by_key)
    variant_evidence_inserted = populate_variant_evidence_rules(db, diseases)
    # Reuses the already-committed Phase 2 evidence-rule populator so every
    # NEW Tier 5 concept (symptom/finding/complication) added above also
    # receives an evidence rule -- idempotent, skips rows that already have
    # one from Phase 2.
    concept_evidence_inserted = populate_evidence_rules(db, diseases)
    validation_inserted = populate_validation_results(db, diseases)

    counts: Dict[str, object] = {
        **new_concept_counts,
        "variants_inserted": variants_inserted,
        "applicability_edges_inserted": applicability_inserted,
        "unresolved_applicability_defs": unresolved,
        "variant_evidence_rules_inserted": variant_evidence_inserted,
        "concept_evidence_rules_inserted": concept_evidence_inserted,
        "validation_results_inserted": validation_inserted,
    }
    return counts


def main() -> None:
    db = SessionLocal()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "export":
            path = write_acceptance_baseline_export(db)
            print(f"acceptance_export_path: {path}")
        else:
            counts = run(db)
            db.commit()
            for label, value in counts.items():
                print(f"{label}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
