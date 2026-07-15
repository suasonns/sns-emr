--
-- PostgreSQL database dump
--

\restrict legXScc9SU8MzGemLrSZVGnee0IUOB43fYrGhbCAVIoEZlb8IVnXbBjMoCEdqfL

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: core; Type: SCHEMA; Schema: -; Owner: sns
--

CREATE SCHEMA core;


ALTER SCHEMA core OWNER TO sns;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: membership_role; Type: TYPE; Schema: core; Owner: sns
--

CREATE TYPE core.membership_role AS ENUM (
    'ADMIN',
    'STAFF',
    'READ_ONLY'
);


ALTER TYPE core.membership_role OWNER TO sns;

--
-- Name: tenant_event_type; Type: TYPE; Schema: core; Owner: sns
--

CREATE TYPE core.tenant_event_type AS ENUM (
    'TENANT_CREATED',
    'SCHEMA_CREATED',
    'TENANT_ACTIVATED',
    'TENANT_SUSPENDED',
    'TENANT_ARCHIVED'
);


ALTER TYPE core.tenant_event_type OWNER TO sns;

--
-- Name: tenant_status; Type: TYPE; Schema: core; Owner: sns
--

CREATE TYPE core.tenant_status AS ENUM (
    'PROVISIONING',
    'ACTIVE',
    'SUSPENDED',
    'ARCHIVED'
);


ALTER TYPE core.tenant_status OWNER TO sns;

--
-- Name: user_status; Type: TYPE; Schema: core; Owner: sns
--

CREATE TYPE core.user_status AS ENUM (
    'ACTIVE',
    'DISABLED'
);


ALTER TYPE core.user_status OWNER TO sns;

--
-- Name: assessment_discipline_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.assessment_discipline_enum AS ENUM (
    'RN',
    'MSW',
    'SC',
    'MD',
    'NP',
    'LVN',
    'CHHA'
);


ALTER TYPE public.assessment_discipline_enum OWNER TO sns;

--
-- Name: assessment_risk_level_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.assessment_risk_level_enum AS ENUM (
    'LOW',
    'MODERATE',
    'HIGH'
);


ALTER TYPE public.assessment_risk_level_enum OWNER TO sns;

--
-- Name: assessment_status_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.assessment_status_enum AS ENUM (
    'DRAFT',
    'SIGNED',
    'VOIDED'
);


ALTER TYPE public.assessment_status_enum OWNER TO sns;

--
-- Name: assessment_type_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.assessment_type_enum AS ENUM (
    'RN_ICA',
    'MSW_ICA',
    'SC_ICA',
    'RN_BEREAVEMENT_BASELINE',
    'BEREAVEMENT_ASSESSMENT'
);


ALTER TYPE public.assessment_type_enum OWNER TO sns;

--
-- Name: assignment_discipline_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.assignment_discipline_enum AS ENUM (
    'MD',
    'DO',
    'MEDICAL_DIRECTOR',
    'ATTENDING_PHYSICIAN',
    'NP',
    'PA',
    'RN',
    'LVN',
    'LPN',
    'CHHA',
    'AIDE',
    'SW',
    'MSW',
    'BSW',
    'LCSW',
    'SC',
    'CHAPLAIN',
    'BEREAVEMENT_COORDINATOR',
    'PHARMACIST',
    'DIETITIAN',
    'RESPIRATORY_THERAPIST',
    'ADMIN',
    'EXECUTIVE_DIRECTOR',
    'ADMINISTRATOR',
    'DIRECTOR',
    'CLINICAL_DIRECTOR',
    'DPCS',
    'HR',
    'BILLING',
    'ACCOUNTING',
    'INTAKE',
    'CASE_MANAGER',
    'ACHC_SURVEYOR',
    'CDPH_SURVEYOR',
    'DHS_SURVEYOR',
    'CMS_SURVEYOR',
    'JOINT_COMMISSION_SURVEYOR',
    'CHAP_SURVEYOR',
    'SURVEYOR',
    'CONSULTANT',
    'VOLUNTEER_COORDINATOR',
    'VOLUNTEER',
    'DRIVER',
    'INTERPRETER',
    'HOUSEKEEPER'
);


ALTER TYPE public.assignment_discipline_enum OWNER TO sns;

--
-- Name: benefit_type_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.benefit_type_enum AS ENUM (
    'INITIAL',
    'RECERT'
);


ALTER TYPE public.benefit_type_enum OWNER TO sns;

--
-- Name: bereavement_case_status; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.bereavement_case_status AS ENUM (
    'ACTIVE',
    'CLOSED'
);


ALTER TYPE public.bereavement_case_status OWNER TO sns;

--
-- Name: bereavement_decline_reason; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.bereavement_decline_reason AS ENUM (
    'FAMILY_DECLINED_SERVICE',
    'SERVICE_NOT_DESIRED',
    'STAFF_UNAVAILABLE',
    'CULTURAL_PREFERENCE'
);


ALTER TYPE public.bereavement_decline_reason OWNER TO sns;

--
-- Name: bereavement_role; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.bereavement_role AS ENUM (
    'MSW',
    'SC',
    'RN'
);


ALTER TYPE public.bereavement_role OWNER TO sns;

--
-- Name: bereavement_task_status; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.bereavement_task_status AS ENUM (
    'PENDING',
    'COMPLETED',
    'OVERDUE'
);


ALTER TYPE public.bereavement_task_status OWNER TO sns;

--
-- Name: bereavement_task_subtype; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.bereavement_task_subtype AS ENUM (
    'SYMPATHY_CARD',
    'CARD_30_DAY',
    'CARD_60_DAY',
    'CARD_90_DAY',
    'ANNIVERSARY_CARD',
    'BEREAVEMENT_CALL',
    'BEREAVEMENT_COUNSELING'
);


ALTER TYPE public.bereavement_task_subtype OWNER TO sns;

--
-- Name: care_setting_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.care_setting_enum AS ENUM (
    'HOME',
    'ALF',
    'BOARD_AND_CARE',
    'SNF',
    'HOSPITAL',
    'INPATIENT_HOSPICE',
    'RESIDENTIAL_CARE_FACILITY',
    'CORRECTIONAL_FACILITY',
    'HOMELESS_SHELTER',
    'TEMPORARY_RELOCATION',
    'OTHER'
);


ALTER TYPE public.care_setting_enum OWNER TO sns;

--
-- Name: completion_reference_type_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.completion_reference_type_enum AS ENUM (
    'VISIT',
    'NOTE'
);


ALTER TYPE public.completion_reference_type_enum OWNER TO sns;

--
-- Name: event_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.event_type AS ENUM (
    'VISIT',
    'ADMISSION',
    'DISCHARGE'
);


ALTER TYPE public.event_type OWNER TO postgres;

--
-- Name: form_type_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.form_type_enum AS ENUM (
    'AFTER_DEATH',
    'AFTER_HOURS',
    'ANCILLARY_SUPPORT',
    'ASSESS',
    'BEREAVEMENT_VISIT',
    'DEATH_VISIT',
    'DECLINED_VISIT',
    'MISSED_VISIT',
    'OFFICE_HOURS',
    'ON_CALL_TRIAGE',
    'RESPITE_RELIEF',
    'SUPV_VISIT_ONLY',
    'VOLUNTEER_SUPPORT',
    'WEEKENDS',
    'SHORT_FORM',
    'PRE_ADMIT_EVAL'
);


ALTER TYPE public.form_type_enum OWNER TO sns;

--
-- Name: idg_discipline; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.idg_discipline AS ENUM (
    'RN',
    'MD',
    'MSW',
    'SC',
    'LVN',
    'NP'
);


ALTER TYPE public.idg_discipline OWNER TO sns;

--
-- Name: idg_participation_status_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.idg_participation_status_enum AS ENUM (
    'PRESENT',
    'NOT_PRESENT',
    'EXCUSED'
);


ALTER TYPE public.idg_participation_status_enum OWNER TO sns;

--
-- Name: idg_status_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.idg_status_enum AS ENUM (
    'SCHEDULED',
    'IN_PROGRESS',
    'COMPLETED'
);


ALTER TYPE public.idg_status_enum OWNER TO sns;

--
-- Name: level_of_care; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.level_of_care AS ENUM (
    'ROUTINE_HOME_CARE',
    'CONTINUOUS_HOME_CARE',
    'GENERAL_INPATIENT',
    'RESPITE'
);


ALTER TYPE public.level_of_care OWNER TO postgres;

--
-- Name: reg_artifact_type_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.reg_artifact_type_enum AS ENUM (
    'PDF',
    'CSV',
    'JSON'
);


ALTER TYPE public.reg_artifact_type_enum OWNER TO sns;

--
-- Name: reg_report_status_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.reg_report_status_enum AS ENUM (
    'DRAFT',
    'CERTIFIED',
    'LOCKED'
);


ALTER TYPE public.reg_report_status_enum OWNER TO sns;

--
-- Name: reg_report_type_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.reg_report_type_enum AS ENUM (
    'SIERA_ALERTS',
    'VOLUNTEER_ANNUAL',
    'CMS_ANNUAL'
);


ALTER TYPE public.reg_report_type_enum OWNER TO sns;

--
-- Name: safety_responsibility_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.safety_responsibility_enum AS ENUM (
    'HOSPICE_MANAGED',
    'FACILITY_MANAGED'
);


ALTER TYPE public.safety_responsibility_enum OWNER TO sns;

--
-- Name: task_origin_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.task_origin_enum AS ENUM (
    'RULE',
    'VISIT',
    'PERIODIC',
    'MANUAL'
);


ALTER TYPE public.task_origin_enum OWNER TO sns;

--
-- Name: task_status_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.task_status_enum AS ENUM (
    'OPEN',
    'OVERDUE',
    'COMPLETED',
    'CANCELLED',
    'ESCALATION_REQUIRED'
);


ALTER TYPE public.task_status_enum OWNER TO sns;

--
-- Name: task_type_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.task_type_enum AS ENUM (
    'POC_UPDATE',
    'CLINICAL_REVIEW_REQUIRED',
    'CLINICAL_FOLLOWUP'
);


ALTER TYPE public.task_type_enum OWNER TO sns;

--
-- Name: tasks_completion_ref_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.tasks_completion_ref_enum AS ENUM (
    'VISIT',
    'NOTE',
    'ORDER',
    'IDG_MEETING',
    'CERTIFICATION',
    'F2F_ENCOUNTER',
    'PSYCHOSOCIAL_NOTE',
    'SPIRITUAL_NOTE'
);


ALTER TYPE public.tasks_completion_ref_enum OWNER TO sns;

--
-- Name: tasks_completion_ref_enum_v2; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.tasks_completion_ref_enum_v2 AS ENUM (
    'VISIT',
    'CLINICAL_NOTE',
    'DOCUMENT',
    'NOTE',
    'PSYCHOSOCIAL_SUPPORT_NOTE',
    'SPIRITUAL_CARE_NOTE'
);


ALTER TYPE public.tasks_completion_ref_enum_v2 OWNER TO sns;

--
-- Name: tasks_discipline_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.tasks_discipline_enum AS ENUM (
    'RN',
    'MD',
    'NP',
    'SW',
    'CHAPLAIN',
    'AIDE',
    'F2F',
    'MSW',
    'BSW',
    'LCSW',
    'SC',
    'CHHA',
    'LVN'
);


ALTER TYPE public.tasks_discipline_enum OWNER TO sns;

--
-- Name: tasks_origin_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.tasks_origin_enum AS ENUM (
    'ADMISSION',
    'PERIODIC',
    'MANUAL',
    'SYSTEM'
);


ALTER TYPE public.tasks_origin_enum OWNER TO sns;

--
-- Name: tasks_regulatory_basis_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.tasks_regulatory_basis_enum AS ENUM (
    'IDG',
    'VISIT_FREQUENCY',
    'F2F',
    'CERTIFICATION',
    'ADMISSION_REQUIREMENT',
    'POC_UPDATE',
    'IDG_15_DAY',
    'IDG_REVIEW',
    'CONDITION_TRIGGER',
    'POC_TRIGGER'
);


ALTER TYPE public.tasks_regulatory_basis_enum OWNER TO sns;

--
-- Name: tasks_status_enum; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.tasks_status_enum AS ENUM (
    'PENDING',
    'COMPLETED',
    'OVERDUE',
    'ESCALATED',
    'WAIVED',
    'IN_PROGRESS'
);


ALTER TYPE public.tasks_status_enum OWNER TO sns;

--
-- Name: tasks_task_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.tasks_task_type_enum AS ENUM (
    'SFV',
    'OTHER',
    'POC_UPDATE',
    'IDG_REVIEW',
    'CERTIFICATION',
    'RECERTIFICATION',
    'F2F',
    'POC_NONCOMPLIANT_STRUCTURE',
    'POC_REVIEW_REQUIRED',
    'POC_OUT_OF_SCOPE_CARE',
    'POC_STALE_REVIEW',
    'POC_PHYSICIAN_REVIEW_REQUIRED',
    'IDG_POC_REVIEW',
    'INITIAL_RN_ICA',
    'NOE_DUE',
    'INITIAL_MSW_ICA',
    'INITIAL_SC_ICA',
    'INITIAL_BEREAVEMENT',
    'MSW_REOFFER',
    'CHAPLAIN_REOFFER',
    'AIDE_REOFFER',
    'CLINICAL_REVIEW_REQUIRED',
    'CLINICAL_FOLLOWUP',
    'PAIN_MANAGEMENT',
    'WOUND_CARE',
    'RESPIRATORY_MONITORING',
    'PSYCHOSOCIAL_SUPPORT',
    'SPIRITUAL_SUPPORT',
    'HUV1',
    'HUV2'
);


ALTER TYPE public.tasks_task_type_enum OWNER TO postgres;

--
-- Name: visit_schedule_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.visit_schedule_type AS ENUM (
    'ROUTINE',
    'PRN',
    'ON_CALL'
);


ALTER TYPE public.visit_schedule_type OWNER TO postgres;

--
-- Name: visit_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.visit_type AS ENUM (
    'SN',
    'MSW',
    'CHAPLAIN',
    'AIDE'
);


ALTER TYPE public.visit_type OWNER TO postgres;

--
-- Name: volunteer_activity_type; Type: TYPE; Schema: public; Owner: sns
--

CREATE TYPE public.volunteer_activity_type AS ENUM (
    'ADMIN',
    'DIRECT_PATIENT_SUPPORT'
);


ALTER TYPE public.volunteer_activity_type OWNER TO sns;

--
-- Name: prevent_tenant_delete(); Type: FUNCTION; Schema: core; Owner: sns
--

CREATE FUNCTION core.prevent_tenant_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            RAISE EXCEPTION 'Tenants may not be deleted (audit integrity)';
        END;
        $$;


ALTER FUNCTION core.prevent_tenant_delete() OWNER TO sns;

--
-- Name: seed_love_and_faith_tenant(); Type: FUNCTION; Schema: core; Owner: postgres
--

CREATE FUNCTION core.seed_love_and_faith_tenant() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  INSERT INTO core.tenants (
    id,
    name,
    tenant_code,
    display_name,
    schema_name,
    status,
    created_at,
    activated_at
  )
  VALUES (
    '01271980-0000-0000-0000-000005101977',
    'Love and Faith Hospice Services Inc',
    'LOVEFAITH',
    'Love and Faith Hospice Services Inc',
    'love_and_faith',
    'ACTIVE'::core.tenant_status,
    NOW(),
    NOW()
  )
  ON CONFLICT (id) DO NOTHING;
END;
$$;


ALTER FUNCTION core.seed_love_and_faith_tenant() OWNER TO postgres;

--
-- Name: enforce_patient_status_transition(); Type: FUNCTION; Schema: public; Owner: sns
--

CREATE FUNCTION public.enforce_patient_status_transition() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            -- Allow no-op
            IF NEW.status = OLD.status THEN
                RETURN NEW;
            END IF;

            -- ACTIVE may transition to DISCHARGED or DECEASED
            IF OLD.status = 'ACTIVE'
               AND NEW.status IN ('DISCHARGED', 'DECEASED') THEN
                RETURN NEW;
            END IF;

            -- All other transitions are illegal
            RAISE EXCEPTION
                'Illegal patient status transition: % ΓåÆ %',
                OLD.status, NEW.status;
        END;
        $$;


ALTER FUNCTION public.enforce_patient_status_transition() OWNER TO sns;

--
-- Name: prevent_child_modification_when_report_locked(); Type: FUNCTION; Schema: public; Owner: sns
--

CREATE FUNCTION public.prevent_child_modification_when_report_locked() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        DECLARE
            report_uuid uuid;
        BEGIN
            -- Superuser override
            IF current_setting('app.superuser_override', true) = 'true' THEN
                RETURN COALESCE(NEW, OLD);
            END IF;

            IF TG_OP = 'DELETE' THEN
                report_uuid := OLD.report_id;
            ELSE
                report_uuid := NEW.report_id;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM regulatory_reports
                WHERE id = report_uuid
                  AND status = 'LOCKED'
            ) THEN
                RAISE EXCEPTION 'Report is LOCKED and cannot be modified';
            END IF;

            RETURN COALESCE(NEW, OLD);
        END;
        $$;


ALTER FUNCTION public.prevent_child_modification_when_report_locked() OWNER TO sns;

--
-- Name: prevent_report_update_when_locked(); Type: FUNCTION; Schema: public; Owner: sns
--

CREATE FUNCTION public.prevent_report_update_when_locked() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            -- Superuser override
            IF current_setting('app.superuser_override', true) = 'true' THEN
                RETURN NEW;
            END IF;

            -- Default behavior: LOCKED is immutable
            IF OLD.status = 'LOCKED' THEN
                RAISE EXCEPTION 'Locked report header cannot be modified';
            END IF;

            RETURN NEW;
        END;
        $$;


ALTER FUNCTION public.prevent_report_update_when_locked() OWNER TO sns;

--
-- Name: set_bereavement_task_decline_flag(); Type: FUNCTION; Schema: public; Owner: sns
--

CREATE FUNCTION public.set_bereavement_task_decline_flag() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        UPDATE bereavement_tasks
        SET decline_record_exists = true,
            updated_at = now()
        WHERE id = NEW.bereavement_task_id;

        RETURN NEW;
    END;
    $$;


ALTER FUNCTION public.set_bereavement_task_decline_flag() OWNER TO sns;

--
-- Name: update_guardrail_policies_updated_at(); Type: FUNCTION; Schema: public; Owner: sns
--

CREATE FUNCTION public.update_guardrail_policies_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$;


ALTER FUNCTION public.update_guardrail_policies_updated_at() OWNER TO sns;

--
-- Name: update_guardrail_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_guardrail_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_guardrail_updated_at() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: billing_organizations; Type: TABLE; Schema: core; Owner: sns
--

CREATE TABLE core.billing_organizations (
    id uuid NOT NULL,
    name text NOT NULL,
    capability_tier text NOT NULL,
    active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_billing_organizations_ck_billing_org_capability_tier CHECK ((capability_tier = ANY (ARRAY['AUTOMATED'::text, 'MANUAL'::text])))
);


ALTER TABLE core.billing_organizations OWNER TO sns;

--
-- Name: tenant_events; Type: TABLE; Schema: core; Owner: sns
--

CREATE TABLE core.tenant_events (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    event_type core.tenant_event_type NOT NULL,
    event_at timestamp with time zone DEFAULT now() NOT NULL,
    actor_user_id uuid,
    details_json jsonb
);


ALTER TABLE core.tenant_events OWNER TO sns;

--
-- Name: tenants; Type: TABLE; Schema: core; Owner: sns
--

CREATE TABLE core.tenants (
    id uuid NOT NULL,
    tenant_code character varying(50) NOT NULL,
    display_name character varying(255) NOT NULL,
    schema_name character varying(255) NOT NULL,
    status core.tenant_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    activated_at timestamp with time zone,
    archived_at timestamp with time zone,
    billing_organization_id uuid
);


ALTER TABLE core.tenants OWNER TO sns;

--
-- Name: user_tenants; Type: TABLE; Schema: core; Owner: sns
--

CREATE TABLE core.user_tenants (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    role core.membership_role NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE core.user_tenants OWNER TO sns;

--
-- Name: users; Type: TABLE; Schema: core; Owner: sns
--

CREATE TABLE core.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    status core.user_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login_at timestamp with time zone
);


ALTER TABLE core.users OWNER TO sns;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.accounts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.accounts OWNER TO sns;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO sns;

--
-- Name: amendments; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.amendments (
    clinical_note_id uuid NOT NULL,
    author_id uuid NOT NULL,
    reason character varying NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone,
    id uuid NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    original_finalized_at timestamp without time zone
);


ALTER TABLE public.amendments OWNER TO sns;

--
-- Name: diagnoses; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.diagnoses (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    diagnosis_name text NOT NULL,
    onset_date timestamp without time zone NOT NULL,
    infection_source text NOT NULL,
    created_by uuid,
    created_at timestamp without time zone
);


ALTER TABLE public.diagnoses OWNER TO sns;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.orders (
    id uuid NOT NULL,
    visit_id uuid,
    order_text text,
    created_at timestamp without time zone,
    order_category text,
    order_name text,
    medication_class text,
    indication text,
    diagnosis_id uuid,
    status text DEFAULT 'ACTIVE'::text NOT NULL,
    discontinued_at timestamp with time zone,
    discontinued_by uuid,
    discontinued_reason text,
    ordered_by uuid,
    ordered_at timestamp with time zone,
    signed_by uuid,
    signed_at timestamp with time zone,
    route text,
    dose text,
    unit text,
    frequency text,
    CONSTRAINT check_discontinued_requires_reason CHECK (
CASE
    WHEN (status = 'DISCONTINUED'::text) THEN ((discontinued_at IS NOT NULL) AND (discontinued_reason IS NOT NULL) AND (btrim(discontinued_reason) <> ''::text))
    ELSE true
END),
    CONSTRAINT check_orders_base_completeness CHECK (
CASE
    WHEN (order_category = ANY (ARRAY['MEDICATION'::text, 'TREATMENT'::text, 'DME'::text])) THEN ((order_name IS NOT NULL) AND (btrim(order_name) <> ''::text) AND (ordered_at IS NOT NULL))
    ELSE true
END),
    CONSTRAINT check_orders_medication_completeness CHECK (
CASE
    WHEN (order_category = 'MEDICATION'::text) THEN ((indication IS NOT NULL) AND (btrim(indication) <> ''::text) AND (dose IS NOT NULL) AND (btrim(dose) <> ''::text) AND (route IS NOT NULL) AND (btrim(route) <> ''::text) AND (frequency IS NOT NULL) AND (btrim(frequency) <> ''::text))
    ELSE true
END),
    CONSTRAINT check_orders_require_diagnosis CHECK (
CASE
    WHEN (order_category = ANY (ARRAY['MEDICATION'::text, 'TREATMENT'::text, 'DME'::text])) THEN (diagnosis_id IS NOT NULL)
    ELSE true
END),
    CONSTRAINT check_orders_timeline_integrity CHECK ((((signed_at IS NULL) OR (ordered_at IS NULL) OR (signed_at >= ordered_at)) AND ((discontinued_at IS NULL) OR (ordered_at IS NULL) OR (discontinued_at >= ordered_at)))),
    CONSTRAINT check_orders_treatment_dme_completeness CHECK (
CASE
    WHEN (order_category = ANY (ARRAY['TREATMENT'::text, 'DME'::text])) THEN ((indication IS NOT NULL) AND (btrim(indication) <> ''::text))
    ELSE true
END),
    CONSTRAINT ck_orders_ck_orders_order_category CHECK (((order_category IS NULL) OR (order_category = ANY (ARRAY['MEDICATION'::text, 'TREATMENT'::text, 'DME'::text, 'OTHER'::text])))),
    CONSTRAINT ck_orders_ck_orders_status CHECK ((status = ANY (ARRAY['ACTIVE'::text, 'DISCONTINUED'::text, 'COMPLETED'::text])))
);


ALTER TABLE public.orders OWNER TO sns;

--
-- Name: antibiotics_audit_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.antibiotics_audit_view AS
 SELECT o.id,
    o.visit_id,
    o.order_name,
    o.medication_class,
    o.indication,
    d.patient_id,
    d.diagnosis_name,
    d.infection_source,
    d.onset_date,
    o.status,
    o.ordered_at,
    o.signed_at,
    o.discontinued_at,
    o.discontinued_reason
   FROM (public.orders o
     LEFT JOIN public.diagnoses d ON ((o.diagnosis_id = d.id)))
  WHERE ((o.order_category = 'MEDICATION'::text) AND (o.medication_class = 'ANTIBIOTIC'::text));


ALTER VIEW public.antibiotics_audit_view OWNER TO postgres;

--
-- Name: assessment_discrepancies; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.assessment_discrepancies (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tenant_id uuid,
    patient_id uuid NOT NULL,
    domain character varying(50) NOT NULL,
    baseline_assessment_id uuid,
    comparing_assessment_id uuid,
    discrepancy_summary text,
    requires_idg_reconciliation boolean DEFAULT true NOT NULL,
    resolved boolean DEFAULT false NOT NULL,
    resolved_at timestamp with time zone,
    resolved_in_idg_meeting_id uuid,
    resolution_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    resolution_type character varying(30),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    CONSTRAINT ck_assessment_discrepancies_ck_discrepancies_resolved_r_3a93 CHECK (((resolved = false) OR (resolved_at IS NOT NULL)))
);


ALTER TABLE public.assessment_discrepancies OWNER TO sns;

--
-- Name: assessment_references; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.assessment_references (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    assessment_id uuid NOT NULL,
    referenced_assessment_id uuid NOT NULL,
    reference_kind character varying(32) NOT NULL,
    reviewed_ack boolean DEFAULT false NOT NULL,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    CONSTRAINT ck_assessment_references_ck_assessment_references_ack_r_fa9f CHECK (((reviewed_ack = false) OR (reviewed_at IS NOT NULL)))
);


ALTER TABLE public.assessment_references OWNER TO sns;

--
-- Name: assessments; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.assessments (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tenant_id uuid,
    patient_id uuid NOT NULL,
    discipline character varying(16) NOT NULL,
    assessment_type character varying(64) NOT NULL,
    occurred_at timestamp with time zone NOT NULL,
    status character varying(16) DEFAULT 'DRAFT'::character varying NOT NULL,
    signed_at timestamp with time zone,
    signed_by uuid,
    risk_score integer,
    risk_level character varying(16),
    data_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    document_id uuid,
    visit_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    CONSTRAINT ck_assessments_ck_assessment_signed_requires_fields CHECK ((((status)::text <> 'SIGNED'::text) OR ((signed_at IS NOT NULL) AND (signed_by IS NOT NULL)))),
    CONSTRAINT ck_assessments_ck_assessments_signed_requires_signed_at CHECK ((((status)::text <> 'SIGNED'::text) OR (signed_at IS NOT NULL))),
    CONSTRAINT ck_assessments_ck_rn_baseline_must_be_rn CHECK ((((assessment_type)::text <> 'RN_BEREAVEMENT_BASELINE'::text) OR ((discipline)::text = 'RN'::text)))
);


ALTER TABLE public.assessments OWNER TO sns;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.audit_logs (
    user_id character varying NOT NULL,
    role character varying NOT NULL,
    action character varying NOT NULL,
    entity_type character varying,
    entity_id character varying,
    ip_address character varying,
    created_at timestamp without time zone,
    id uuid NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    request_id uuid,
    description text,
    metadata jsonb,
    tenant_id uuid
);


ALTER TABLE public.audit_logs OWNER TO sns;

--
-- Name: authorization_records; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.authorization_records (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    payer_name character varying NOT NULL,
    auth_status character varying NOT NULL,
    tenant_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    authorization_number character varying(100),
    service_type character varying(50),
    status character varying(32) DEFAULT 'PENDING'::character varying,
    created_by character varying(255)
);


ALTER TABLE public.authorization_records OWNER TO sns;

--
-- Name: benefit_periods; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.benefit_periods (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    start_date date NOT NULL,
    end_date date,
    is_current boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tenant_id uuid NOT NULL,
    created_by uuid,
    benefit_type character varying(32) NOT NULL,
    period_number integer NOT NULL,
    election_date date NOT NULL
);


ALTER TABLE public.benefit_periods OWNER TO sns;

--
-- Name: bereavement_cases; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.bereavement_cases (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    status public.bereavement_case_status DEFAULT 'ACTIVE'::public.bereavement_case_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.bereavement_cases OWNER TO sns;

--
-- Name: bereavement_declines; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.bereavement_declines (
    id uuid NOT NULL,
    bereavement_task_id uuid NOT NULL,
    declined_role public.bereavement_role NOT NULL,
    decline_reason public.bereavement_decline_reason NOT NULL,
    recorded_by_user_id uuid,
    recorded_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.bereavement_declines OWNER TO sns;

--
-- Name: bereavement_tasks; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.bereavement_tasks (
    id uuid NOT NULL,
    bereavement_case_id uuid NOT NULL,
    task_subtype public.bereavement_task_subtype NOT NULL,
    due_date date NOT NULL,
    status public.bereavement_task_status DEFAULT 'PENDING'::public.bereavement_task_status NOT NULL,
    primary_roles_allowed character varying(8)[] DEFAULT ARRAY['MSW'::text, 'SC'::text] NOT NULL,
    fallback_role public.bereavement_role DEFAULT 'RN'::public.bereavement_role NOT NULL,
    decline_record_exists boolean DEFAULT false NOT NULL,
    completed_by_user_id uuid,
    completed_by_role public.bereavement_role,
    completed_at timestamp with time zone,
    evidence_id uuid,
    exception_reason text,
    billable boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_bereavement_tasks_ck_bereavement_tasks_completed_req_53f4 CHECK (((status <> 'COMPLETED'::public.bereavement_task_status) OR ((evidence_id IS NOT NULL) OR (exception_reason IS NOT NULL)))),
    CONSTRAINT ck_bereavement_tasks_ck_bereavement_tasks_completed_req_bb95 CHECK (((status <> 'COMPLETED'::public.bereavement_task_status) OR ((completed_at IS NOT NULL) AND (completed_by_user_id IS NOT NULL) AND (completed_by_role IS NOT NULL)))),
    CONSTRAINT ck_bereavement_tasks_ck_bereavement_tasks_not_billable CHECK ((billable = false)),
    CONSTRAINT ck_bereavement_tasks_ck_bereavement_tasks_rn_requires_decline CHECK (((completed_by_role IS NULL) OR (completed_by_role <> 'RN'::public.bereavement_role) OR (decline_record_exists = true)))
);


ALTER TABLE public.bereavement_tasks OWNER TO sns;

--
-- Name: billing_cycles; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.billing_cycles (
    id character varying NOT NULL,
    tenant_id character varying NOT NULL,
    month integer NOT NULL,
    year integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    status character varying(32) DEFAULT 'OPEN'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    created_by character varying(255)
);


ALTER TABLE public.billing_cycles OWNER TO sns;

--
-- Name: billing_snapshot; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.billing_snapshot (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    data json NOT NULL
);


ALTER TABLE public.billing_snapshot OWNER TO sns;

--
-- Name: billing_snapshots; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.billing_snapshots (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    billing_cycle_id character varying,
    snapshot_type character varying(50) NOT NULL,
    version character varying(50),
    data json NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(255)
);


ALTER TABLE public.billing_snapshots OWNER TO sns;

--
-- Name: billing_summaries; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.billing_summaries (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    billing_cycle_id character varying NOT NULL,
    total_units integer DEFAULT 0 NOT NULL,
    total_amount integer DEFAULT 0 NOT NULL,
    risk_score integer NOT NULL,
    status character varying(32) DEFAULT 'DRAFT'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    created_by character varying(255)
);


ALTER TABLE public.billing_summaries OWNER TO sns;

--
-- Name: billing_summary; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.billing_summary (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    billing_cycle_id character varying NOT NULL,
    total_units integer NOT NULL,
    status character varying NOT NULL,
    risk_score integer NOT NULL
);


ALTER TABLE public.billing_summary OWNER TO sns;

--
-- Name: certifications; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.certifications (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    benefit_period_id uuid NOT NULL,
    cert_type character varying NOT NULL,
    signed_at timestamp without time zone NOT NULL,
    effective_date date NOT NULL,
    signed_by_role character varying NOT NULL,
    signed_by_user_id uuid,
    status character varying DEFAULT 'FINALIZED'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    certification_type character varying,
    effective_start_date date,
    effective_end_date date,
    primary_dx character varying,
    narrative text
);


ALTER TABLE public.certifications OWNER TO sns;

--
-- Name: change_of_condition; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.change_of_condition (
    id uuid NOT NULL,
    visit_id uuid,
    severity text,
    reason text,
    created_at timestamp without time zone
);


ALTER TABLE public.change_of_condition OWNER TO postgres;

--
-- Name: chha_pocs; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.chha_pocs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    status character varying DEFAULT 'draft'::character varying NOT NULL,
    effective_start date,
    effective_end date,
    frequency character varying,
    adl_scope text,
    instructions text,
    safety_precautions text,
    finalized_at timestamp without time zone,
    finalized_by uuid,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.chha_pocs OWNER TO sns;

--
-- Name: chha_visit_outcomes; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.chha_visit_outcomes (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    visit_id uuid NOT NULL,
    poc_reference_id uuid,
    tolerance_to_care character varying(50) DEFAULT 'WELL_TOLERATED'::character varying NOT NULL,
    condition_during_visit character varying(50) DEFAULT 'STABLE'::character varying NOT NULL,
    skin_outcome character varying(50) DEFAULT 'NOT_ASSESSED'::character varying NOT NULL,
    pain_or_change_observed boolean DEFAULT false NOT NULL,
    rn_notification_required boolean DEFAULT false NOT NULL,
    rn_notified boolean DEFAULT false NOT NULL,
    rn_notified_at timestamp with time zone,
    rn_notified_name character varying(255),
    caregiver_instruction_provided boolean DEFAULT false NOT NULL,
    caregiver_understanding_confirmed boolean DEFAULT false NOT NULL,
    exception_narrative text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by uuid,
    updated_by uuid
);


ALTER TABLE public.chha_visit_outcomes OWNER TO sns;

--
-- Name: chha_visit_task_results; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.chha_visit_task_results (
    id uuid NOT NULL,
    outcome_id uuid NOT NULL,
    section_code character varying(100) NOT NULL,
    task_code character varying(100) NOT NULL,
    was_assigned boolean DEFAULT true NOT NULL,
    completed boolean DEFAULT false NOT NULL,
    refused boolean DEFAULT false NOT NULL,
    not_done boolean DEFAULT false NOT NULL,
    observation_code character varying(100),
    result_note text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.chha_visit_task_results OWNER TO sns;

--
-- Name: claim_export_log; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.claim_export_log (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    billing_cycle_id character varying NOT NULL,
    file_path character varying NOT NULL,
    override_used boolean,
    override_reason character varying,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.claim_export_log OWNER TO sns;

--
-- Name: claim_export_logs; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.claim_export_logs (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    billing_cycle_id character varying NOT NULL,
    file_path character varying NOT NULL,
    export_type character varying(50),
    status character varying(32) DEFAULT 'SUCCESS'::character varying NOT NULL,
    override_used boolean DEFAULT false NOT NULL,
    override_reason character varying,
    override_approved_by character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(255)
);


ALTER TABLE public.claim_export_logs OWNER TO sns;

--
-- Name: clinical_note_versions; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.clinical_note_versions (
    id uuid NOT NULL,
    clinical_note_id uuid NOT NULL,
    version_number integer NOT NULL,
    content jsonb NOT NULL,
    amend_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    is_active boolean DEFAULT true NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_clinical_note_versions_ck_clinical_note_versions_ver_e3fb CHECK ((version_number >= 1))
);


ALTER TABLE public.clinical_note_versions OWNER TO sns;

--
-- Name: clinical_notes; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.clinical_notes (
    visit_id uuid NOT NULL,
    author_id uuid NOT NULL,
    note_type character varying NOT NULL,
    content jsonb DEFAULT '{}'::jsonb NOT NULL,
    status character varying,
    finalized_at timestamp without time zone,
    id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    finalized_by uuid,
    tenant_id uuid NOT NULL,
    finalized_role_id uuid,
    finalized_interface_id uuid,
    patient_id uuid,
    care_level character varying,
    visit_type character varying,
    visit_origin character varying,
    note_category character varying,
    encounter_type character varying,
    discipline character varying,
    encounter_date date,
    observed_data json,
    patient_reported json,
    caregiver_reported json,
    assessment json,
    interventions json,
    plan_of_care_updates json,
    needs_clarification boolean,
    red_flags json,
    audit_flags json,
    incident_required boolean,
    incident_status character varying,
    incident_id uuid,
    signed_by uuid,
    signed_at timestamp without time zone,
    current_version_id uuid,
    form_family text,
    form_key character varying(128),
    module_payload json,
    is_primary_form boolean DEFAULT true NOT NULL,
    parent_form_id uuid,
    is_primary boolean DEFAULT true NOT NULL,
    parent_note_id uuid,
    requires_countersign boolean DEFAULT false NOT NULL,
    countersigned_by uuid,
    countersigned_at timestamp with time zone,
    CONSTRAINT ck_clinical_notes_ck_bsw_finalize_requires_countersign CHECK ((((discipline)::text <> 'BSW'::text) OR ((finalized_at IS NULL) OR (countersigned_by IS NOT NULL)))),
    CONSTRAINT ck_clinical_notes_ck_bsw_requires_flag CHECK ((((discipline)::text <> 'BSW'::text) OR (requires_countersign = true))),
    CONSTRAINT ck_clinical_notes_ck_countersign_before_finalize CHECK (((countersigned_at IS NULL) OR (finalized_at IS NULL) OR (countersigned_at <= finalized_at))),
    CONSTRAINT ck_clinical_notes_ck_countersign_pair CHECK ((((countersigned_by IS NULL) AND (countersigned_at IS NULL)) OR ((countersigned_by IS NOT NULL) AND (countersigned_at IS NOT NULL)))),
    CONSTRAINT ck_clinical_notes_ck_discipline_valid CHECK (((discipline)::text = ANY ((ARRAY['RN'::character varying, 'LVN'::character varying, 'NP'::character varying, 'MD'::character varying, 'SC'::character varying, 'MSW'::character varying, 'LCSW'::character varying, 'BSW'::character varying])::text[])))
);


ALTER TABLE public.clinical_notes OWNER TO sns;

--
-- Name: communications_logs; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.communications_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid,
    channel character varying,
    direction character varying,
    subject character varying,
    body text,
    status character varying NOT NULL,
    external_reference character varying,
    sent_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    event_type character varying,
    focus_area character varying,
    event_time timestamp without time zone,
    summary text,
    details text,
    acknowledged_by uuid,
    acknowledged_at timestamp with time zone,
    verified_by uuid,
    verified_at timestamp with time zone,
    resolved_by uuid,
    resolved_at timestamp with time zone,
    CONSTRAINT ck_communications_logs_status_allowed CHECK (((status)::text = ANY ((ARRAY['RECEIVED'::character varying, 'ACKNOWLEDGED'::character varying, 'VERIFIED'::character varying, 'RESOLVED'::character varying])::text[])))
);


ALTER TABLE public.communications_logs OWNER TO sns;

--
-- Name: continuous_care_events; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.continuous_care_events (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    reason character varying,
    tenant_id uuid,
    visit_id uuid,
    service_level character varying(50) DEFAULT 'CONTINUOUS_CARE'::character varying,
    status character varying(32) DEFAULT 'ACTIVE'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.continuous_care_events OWNER TO sns;

--
-- Name: diagnosis_discrepancies; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.diagnosis_discrepancies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    referral_primary text,
    rn_primary text,
    cti_primary text,
    status text DEFAULT 'OPEN'::text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_diagnosis_discrepancies_ck_dx_disc_status CHECK ((status = ANY (ARRAY['OPEN'::text, 'ACKNOWLEDGED'::text, 'RESOLVED'::text])))
);


ALTER TABLE public.diagnosis_discrepancies OWNER TO sns;

--
-- Name: diagnosis_reconciliations; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.diagnosis_reconciliations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    discrepancy_id uuid NOT NULL,
    resolution_choice text NOT NULL,
    narrative text,
    attested_by_account_id uuid NOT NULL,
    attested_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_diagnosis_reconciliations_ck_dx_recon_choice CHECK ((resolution_choice = ANY (ARRAY['RN_MORE_ACCURATE_TERMINAL'::text, 'CTI_TERMINAL_EVENT_RN_UNDERLYING'::text, 'CONDITION_CHANGED'::text, 'BOTH_RELEVANT_PRIMARY_VS_CONTRIBUTING'::text, 'OTHER'::text])))
);


ALTER TABLE public.diagnosis_reconciliations OWNER TO sns;

--
-- Name: diagnosis_sources; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.diagnosis_sources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    source text NOT NULL,
    dx_type text NOT NULL,
    icd_code text,
    description text NOT NULL,
    documented_by_account_id uuid,
    documented_at timestamp without time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_diagnosis_sources_ck_dx_source CHECK ((source = ANY (ARRAY['REFERRAL'::text, 'RN_IA'::text, 'CTI'::text]))),
    CONSTRAINT ck_diagnosis_sources_ck_dx_type CHECK ((dx_type = ANY (ARRAY['PRIMARY'::text, 'RELATED'::text, 'SECONDARY'::text])))
);


ALTER TABLE public.diagnosis_sources OWNER TO sns;

--
-- Name: discharge_reasons; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.discharge_reasons (
    code character varying(64) NOT NULL,
    label character varying(128) NOT NULL,
    cms_category character varying(32) NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_discharge_reasons_ck_discharge_reasons_cms_category CHECK (((cms_category)::text = ANY (ARRAY[('DEATH'::character varying)::text, ('TRANSFER'::character varying)::text, ('NO_LONGER_TERMINAL'::character varying)::text, ('DISCHARGE_FOR_CAUSE'::character varying)::text, ('REVOCATION'::character varying)::text])))
);


ALTER TABLE public.discharge_reasons OWNER TO sns;

--
-- Name: discharges; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.discharges (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    discharge_reason_code character varying(64) NOT NULL,
    cms_category character varying(32) NOT NULL,
    status character varying(16) DEFAULT 'DRAFT'::character varying NOT NULL,
    effective_at timestamp with time zone,
    recorded_at timestamp with time zone DEFAULT now() NOT NULL,
    recorded_by_user_id uuid,
    transfer_destination_type character varying(32),
    transfer_destination_name character varying(128),
    transfer_destination_notes text,
    physician_discharge_order_id uuid,
    supporting_clinical_note_id uuid,
    documentation_note_id uuid,
    remediation_attempts_documented boolean DEFAULT false NOT NULL,
    patient_notified boolean DEFAULT false NOT NULL,
    medical_director_approval boolean DEFAULT false NOT NULL,
    revocation_statement_signed boolean DEFAULT false NOT NULL,
    initiated_by character varying(16),
    death_documentation_present boolean DEFAULT false NOT NULL,
    notes text,
    CONSTRAINT ck_discharges_ck_discharges_cms_category CHECK (((cms_category)::text = ANY (ARRAY[('DEATH'::character varying)::text, ('TRANSFER'::character varying)::text, ('NO_LONGER_TERMINAL'::character varying)::text, ('DISCHARGE_FOR_CAUSE'::character varying)::text, ('REVOCATION'::character varying)::text]))),
    CONSTRAINT ck_discharges_ck_discharges_death_requires_death_documentation CHECK ((((status)::text <> 'FINALIZED'::text) OR ((cms_category)::text <> 'DEATH'::text) OR (death_documentation_present = true))),
    CONSTRAINT ck_discharges_ck_discharges_finalized_requires_effectiv_3a78 CHECK ((((status)::text <> 'FINALIZED'::text) OR ((effective_at IS NOT NULL) AND (physician_discharge_order_id IS NOT NULL)))),
    CONSTRAINT ck_discharges_ck_discharges_for_cause_requires_docs CHECK ((((status)::text <> 'FINALIZED'::text) OR ((cms_category)::text <> 'DISCHARGE_FOR_CAUSE'::text) OR ((documentation_note_id IS NOT NULL) AND (remediation_attempts_documented = true) AND (patient_notified = true) AND (medical_director_approval = true)))),
    CONSTRAINT ck_discharges_ck_discharges_initiated_by CHECK (((initiated_by IS NULL) OR ((initiated_by)::text = ANY (ARRAY[('PATIENT'::character varying)::text, ('LEGAL_REP'::character varying)::text, ('HOSPICE'::character varying)::text, ('SYSTEM'::character varying)::text])))),
    CONSTRAINT ck_discharges_ck_discharges_no_longer_terminal_requires_f0ae CHECK ((((status)::text <> 'FINALIZED'::text) OR ((cms_category)::text <> 'NO_LONGER_TERMINAL'::text) OR (supporting_clinical_note_id IS NOT NULL))),
    CONSTRAINT ck_discharges_ck_discharges_revocation_requires_patient_1b13 CHECK ((((status)::text <> 'FINALIZED'::text) OR ((cms_category)::text <> 'REVOCATION'::text) OR ((revocation_statement_signed = true) AND ((initiated_by)::text = ANY (ARRAY[('PATIENT'::character varying)::text, ('LEGAL_REP'::character varying)::text]))))),
    CONSTRAINT ck_discharges_ck_discharges_status CHECK (((status)::text = ANY (ARRAY[('DRAFT'::character varying)::text, ('FINALIZED'::character varying)::text, ('VOIDED'::character varying)::text]))),
    CONSTRAINT ck_discharges_ck_discharges_transfer_destination_type CHECK (((transfer_destination_type IS NULL) OR ((transfer_destination_type)::text = ANY (ARRAY[('HOSPICE'::character varying)::text, ('PCP'::character varying)::text, ('SNF'::character varying)::text, ('HOSPITAL'::character varying)::text, ('REHAB'::character varying)::text, ('HOME_HEALTH'::character varying)::text, ('PALLIATIVE_CARE'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_discharges_ck_discharges_transfer_requires_destination_type CHECK ((((status)::text <> 'FINALIZED'::text) OR ((cms_category)::text <> 'TRANSFER'::text) OR (transfer_destination_type IS NOT NULL)))
);


ALTER TABLE public.discharges OWNER TO sns;

--
-- Name: document_idg_resolution; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.document_idg_resolution (
    document_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    resolution_status character varying(32) NOT NULL,
    resolved_by uuid NOT NULL,
    resolved_at timestamp with time zone DEFAULT now() NOT NULL,
    resolution_note text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE public.document_idg_resolution OWNER TO sns;

--
-- Name: document_notifications; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.document_notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    document_id uuid,
    notification_id uuid,
    status character varying,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    recipient_role character varying,
    recipient_user_id uuid,
    notified_at timestamp without time zone,
    acknowledged_at timestamp without time zone,
    reminder_count integer,
    last_reminder_at timestamp without time zone,
    resolution_status character varying,
    resolution_note text,
    resolved_at timestamp without time zone,
    resolved_by uuid
);


ALTER TABLE public.document_notifications OWNER TO sns;

--
-- Name: document_records; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.document_records (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    document_type character varying(64) NOT NULL,
    source character varying(32) DEFAULT 'EXTERNAL'::character varying NOT NULL,
    file_name character varying(255),
    file_path character varying(512),
    extracted_values jsonb,
    document_text text,
    is_flagged boolean DEFAULT false NOT NULL,
    flag_tier character varying(16),
    matched_rule_ids jsonb,
    uploaded_at timestamp with time zone DEFAULT now() NOT NULL,
    uploaded_by uuid
);


ALTER TABLE public.document_records OWNER TO sns;

--
-- Name: drug_aliases; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.drug_aliases (
    alias_text character varying(255) NOT NULL,
    canonical_text character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    id uuid
);


ALTER TABLE public.drug_aliases OWNER TO sns;

--
-- Name: dx_primary_policies; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.dx_primary_policies (
    id uuid NOT NULL,
    diagnosis_code character varying(64) NOT NULL,
    diagnosis_name character varying(255) NOT NULL,
    allowed_primary boolean DEFAULT true NOT NULL,
    rationale character varying(512),
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE public.dx_primary_policies OWNER TO sns;

--
-- Name: dx_primary_policy; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.dx_primary_policy (
    id uuid NOT NULL,
    tenant_id uuid,
    code_pattern character varying(16) NOT NULL,
    pattern_type character varying(16) DEFAULT 'LIKE'::character varying NOT NULL,
    allow_primary boolean DEFAULT false NOT NULL,
    allow_secondary boolean DEFAULT true NOT NULL,
    reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.dx_primary_policy OWNER TO sns;

--
-- Name: eligibility_assessments; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.eligibility_assessments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    ruleset_id text NOT NULL,
    ruleset_version text NOT NULL,
    eligible boolean NOT NULL,
    score integer DEFAULT 0,
    observations_snapshot jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE public.eligibility_assessments OWNER TO sns;

--
-- Name: eligibility_decisions; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.eligibility_decisions (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    decision character varying(50) NOT NULL,
    lcd_id character varying(20) NOT NULL,
    mac character varying(20) NOT NULL,
    mac_type character varying(10) NOT NULL,
    lcd_effective_date date NOT NULL,
    decision_timestamp timestamp with time zone NOT NULL,
    config_hash character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE public.eligibility_decisions OWNER TO sns;

--
-- Name: eligibility_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: sns
--

CREATE SEQUENCE public.eligibility_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.eligibility_decisions_id_seq OWNER TO sns;

--
-- Name: eligibility_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sns
--

ALTER SEQUENCE public.eligibility_decisions_id_seq OWNED BY public.eligibility_decisions.id;


--
-- Name: eligibility_rulesets; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.eligibility_rulesets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    ruleset_id text NOT NULL,
    ruleset_version text NOT NULL,
    condition text NOT NULL,
    jurisdiction text DEFAULT 'ANY'::text NOT NULL,
    ruleset_json jsonb NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE public.eligibility_rulesets OWNER TO sns;

--
-- Name: external_substances; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.external_substances (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid,
    substance_name character varying,
    category character varying,
    notes text,
    recorded_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    name character varying,
    substance_type character varying,
    initiated_by uuid,
    ordered_by_provider uuid,
    purpose text,
    known_interactions text,
    clinician_reviewed boolean,
    clinician_action character varying,
    clinician_notes text,
    coverage_intent character varying,
    financial_responsibility character varying,
    reviewed_at timestamp without time zone,
    reviewed_by uuid,
    updated_at timestamp without time zone
);


ALTER TABLE public.external_substances OWNER TO sns;

--
-- Name: f2f_encounters; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.f2f_encounters (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    benefit_period_id uuid NOT NULL,
    encounter_date date NOT NULL,
    performed_by_role character varying NOT NULL,
    performed_by_user_id uuid,
    summary text,
    status character varying DEFAULT 'DRAFT'::character varying NOT NULL,
    finalized_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    pps_score_previous integer,
    pps_score_current integer,
    weight_loss_lbs numeric,
    adl_dependency_level text,
    is_bedbound boolean,
    oral_intake_decline boolean,
    dysphagia boolean,
    hospitalizations_30d integer,
    oxygen_lpm_previous numeric,
    oxygen_lpm_current numeric,
    primary_diagnosis text,
    secondary_conditions text,
    clinical_decline_summary text,
    kps_score integer,
    fast_score text,
    nyha_class text,
    adl_dependency_count integer,
    attested_at timestamp without time zone,
    attesting_provider_user_id uuid
);


ALTER TABLE public.f2f_encounters OWNER TO sns;

--
-- Name: form_modules; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.form_modules (
    id uuid NOT NULL,
    name character varying(128) NOT NULL,
    module_key character varying(128) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone
);


ALTER TABLE public.form_modules OWNER TO sns;

--
-- Name: form_package_modules; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.form_package_modules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    form_registry_id uuid NOT NULL,
    module_id uuid NOT NULL,
    display_order integer,
    is_required boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone
);


ALTER TABLE public.form_package_modules OWNER TO sns;

--
-- Name: form_registry; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.form_registry (
    id uuid NOT NULL,
    form_type character varying(64) NOT NULL,
    form_family character varying(64) NOT NULL,
    discipline character varying(32) NOT NULL,
    level_of_care character varying(32),
    form_key character varying(128) NOT NULL,
    is_primary boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone,
    attached_forms json,
    version integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.form_registry OWNER TO sns;

--
-- Name: forms; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.forms (
    id uuid NOT NULL,
    visit_id uuid NOT NULL,
    form_registry_id uuid NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    content jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    form_key character varying(128),
    form_family character varying(64),
    form_type character varying(64),
    status character varying(32) DEFAULT 'DRAFT'::character varying NOT NULL,
    finalized_at timestamp with time zone,
    finalized_by character varying(64),
    tenant_id character varying(64)
);


ALTER TABLE public.forms OWNER TO sns;

--
-- Name: gip_periods; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.gip_periods (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    reason character varying,
    tenant_id uuid,
    visit_id uuid,
    service_level character varying(50) DEFAULT 'GIP'::character varying,
    status character varying(32) DEFAULT 'ACTIVE'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.gip_periods OWNER TO sns;

--
-- Name: guardrail_policies; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.guardrail_policies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    policy_key character varying(128) NOT NULL,
    value text NOT NULL,
    description text,
    value_type character varying(16) DEFAULT 'STRING'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    effective_date timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    updated_by uuid,
    CONSTRAINT ck_guardrail_policies_ck_guardrail_policies_value_type CHECK (((value_type)::text = ANY ((ARRAY['STRING'::character varying, 'INTEGER'::character varying, 'BOOLEAN'::character varying, 'JSON'::character varying])::text[])))
);


ALTER TABLE public.guardrail_policies OWNER TO sns;

--
-- Name: hope_records; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.hope_records (
    id uuid NOT NULL,
    patient_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    previous_hope_record_id uuid
);


ALTER TABLE public.hope_records OWNER TO sns;

--
-- Name: hope_symptom_assessments; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.hope_symptom_assessments (
    id uuid NOT NULL,
    hope_record_id uuid NOT NULL,
    symptom_code text NOT NULL,
    severity integer,
    assessed_at timestamp with time zone NOT NULL,
    assessed_by_user_id uuid NOT NULL
);


ALTER TABLE public.hope_symptom_assessments OWNER TO sns;

--
-- Name: hope_symptom_followups; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.hope_symptom_followups (
    id uuid NOT NULL,
    hope_record_id uuid NOT NULL,
    symptom_code text NOT NULL,
    followup_required boolean NOT NULL,
    followup_completed boolean NOT NULL,
    determined_at timestamp with time zone NOT NULL
);


ALTER TABLE public.hope_symptom_followups OWNER TO sns;

--
-- Name: hope_symptom_visits; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.hope_symptom_visits (
    id uuid NOT NULL,
    hope_symptom_followup_id uuid,
    visit_id uuid,
    completed_by_user_id uuid NOT NULL,
    completed_at timestamp with time zone NOT NULL
);


ALTER TABLE public.hope_symptom_visits OWNER TO sns;

--
-- Name: idg_attendance; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_attendance (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    idg_session_id uuid NOT NULL,
    user_id uuid,
    participant_name character varying(255),
    discipline character varying(64) NOT NULL,
    attendance_mode text DEFAULT 'IN_PERSON'::text NOT NULL,
    attended boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_idg_attendance_ck_idg_attendance_mode CHECK ((attendance_mode = ANY (ARRAY['IN_PERSON'::text, 'REMOTE'::text, 'PHONE'::text, 'MANUAL'::text])))
);


ALTER TABLE public.idg_attendance OWNER TO sns;

--
-- Name: idg_justification_notes; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_justification_notes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    eligibility_assessment_id uuid NOT NULL,
    text text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.idg_justification_notes OWNER TO sns;

--
-- Name: idg_md_attestations; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_md_attestations (
    attestation_id uuid NOT NULL,
    idg_id uuid NOT NULL,
    md_user_id uuid NOT NULL,
    attestation_text text NOT NULL,
    signed_at timestamp with time zone NOT NULL,
    idg_review_id uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    id uuid,
    CONSTRAINT ck_md_attestations_idg_link_consistent CHECK (((idg_review_id IS NULL) OR (idg_id IS NULL) OR (idg_review_id = idg_id)))
);


ALTER TABLE public.idg_md_attestations OWNER TO sns;

--
-- Name: idg_meetings; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_meetings (
    idg_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    benefit_period_id uuid,
    meeting_date date NOT NULL,
    status public.idg_status_enum DEFAULT 'SCHEDULED'::public.idg_status_enum NOT NULL,
    finalized_at timestamp without time zone,
    rn_required boolean DEFAULT true NOT NULL,
    physician_required boolean DEFAULT true NOT NULL,
    social_worker_required boolean DEFAULT false NOT NULL,
    chaplain_required boolean DEFAULT false NOT NULL,
    rn_present boolean DEFAULT false NOT NULL,
    physician_present boolean DEFAULT false NOT NULL,
    social_worker_present boolean DEFAULT false NOT NULL,
    chaplain_present boolean DEFAULT false NOT NULL,
    summary text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    id uuid
);


ALTER TABLE public.idg_meetings OWNER TO sns;

--
-- Name: idg_notes; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_notes (
    idg_note_id uuid NOT NULL,
    idg_id uuid NOT NULL,
    discipline character varying(50) NOT NULL,
    author_user_id uuid NOT NULL,
    summary text NOT NULL,
    recommendations text,
    change_in_condition boolean NOT NULL,
    poc_change_recommended boolean NOT NULL,
    signed_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    idg_review_id uuid,
    id uuid,
    note_text text
);


ALTER TABLE public.idg_notes OWNER TO sns;

--
-- Name: idg_participants; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_participants (
    participant_id uuid NOT NULL,
    idg_id uuid NOT NULL,
    discipline character varying(50) NOT NULL,
    user_id uuid,
    participation_status public.idg_participation_status_enum NOT NULL,
    reason_if_excused text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.idg_participants OWNER TO sns;

--
-- Name: idg_reviews; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_reviews (
    patient_id uuid NOT NULL,
    review_date date NOT NULL,
    rn_present boolean,
    physician_present boolean,
    social_worker_present boolean,
    chaplain_present boolean,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    finalized_at timestamp with time zone,
    benefit_period_id uuid,
    summary text,
    poc_action text,
    idg_meeting_id uuid,
    tenant_id uuid,
    is_finalized boolean,
    finalized_by uuid
);


ALTER TABLE public.idg_reviews OWNER TO sns;

--
-- Name: idg_session; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_session (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    plan_of_care_id uuid NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    facilitator_user_id uuid,
    idg_status text DEFAULT 'NOT_YET_REVIEWED'::text NOT NULL,
    ai_assist_status text DEFAULT 'NOT_USED'::text NOT NULL,
    summary_note text,
    review_prompt_shown boolean DEFAULT false NOT NULL,
    ready_for_review boolean DEFAULT false NOT NULL,
    reviewed_by_user_id uuid,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_idg_session_ck_idg_session_ai_assist_status CHECK ((ai_assist_status = ANY (ARRAY['NOT_USED'::text, 'TRANSCRIPT_GENERATED'::text, 'SUMMARY_DRAFTED'::text, 'REVIEW_PENDING'::text, 'FINALIZED'::text]))),
    CONSTRAINT ck_idg_session_ck_idg_session_status CHECK ((idg_status = ANY (ARRAY['NOT_YET_REVIEWED'::text, 'IN_PROGRESS'::text, 'REVIEWED'::text])))
);


ALTER TABLE public.idg_session OWNER TO sns;

--
-- Name: idg_signatures; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.idg_signatures (
    id uuid NOT NULL,
    idg_review_id uuid NOT NULL,
    discipline public.idg_discipline NOT NULL,
    user_id uuid,
    signed_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    idg_meeting_id uuid,
    idg_session_id uuid,
    signature_role text DEFAULT 'ATTENDANCE_ACK'::text NOT NULL,
    CONSTRAINT ck_idg_signatures_ck_idg_signatures_role CHECK ((signature_role = ANY (ARRAY['ATTENDANCE_ACK'::text, 'FINAL_NOTE_CONFIRM'::text, 'SESSION_FINALIZER'::text])))
);


ALTER TABLE public.idg_signatures OWNER TO sns;

--
-- Name: incident_reports; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.incident_reports (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    clinical_note_id uuid,
    incident_type character varying(32) NOT NULL,
    incident_severity character varying(16) DEFAULT 'STANDARD'::character varying NOT NULL,
    incident_date date NOT NULL,
    reported_date date,
    incident_time time without time zone,
    reported_by character varying(32),
    witnessed_by character varying(32),
    place character varying(16),
    area character varying(32),
    surface character varying(32),
    medication_used character varying(32),
    activity_at_time character varying(64),
    injury_level character varying(32),
    injury_type character varying(32),
    other_injury_text text,
    narrative text,
    entered_by uuid,
    signed_by uuid,
    signed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_incident_reports_ck_incident_reports_activity_at_time CHECK (((activity_at_time IS NULL) OR ((activity_at_time)::text = ANY (ARRAY[('REACHING_CHAIR_TO_BED'::character varying)::text, ('REACHING_BED_TO_CHAIR'::character varying)::text, ('AMBULATING'::character varying)::text, ('TOILETING'::character varying)::text, ('TRANSFERRING'::character varying)::text, ('SITTING'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_area CHECK (((area IS NULL) OR ((area)::text = ANY (ARRAY[('PT_ROOM_BEDROOM'::character varying)::text, ('HALLWAY'::character varying)::text, ('BATHROOM'::character varying)::text, ('STEPS'::character varying)::text, ('KITCHEN'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_incident_severity CHECK (((incident_severity)::text = ANY (ARRAY[('STANDARD'::character varying)::text, ('SIGNIFICANT'::character varying)::text, ('SENTINEL'::character varying)::text]))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_incident_type CHECK (((incident_type)::text = ANY (ARRAY[('FALL'::character varying)::text, ('ADVERSE_REACTION'::character varying)::text, ('SENTINEL_EVENT'::character varying)::text, ('OTHER'::character varying)::text]))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_injury_level CHECK (((injury_level IS NULL) OR ((injury_level)::text = ANY (ARRAY[('NO_INJURY'::character varying)::text, ('MINOR_INJURY'::character varying)::text, ('MODERATE_INJURY'::character varying)::text, ('HOSPITALIZATION_REQUIRED'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_injury_type CHECK (((injury_type IS NULL) OR ((injury_type)::text = ANY (ARRAY[('NONE'::character varying)::text, ('SKIN_TEAR'::character varying)::text, ('LACERATION'::character varying)::text, ('BRUISE'::character varying)::text, ('FRACTURE'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_medication_used CHECK (((medication_used IS NULL) OR ((medication_used)::text = ANY (ARRAY[('NONE'::character varying)::text, ('ANALGESIC'::character varying)::text, ('SEDATIVE'::character varying)::text, ('OPIATE'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_place CHECK (((place IS NULL) OR ((place)::text = ANY (ARRAY[('POS'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_reported_by CHECK (((reported_by IS NULL) OR ((reported_by)::text = ANY (ARRAY[('PATIENT'::character varying)::text, ('PCG'::character varying)::text, ('SPOUSE_PARTNER'::character varying)::text, ('CHILD'::character varying)::text, ('RELATIVE'::character varying)::text, ('FRIEND'::character varying)::text, ('FACILITY_STAFF'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_signed_requires_fields CHECK (((signed_by IS NULL) OR (signed_at IS NOT NULL))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_surface CHECK (((surface IS NULL) OR ((surface)::text = ANY (ARRAY[('CARPET'::character varying)::text, ('RUNNER'::character varying)::text, ('THROW_AWAY_RUG'::character varying)::text, ('SLAB'::character varying)::text, ('WOOD'::character varying)::text, ('OTHER'::character varying)::text])))),
    CONSTRAINT ck_incident_reports_ck_incident_reports_witnessed_by CHECK (((witnessed_by IS NULL) OR ((witnessed_by)::text = ANY (ARRAY[('NOT_WITNESSED'::character varying)::text, ('STAFF'::character varying)::text, ('PCG'::character varying)::text, ('SPOUSE_PARTNER'::character varying)::text, ('CHILD'::character varying)::text, ('RELATIVE'::character varying)::text, ('FRIEND'::character varying)::text, ('FACILITY_STAFF'::character varying)::text, ('OTHER'::character varying)::text]))))
);


ALTER TABLE public.incident_reports OWNER TO sns;

--
-- Name: infection_control_summary_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.infection_control_summary_view AS
 SELECT d.patient_id,
    d.diagnosis_name,
    d.infection_source,
    count(o.id) AS total_orders,
    count(*) FILTER (WHERE (o.medication_class = 'ANTIBIOTIC'::text)) AS antibiotic_orders,
    count(*) FILTER (WHERE (o.status = 'ACTIVE'::text)) AS active_orders,
    count(*) FILTER (WHERE (o.status = 'DISCONTINUED'::text)) AS discontinued_orders,
    min(o.ordered_at) AS first_order,
    max(o.ordered_at) AS last_order
   FROM (public.diagnoses d
     LEFT JOIN public.orders o ON ((o.diagnosis_id = d.id)))
  GROUP BY d.patient_id, d.diagnosis_name, d.infection_source;


ALTER VIEW public.infection_control_summary_view OWNER TO postgres;

--
-- Name: interfaces; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.interfaces (
    id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE public.interfaces OWNER TO sns;

--
-- Name: med_reconciliation_audit_logs; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.med_reconciliation_audit_logs (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    import_id uuid,
    item_id uuid,
    stage character varying(50) NOT NULL,
    event_type character varying(100) NOT NULL,
    med_name_raw character varying(255),
    input_payload jsonb,
    normalized_payload jsonb,
    comparison_payload jsonb,
    decision_payload jsonb,
    created_by uuid,
    created_at timestamp with time zone NOT NULL,
    hash_version character varying(20) NOT NULL,
    prev_signature_hash character varying(64),
    signature_hash character varying(64)
);


ALTER TABLE public.med_reconciliation_audit_logs OWNER TO sns;

--
-- Name: med_reconciliation_imports; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.med_reconciliation_imports (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    source_type character varying(32) NOT NULL,
    source_context character varying(32) NOT NULL,
    status character varying(32) DEFAULT 'PENDING_REVIEW'::character varying NOT NULL,
    source_file_name character varying(255),
    uploaded_by uuid,
    uploaded_at timestamp with time zone NOT NULL,
    parsed_at timestamp with time zone,
    reviewed_at timestamp with time zone,
    reviewed_by uuid,
    raw_summary text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by uuid,
    CONSTRAINT ck_med_reconciliation_imports_ck_med_reconciliation_imp_14f3 CHECK (((source_type)::text = ANY ((ARRAY['PDF'::character varying, 'CCD'::character varying, 'C-CDA'::character varying, 'SCANNED_DOC'::character varying, 'MANUAL'::character varying])::text[]))),
    CONSTRAINT ck_med_reconciliation_imports_ck_med_reconciliation_imp_3d82 CHECK (((source_context)::text = ANY ((ARRAY['HOSPITAL_DISCHARGE'::character varying, 'ED_VISIT'::character varying, 'INPATIENT_STAY'::character varying, 'OTHER'::character varying])::text[]))),
    CONSTRAINT ck_med_reconciliation_imports_ck_med_reconciliation_imp_dbe6 CHECK (((status)::text = ANY ((ARRAY['PENDING_REVIEW'::character varying, 'PARTIALLY_REVIEWED'::character varying, 'FINALIZED'::character varying])::text[])))
);


ALTER TABLE public.med_reconciliation_imports OWNER TO sns;

--
-- Name: med_reconciliation_items; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.med_reconciliation_items (
    id uuid NOT NULL,
    import_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    list_type character varying(32) NOT NULL,
    med_name_raw character varying(255) NOT NULL,
    med_name_normalized character varying(255),
    dose character varying(128),
    route character varying(64),
    frequency character varying(128),
    indication character varying(255),
    reaction_description text,
    severity character varying(16),
    reaction_category_suggested character varying(32),
    reaction_category_final character varying(32),
    is_discharge_candidate boolean DEFAULT false NOT NULL,
    requires_immediate_review boolean DEFAULT false NOT NULL,
    is_critical_reaction boolean DEFAULT false NOT NULL,
    review_status character varying(32) DEFAULT 'PENDING'::character varying NOT NULL,
    notes text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    dose_normalized character varying(128),
    route_normalized character varying(64),
    frequency_normalized character varying(128),
    comparison_status character varying(32),
    comparison_flags jsonb,
    matched_medication_id uuid,
    comparison_review_reason text,
    created_by uuid,
    signature_hash character varying(64),
    CONSTRAINT ck_med_reconciliation_items_ck_med_reconciliation_items_247d CHECK (((review_status)::text = ANY ((ARRAY['PENDING'::character varying, 'REVIEWED'::character varying, 'ACCEPTED'::character varying, 'REJECTED'::character varying])::text[]))),
    CONSTRAINT ck_med_reconciliation_items_ck_med_reconciliation_items_4852 CHECK (((list_type)::text = ANY ((ARRAY['INPATIENT_HISTORY'::character varying, 'DISCHARGE_LIST'::character varying])::text[]))),
    CONSTRAINT ck_med_reconciliation_items_ck_med_reconciliation_items_80fa CHECK (((reaction_category_final IS NULL) OR ((reaction_category_final)::text = ANY ((ARRAY['ALLERGY'::character varying, 'SIDE_EFFECT'::character varying, 'INTOLERANCE'::character varying])::text[])))),
    CONSTRAINT ck_med_reconciliation_items_ck_med_reconciliation_items_b94f CHECK (((reaction_category_suggested IS NULL) OR ((reaction_category_suggested)::text = ANY ((ARRAY['POSSIBLE_ALLERGY'::character varying, 'POSSIBLE_SIDE_EFFECT'::character varying, 'POSSIBLE_INTOLERANCE'::character varying, 'UNKNOWN'::character varying])::text[])))),
    CONSTRAINT ck_med_reconciliation_items_ck_med_reconciliation_items_f243 CHECK (((severity IS NULL) OR ((severity)::text = ANY ((ARRAY['MILD'::character varying, 'MODERATE'::character varying, 'SEVERE'::character varying])::text[]))))
);


ALTER TABLE public.med_reconciliation_items OWNER TO sns;

--
-- Name: medications; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.medications (
    patient_id uuid NOT NULL,
    medication_name character varying NOT NULL,
    dosage character varying NOT NULL,
    route character varying NOT NULL,
    frequency character varying NOT NULL,
    start_date date NOT NULL,
    end_date date,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    canonical_name character varying(255),
    tenant_id uuid NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    is_prn boolean DEFAULT false NOT NULL,
    discontinued_at date
);


ALTER TABLE public.medications OWNER TO sns;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid,
    user_id uuid,
    notification_type character varying,
    status character varying,
    payload jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone,
    created_by uuid,
    source_type character varying,
    source_id uuid,
    message text,
    seen_at timestamp without time zone,
    title text,
    is_read boolean DEFAULT false,
    read_at timestamp with time zone
);


ALTER TABLE public.notifications OWNER TO sns;

--
-- Name: orders_audit_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.orders_audit_view AS
 SELECT o.id,
    o.visit_id,
    o.order_category,
    o.order_name,
    o.medication_class,
    o.indication,
    o.status,
    o.ordered_at,
    o.ordered_by,
    o.signed_at,
    o.signed_by,
    o.discontinued_at,
    o.discontinued_by,
    o.discontinued_reason,
    (o.signed_at - o.ordered_at) AS time_to_sign,
    (o.discontinued_at - o.ordered_at) AS time_to_discontinue,
        CASE
            WHEN (o.status = 'ACTIVE'::text) THEN true
            ELSE false
        END AS is_active,
        CASE
            WHEN (o.status = 'DISCONTINUED'::text) THEN true
            ELSE false
        END AS is_discontinued,
        CASE
            WHEN (o.signed_at IS NOT NULL) THEN true
            ELSE false
        END AS is_signed,
    d.diagnosis_name,
    d.infection_source
   FROM (public.orders o
     LEFT JOIN public.diagnoses d ON ((o.diagnosis_id = d.id)));


ALTER VIEW public.orders_audit_view OWNER TO postgres;

--
-- Name: orders_compliance_flags_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.orders_compliance_flags_view AS
 SELECT id,
    order_name,
    status,
    ordered_at,
    signed_at,
        CASE
            WHEN (signed_at IS NULL) THEN 'MISSING_SIGNATURE'::text
            WHEN (signed_at < ordered_at) THEN 'INVALID_TIMING'::text
            ELSE 'OK'::text
        END AS signature_issue,
        CASE
            WHEN ((status = 'DISCONTINUED'::text) AND (discontinued_reason IS NULL)) THEN 'MISSING_REASON'::text
            ELSE 'OK'::text
        END AS discontinuation_issue
   FROM public.orders;


ALTER VIEW public.orders_compliance_flags_view OWNER TO postgres;

--
-- Name: orders_snapshot; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.orders_snapshot (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    discipline character varying NOT NULL,
    visits_per_week integer NOT NULL,
    effective_date date NOT NULL,
    end_date date
);


ALTER TABLE public.orders_snapshot OWNER TO sns;

--
-- Name: orders_snapshots; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.orders_snapshots (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    discipline character varying(32) NOT NULL,
    visits_per_week integer NOT NULL,
    status character varying(32) DEFAULT 'ACTIVE'::character varying NOT NULL,
    effective_date date NOT NULL,
    end_date date,
    snapshot_type character varying(50) DEFAULT 'ORDERS'::character varying NOT NULL,
    version character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(255),
    CONSTRAINT ck_orders_snapshots_ck_orders_snapshot_dates CHECK (((end_date IS NULL) OR (end_date >= effective_date)))
);


ALTER TABLE public.orders_snapshots OWNER TO sns;

--
-- Name: patient_allergies; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.patient_allergies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    allergy_name text NOT NULL,
    reaction text,
    severity text,
    is_active boolean DEFAULT true NOT NULL,
    recorded_at timestamp without time zone DEFAULT now() NOT NULL,
    recorded_by_account_id uuid
);


ALTER TABLE public.patient_allergies OWNER TO sns;

--
-- Name: patient_allergy_profiles; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.patient_allergy_profiles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    is_nkda boolean DEFAULT false NOT NULL,
    last_updated_at timestamp without time zone DEFAULT now() NOT NULL,
    last_updated_by_account_id uuid
);


ALTER TABLE public.patient_allergy_profiles OWNER TO sns;

--
-- Name: patient_assignments; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.patient_assignments (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    discipline public.assignment_discipline_enum NOT NULL,
    user_id uuid NOT NULL,
    service_area character varying(64),
    status character varying(16) DEFAULT 'ASSIGNED'::character varying NOT NULL,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    assigned_by uuid,
    note text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by uuid,
    is_primary boolean NOT NULL,
    active boolean NOT NULL,
    deactivated_at timestamp with time zone
);


ALTER TABLE public.patient_assignments OWNER TO sns;

--
-- Name: patients; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.patients (
    mrn character varying NOT NULL,
    full_name character varying NOT NULL,
    date_of_birth date NOT NULL,
    primary_diagnosis character varying NOT NULL,
    status character varying DEFAULT 'ACTIVE'::character varying NOT NULL,
    discharge_date date,
    discharge_reason character varying,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    acuity_state character varying DEFAULT 'ROUTINE'::character varying NOT NULL,
    crisis_started_at timestamp without time zone,
    crisis_ended_at timestamp without time zone,
    hospice_election_date date,
    current_discharge_id uuid,
    tenant_id uuid NOT NULL,
    records_release_signed_at timestamp with time zone,
    election_signed_at timestamp with time zone,
    soc_date timestamp with time zone,
    admission_status character varying(32) NOT NULL,
    admission_authorized_at timestamp with time zone,
    admission_authorized_by uuid,
    not_admitted_at timestamp with time zone,
    not_admitted_reason text,
    ssn_last4 character varying(4),
    on_service_at timestamp with time zone,
    has_wounds boolean DEFAULT false,
    has_chha boolean DEFAULT false,
    has_lvn boolean DEFAULT false,
    deleted_at timestamp with time zone,
    CONSTRAINT ck_patients_ck_patients_admission_status CHECK (((admission_status)::text = ANY (ARRAY[('PRE_REFERRAL'::character varying)::text, ('RECORDS_PENDING'::character varying)::text, ('MD_REVIEW_PENDING'::character varying)::text, ('AUTHORIZED_TO_ADMIT'::character varying)::text, ('ADMITTED'::character varying)::text, ('NOT_ADMITTED'::character varying)::text]))),
    CONSTRAINT patients_status_check CHECK (((status)::text = ANY (ARRAY[('ACTIVE'::character varying)::text, ('DISCHARGED'::character varying)::text, ('DECEASED'::character varying)::text])))
);


ALTER TABLE public.patients OWNER TO sns;

--
-- Name: patient_face_sheet_view; Type: VIEW; Schema: public; Owner: sns
--

CREATE VIEW public.patient_face_sheet_view AS
 WITH rn_primary AS (
         SELECT diagnosis_sources.patient_id,
            diagnosis_sources.icd_code,
            diagnosis_sources.description
           FROM public.diagnosis_sources
          WHERE ((diagnosis_sources.source = 'RN_IA'::text) AND (diagnosis_sources.dx_type = 'PRIMARY'::text) AND (diagnosis_sources.is_active = true))
        ), cti_primary AS (
         SELECT diagnosis_sources.patient_id,
            diagnosis_sources.icd_code,
            diagnosis_sources.description
           FROM public.diagnosis_sources
          WHERE ((diagnosis_sources.source = 'CTI'::text) AND (diagnosis_sources.dx_type = 'PRIMARY'::text) AND (diagnosis_sources.is_active = true))
        )
 SELECT p.id AS patient_id,
    p.status AS patient_status,
    COALESCE(rn_primary.icd_code, cti_primary.icd_code) AS primary_dx_icd,
        CASE
            WHEN ((rn_primary.icd_code IS NOT NULL) AND (cti_primary.icd_code IS NOT NULL) AND (rn_primary.icd_code <> cti_primary.icd_code)) THEN true
            ELSE false
        END AS dx_discrepancy_open,
        CASE
            WHEN ((rn_primary.icd_code IS NOT NULL) AND (cti_primary.icd_code IS NOT NULL) AND (rn_primary.icd_code <> cti_primary.icd_code)) THEN 'OPEN'::text
            ELSE 'NONE'::text
        END AS dx_discrepancy_status,
        CASE
            WHEN (ap.is_nkda = true) THEN 'NKDA'::text
            WHEN (pa.patient_id IS NOT NULL) THEN 'HAS_ALLERGY'::text
            ELSE 'NOT_DOCUMENTED'::text
        END AS allergy_state
   FROM ((((public.patients p
     LEFT JOIN rn_primary ON ((rn_primary.patient_id = p.id)))
     LEFT JOIN cti_primary ON ((cti_primary.patient_id = p.id)))
     LEFT JOIN public.patient_allergy_profiles ap ON ((ap.patient_id = p.id)))
     LEFT JOIN public.patient_allergies pa ON ((pa.patient_id = p.id)));


ALTER VIEW public.patient_face_sheet_view OWNER TO sns;

--
-- Name: patient_insurances; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.patient_insurances (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    payer_type character varying(32) NOT NULL,
    payer_name character varying(255) NOT NULL,
    subscriber_id character varying(128) NOT NULL,
    subscriber_id_type character varying(32),
    group_number character varying(128),
    coverage_scope character varying(32) NOT NULL,
    priority_order integer NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    effective_date date,
    end_date date,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    verified_at timestamp with time zone,
    verified_by uuid,
    created_by uuid
);


ALTER TABLE public.patient_insurances OWNER TO sns;

--
-- Name: patient_payers; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.patient_payers (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    payer_name character varying NOT NULL,
    payer_type character varying NOT NULL,
    subscriber_id character varying,
    subscriber_id_type character varying,
    facility_name character varying,
    effective_start_date date,
    end_date date,
    is_primary boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by uuid
);


ALTER TABLE public.patient_payers OWNER TO sns;

--
-- Name: patient_pos; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.patient_pos (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    pos_type character varying NOT NULL,
    facility_name character varying,
    effective_date date NOT NULL,
    end_date date,
    tenant_id uuid,
    status character varying(32) DEFAULT 'ACTIVE'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    created_by character varying(255)
);


ALTER TABLE public.patient_pos OWNER TO sns;

--
-- Name: patients_snapshot_angela; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patients_snapshot_angela (
    mrn character varying,
    full_name character varying,
    date_of_birth date,
    primary_diagnosis character varying,
    status character varying,
    discharge_date date,
    discharge_reason character varying,
    id uuid,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    created_by uuid,
    acuity_state character varying,
    crisis_started_at timestamp without time zone,
    crisis_ended_at timestamp without time zone,
    hospice_election_date date,
    current_discharge_id uuid,
    tenant_id uuid,
    records_release_signed_at timestamp with time zone,
    election_signed_at timestamp with time zone,
    soc_date timestamp with time zone,
    admission_status character varying(32),
    admission_authorized_at timestamp with time zone,
    admission_authorized_by uuid,
    not_admitted_at timestamp with time zone,
    not_admitted_reason text,
    ssn_last4 character varying(4),
    on_service_at timestamp with time zone,
    has_wounds boolean,
    has_chha boolean,
    has_lvn boolean,
    deleted_at timestamp with time zone
);


ALTER TABLE public.patients_snapshot_angela OWNER TO postgres;

--
-- Name: payer_contracts; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.payer_contracts (
    id character varying NOT NULL,
    tenant_id character varying NOT NULL,
    payer_name character varying NOT NULL,
    has_contract character varying,
    payer_id uuid,
    contract_number character varying(100),
    status character varying(32) DEFAULT 'ACTIVE'::character varying,
    start_date date,
    end_date date,
    created_at timestamp with time zone DEFAULT now(),
    created_by character varying(255)
);


ALTER TABLE public.payer_contracts OWNER TO sns;

--
-- Name: payers; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.payers (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(50),
    payer_type character varying(50),
    status character varying(32) DEFAULT 'ACTIVE'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    created_by character varying(255)
);


ALTER TABLE public.payers OWNER TO sns;

--
-- Name: plan_of_care; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.plan_of_care (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    status character varying(32) DEFAULT 'DRAFT'::character varying NOT NULL,
    version_number integer DEFAULT 1 NOT NULL,
    effective_at timestamp with time zone,
    review_due_at timestamp with time zone,
    last_reviewed_at timestamp with time zone,
    rn_coordinator_user_id uuid,
    attending_physician_name character varying(255),
    medical_director_user_id uuid,
    approval_status character varying(32) DEFAULT 'PENDING'::character varying NOT NULL,
    approved_at timestamp with time zone,
    approved_by_user_id uuid,
    supersedes_plan_of_care_id uuid,
    current_version_id uuid,
    poc_content_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_plan_of_care_ck_plan_of_care_approval_pair CHECK ((((approved_at IS NULL) AND (approved_by_user_id IS NULL)) OR ((approved_at IS NOT NULL) AND (approved_by_user_id IS NOT NULL)))),
    CONSTRAINT ck_plan_of_care_ck_plan_of_care_approval_status CHECK (((approval_status)::text = ANY ((ARRAY['PENDING'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying])::text[]))),
    CONSTRAINT ck_plan_of_care_ck_plan_of_care_status CHECK (((status)::text = ANY ((ARRAY['DRAFT'::character varying, 'ACTIVE'::character varying, 'SUPERSEDED'::character varying, 'ARCHIVED'::character varying])::text[])))
);


ALTER TABLE public.plan_of_care OWNER TO sns;

--
-- Name: plan_of_care_approvals; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.plan_of_care_approvals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    plan_of_care_id uuid NOT NULL,
    version_id uuid NOT NULL,
    approver_role character varying(64) NOT NULL,
    approver_user_id uuid,
    decision character varying(32) DEFAULT 'PENDING'::character varying NOT NULL,
    decision_note text,
    decided_at timestamp with time zone,
    CONSTRAINT ck_plan_of_care_approvals_ck_plan_of_care_approvals_decision CHECK (((decision)::text = ANY ((ARRAY['PENDING'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying])::text[])))
);


ALTER TABLE public.plan_of_care_approvals OWNER TO sns;

--
-- Name: plan_of_care_goals; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.plan_of_care_goals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    plan_of_care_id uuid NOT NULL,
    problem_code character varying(128),
    problem_label character varying(255) NOT NULL,
    goal_text text NOT NULL,
    outcome_measure text,
    target_date date,
    status character varying(32) DEFAULT 'ACTIVE'::character varying NOT NULL,
    discipline_owner character varying(64),
    progress_summary text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_plan_of_care_goals_ck_plan_of_care_goals_status CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'MET'::character varying, 'NOT_MET'::character varying, 'DISCONTINUED'::character varying])::text[])))
);


ALTER TABLE public.plan_of_care_goals OWNER TO sns;

--
-- Name: plan_of_care_versions; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.plan_of_care_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    plan_of_care_id uuid NOT NULL,
    version_number integer NOT NULL,
    snapshot_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    change_reason text,
    trigger_source character varying(64),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    approved_at timestamp with time zone,
    approved_by_user_id uuid,
    based_on_version_id uuid
);


ALTER TABLE public.plan_of_care_versions OWNER TO sns;

--
-- Name: poc_problem_templates; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.poc_problem_templates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    condition text NOT NULL,
    problem_label text NOT NULL
);


ALTER TABLE public.poc_problem_templates OWNER TO sns;

--
-- Name: refusals; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.refusals (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    discipline text NOT NULL,
    reason text,
    refused_at timestamp with time zone NOT NULL,
    was_reoffered boolean DEFAULT false NOT NULL,
    reoffered_at timestamp with time zone,
    created_by uuid,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT refusals_discipline_check CHECK ((discipline = ANY (ARRAY['RN'::text, 'MD'::text, 'F2F'::text, 'SW'::text, 'CHAPLAIN'::text, 'AIDE'::text])))
);


ALTER TABLE public.refusals OWNER TO sns;

--
-- Name: regulatory_report_artifacts; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.regulatory_report_artifacts (
    id uuid NOT NULL,
    report_id uuid NOT NULL,
    artifact_type public.reg_artifact_type_enum NOT NULL,
    file_path text NOT NULL,
    checksum text NOT NULL,
    generated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.regulatory_report_artifacts OWNER TO sns;

--
-- Name: regulatory_report_metrics; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.regulatory_report_metrics (
    id uuid NOT NULL,
    report_id uuid NOT NULL,
    section_id uuid,
    metric_key text NOT NULL,
    metric_value_numeric numeric,
    metric_value_text text,
    breakdown_json json
);


ALTER TABLE public.regulatory_report_metrics OWNER TO sns;

--
-- Name: regulatory_report_sections; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.regulatory_report_sections (
    id uuid NOT NULL,
    report_id uuid NOT NULL,
    section_key text NOT NULL,
    section_title text NOT NULL,
    section_version integer DEFAULT 1 NOT NULL,
    generated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.regulatory_report_sections OWNER TO sns;

--
-- Name: regulatory_reports; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.regulatory_reports (
    id uuid NOT NULL,
    report_type public.reg_report_type_enum NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    status public.reg_report_status_enum NOT NULL,
    generated_at timestamp with time zone NOT NULL,
    generated_by uuid,
    certified_at timestamp with time zone,
    certified_by uuid,
    integrity_hash text,
    metadata json,
    CONSTRAINT chk_certified_requires_certified_at CHECK (((status <> ALL (ARRAY['CERTIFIED'::public.reg_report_status_enum, 'LOCKED'::public.reg_report_status_enum])) OR (certified_at IS NOT NULL))),
    CONSTRAINT chk_locked_requires_integrity_hash CHECK (((status <> 'LOCKED'::public.reg_report_status_enum) OR (integrity_hash IS NOT NULL)))
);


ALTER TABLE public.regulatory_reports OWNER TO sns;

--
-- Name: respite_periods; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.respite_periods (
    id character varying NOT NULL,
    patient_id character varying NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    reason character varying,
    tenant_id uuid,
    visit_id uuid,
    service_level character varying(50) DEFAULT 'RESPITE'::character varying,
    status character varying(32) DEFAULT 'ACTIVE'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.respite_periods OWNER TO sns;

--
-- Name: rn_recert_assessments; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.rn_recert_assessments (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    benefit_period_id uuid NOT NULL,
    created_by_user_id uuid NOT NULL,
    form_type character varying(50) DEFAULT 'RECERT'::character varying NOT NULL,
    form_family character varying(50) DEFAULT 'CLINICAL'::character varying NOT NULL,
    discipline character varying(50) DEFAULT 'RN'::character varying NOT NULL,
    status character varying(20) DEFAULT 'DRAFT'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    finalized_at timestamp with time zone,
    pps_score integer,
    kps_score integer,
    fast_stage character varying(50),
    nyha_class character varying(50),
    adl_level character varying(50),
    adl_dependency_count integer,
    primary_diagnosis text,
    eligibility_recommendation character varying(20) DEFAULT 'UNDECIDED'::character varying NOT NULL,
    raw_observations_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    clarification_items_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    normalized_observations_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    translation_output_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    translation_source_map_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    interpretation_output_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    translation_mode_used character varying(20) DEFAULT 'DETERMINISTIC'::character varying NOT NULL,
    translation_reviewed_by uuid,
    translation_reviewed_at timestamp with time zone,
    translation_accepted boolean DEFAULT false NOT NULL,
    attested_at timestamp with time zone,
    attesting_provider_user_id uuid
);


ALTER TABLE public.rn_recert_assessments OWNER TO sns;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.roles (
    id uuid NOT NULL,
    interface_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE public.roles OWNER TO sns;

--
-- Name: runbooks; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.runbooks (
    id uuid NOT NULL,
    tenant_id character varying NOT NULL,
    baseline_tag character varying NOT NULL,
    generated_at timestamp without time zone NOT NULL,
    policy_snapshot jsonb NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.runbooks OWNER TO sns;

--
-- Name: safety_assessments; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.safety_assessments (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    data_json jsonb,
    completed_at timestamp with time zone,
    signed_at timestamp with time zone,
    signed_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    care_setting public.care_setting_enum NOT NULL,
    safety_responsibility public.safety_responsibility_enum NOT NULL
);


ALTER TABLE public.safety_assessments OWNER TO sns;

--
-- Name: security_activity_events; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.security_activity_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid,
    role text,
    event_type text NOT NULL,
    scope text,
    patient_count integer DEFAULT 0 NOT NULL,
    document_count integer DEFAULT 0 NOT NULL,
    result text NOT NULL,
    reason text,
    metadata jsonb
);


ALTER TABLE public.security_activity_events OWNER TO sns;

--
-- Name: service_coverage_decisions; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.service_coverage_decisions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid,
    payer_id uuid,
    service_type character varying,
    decision character varying,
    effective_start_date date,
    effective_end_date date,
    rationale text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by uuid,
    service_id uuid,
    coverage_intent character varying,
    financial_responsibility character varying,
    decision_source character varying,
    decision_reason text,
    evidence_reference_type character varying,
    evidence_reference_id uuid,
    selected_payer_id uuid,
    decided_at timestamp without time zone,
    decided_by uuid,
    updated_at timestamp without time zone
);


ALTER TABLE public.service_coverage_decisions OWNER TO sns;

--
-- Name: sfv_requirements; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.sfv_requirements (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    trigger_source_type character varying(32) NOT NULL,
    trigger_reference_id uuid NOT NULL,
    trigger_symptom_group character varying(16) NOT NULL,
    trigger_datetime timestamp with time zone NOT NULL,
    due_at timestamp with time zone NOT NULL,
    task_id uuid,
    completed_visit_id uuid,
    completed_at timestamp with time zone,
    status character varying(16) DEFAULT 'OPEN'::character varying NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    CONSTRAINT ck_sfv_requirements_ck_sfv_requirements_status CHECK (((status)::text = ANY ((ARRAY['OPEN'::character varying, 'COMPLETED'::character varying, 'OVERDUE'::character varying, 'CANCELLED'::character varying])::text[]))),
    CONSTRAINT ck_sfv_requirements_ck_sfv_requirements_trigger_source_type CHECK (((trigger_source_type)::text = ANY ((ARRAY['INITIAL_RN_ICA'::character varying, 'HUV1'::character varying, 'HUV2'::character varying])::text[]))),
    CONSTRAINT ck_sfv_requirements_ck_sfv_requirements_trigger_symptom_group CHECK (((trigger_symptom_group)::text = ANY ((ARRAY['PAIN'::character varying, 'NON_PAIN'::character varying, 'BOTH'::character varying])::text[])))
);


ALTER TABLE public.sfv_requirements OWNER TO sns;

--
-- Name: survey_access; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.survey_access (
    patient_id uuid NOT NULL,
    issued_by uuid,
    token_jti character varying NOT NULL,
    issued_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL,
    used boolean,
    revoked boolean,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    tenant_id uuid NOT NULL
);


ALTER TABLE public.survey_access OWNER TO sns;

--
-- Name: tasks; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.tasks (
    id uuid NOT NULL,
    patient_id uuid NOT NULL,
    benefit_period_id uuid,
    origin public.tasks_origin_enum NOT NULL,
    discipline public.tasks_discipline_enum NOT NULL,
    assigned_user_id uuid,
    regulatory_basis public.tasks_regulatory_basis_enum NOT NULL,
    due_date date NOT NULL,
    status public.tasks_status_enum DEFAULT 'PENDING'::public.tasks_status_enum NOT NULL,
    completed_at timestamp without time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    excused_reason_code character varying(64),
    excused_at timestamp with time zone,
    excused_source character varying(32),
    completion_reference_type public.tasks_completion_ref_enum_v2,
    completion_reference_id uuid,
    tenant_id uuid NOT NULL,
    alert_reason text,
    scheduled_start_at timestamp with time zone,
    schedule_status character varying(32),
    due_at timestamp with time zone,
    clinical_note_id uuid,
    incident_id uuid,
    requires_countersignature boolean DEFAULT false,
    countersigned_by uuid,
    countersigned_at timestamp without time zone,
    sla_start_at timestamp with time zone,
    sla_due_at timestamp with time zone NOT NULL,
    escalation_level integer DEFAULT 0,
    escalated_at timestamp with time zone,
    escalation_reason text,
    is_overdue boolean DEFAULT false,
    priority text,
    clinical_severity text,
    assigned_role text,
    notification_required boolean DEFAULT false,
    reference_type text,
    reference_id uuid,
    task_type public.tasks_task_type_enum NOT NULL,
    CONSTRAINT ck_tasks_completed_requires_completion_reference CHECK (((status <> 'COMPLETED'::public.tasks_status_enum) OR ((completed_at IS NOT NULL) AND (completion_reference_type IS NOT NULL) AND (completion_reference_id IS NOT NULL)))),
    CONSTRAINT ck_tasks_completed_requires_evidence CHECK ((((status = 'COMPLETED'::public.tasks_status_enum) AND (completed_at IS NOT NULL) AND (completion_reference_type IS NOT NULL) AND (completion_reference_id IS NOT NULL)) OR ((status <> 'COMPLETED'::public.tasks_status_enum) AND (completed_at IS NULL) AND (completion_reference_type IS NULL) AND (completion_reference_id IS NULL)))),
    CONSTRAINT ck_tasks_completion_reference_type_allowed CHECK (((completion_reference_type IS NULL) OR ((completion_reference_type)::text = ANY (ARRAY['VISIT'::text, 'NOTE'::text, 'DOCUMENT'::text, 'CLINICAL_NOTE'::text])))),
    CONSTRAINT tasks_completion_evidence_consistency CHECK ((((status = 'COMPLETED'::public.tasks_status_enum) AND (completed_at IS NOT NULL) AND (completion_reference_type IS NOT NULL) AND (completion_reference_id IS NOT NULL)) OR ((status <> 'COMPLETED'::public.tasks_status_enum) AND (completed_at IS NULL) AND (completion_reference_type IS NULL) AND (completion_reference_id IS NULL))))
);


ALTER TABLE public.tasks OWNER TO sns;

--
-- Name: tenant_rule_toggles; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.tenant_rule_toggles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_id uuid NOT NULL,
    workflow character varying(32) NOT NULL,
    rule_id character varying(128) NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tenant_rule_toggles OWNER TO sns;

--
-- Name: tenants; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.tenants (
    id uuid NOT NULL,
    legal_name text NOT NULL,
    display_name text NOT NULL,
    status text DEFAULT 'ACTIVE'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    npi character varying(10) NOT NULL,
    tax_id character varying(15),
    ptan character varying(32),
    tenant_type character varying,
    environment_tag character varying,
    environment_type text DEFAULT 'PRODUCTION'::text,
    allow_full_reset boolean DEFAULT false
);


ALTER TABLE public.tenants OWNER TO sns;

--
-- Name: user_interface_roles; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.user_interface_roles (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    user_id uuid NOT NULL,
    interface_id uuid NOT NULL,
    role_id uuid NOT NULL,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone
);


ALTER TABLE public.user_interface_roles OWNER TO sns;

--
-- Name: users; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.users (
    email character varying NOT NULL,
    full_name character varying NOT NULL,
    role character varying NOT NULL,
    license_number character varying,
    active boolean,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    tenant_id uuid NOT NULL,
    has_admin_access boolean DEFAULT false,
    access_level character varying(32) NOT NULL
);


ALTER TABLE public.users OWNER TO sns;

--
-- Name: v_idg_compliance; Type: VIEW; Schema: public; Owner: sns
--

CREATE VIEW public.v_idg_compliance AS
 SELECT r.id AS idg_review_id,
    r.patient_id,
    (md.attestation_id IS NOT NULL) AS has_md_attestation,
    (count(s.id) > 0) AS has_signature
   FROM ((public.idg_reviews r
     LEFT JOIN public.idg_md_attestations md ON (((md.idg_id = r.id) OR (md.idg_review_id = r.id))))
     LEFT JOIN public.idg_signatures s ON ((s.idg_review_id = r.id)))
  GROUP BY r.id, r.patient_id, md.attestation_id;


ALTER VIEW public.v_idg_compliance OWNER TO sns;

--
-- Name: visit_minutes; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.visit_minutes (
    id character varying NOT NULL,
    visit_id character varying NOT NULL,
    discipline character varying NOT NULL,
    minutes integer NOT NULL,
    units integer NOT NULL,
    tenant_id uuid,
    service_date date,
    status character varying(32) DEFAULT 'DRAFT'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    created_by character varying(255)
);


ALTER TABLE public.visit_minutes OWNER TO sns;

--
-- Name: visits; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.visits (
    patient_id uuid NOT NULL,
    provider_id uuid NOT NULL,
    visit_type character varying NOT NULL,
    visit_datetime timestamp with time zone,
    status character varying,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    is_supervisory boolean DEFAULT false NOT NULL,
    finalized_at timestamp with time zone,
    finalized_by uuid,
    chha_poc_id uuid,
    acuity_state_at_visit character varying(32),
    tenant_id uuid NOT NULL,
    finalized_role_id uuid,
    finalized_interface_id uuid,
    visit_discipline character varying(16) NOT NULL,
    visit_mode character varying NOT NULL,
    updated_by uuid,
    deleted_at timestamp with time zone,
    deleted_by uuid,
    form_type text NOT NULL,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    documented_minutes integer,
    billing_units integer,
    is_billable boolean DEFAULT true,
    billing_cycle_id uuid,
    CONSTRAINT visits_form_type_check CHECK ((form_type = ANY (ARRAY['AFTER_DEATH'::text, 'AFTER_HOURS'::text, 'ANCILLARY_SUPPORT'::text, 'ASSESS'::text, 'BEREAVEMENT_VISIT'::text, 'DEATH_VISIT'::text, 'DECLINED_VISIT'::text, 'MISSED_VISIT'::text, 'OFFICE_HOURS'::text, 'ON_CALL_TRIAGE'::text, 'PRE_ADMIT_EVAL'::text, 'RESPITE_RELIEF'::text, 'ROUTINE_VISIT'::text, 'SHORT_FORM'::text, 'SUPV_VISIT_ONLY'::text, 'VOLUNTEER_SUPPORT'::text, 'WEEKENDS'::text])))
);


ALTER TABLE public.visits OWNER TO sns;

--
-- Name: volunteer_hours; Type: TABLE; Schema: public; Owner: sns
--

CREATE TABLE public.volunteer_hours (
    id uuid NOT NULL,
    volunteer_user_id uuid NOT NULL,
    date date NOT NULL,
    hours numeric(5,2) NOT NULL,
    activity_type public.volunteer_activity_type NOT NULL,
    supervised_by_user_id uuid,
    counts_for_5_percent boolean DEFAULT true NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_volunteer_hours_ck_volunteer_hours_positive CHECK ((hours > (0)::numeric))
);


ALTER TABLE public.volunteer_hours OWNER TO sns;

--
-- Name: eligibility_decisions id; Type: DEFAULT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.eligibility_decisions ALTER COLUMN id SET DEFAULT nextval('public.eligibility_decisions_id_seq'::regclass);


--
-- Data for Name: billing_organizations; Type: TABLE DATA; Schema: core; Owner: sns
--

COPY core.billing_organizations (id, name, capability_tier, active) FROM stdin;
00000000-0000-0000-0000-632455464000	NE Billing	AUTOMATED	t
\.


--
-- Data for Name: tenant_events; Type: TABLE DATA; Schema: core; Owner: sns
--

COPY core.tenant_events (id, tenant_id, event_type, event_at, actor_user_id, details_json) FROM stdin;
\.


--
-- Data for Name: tenants; Type: TABLE DATA; Schema: core; Owner: sns
--

COPY core.tenants (id, tenant_code, display_name, schema_name, status, created_at, activated_at, archived_at, billing_organization_id) FROM stdin;
01271980-0000-0000-0000-000005101977	LOVEFAITH	Love and Faith Hospice Services Inc	love_and_faith	ACTIVE	2026-06-04 22:44:05.518068-07	2026-06-04 22:44:05.518068-07	\N	\N
\.


--
-- Data for Name: user_tenants; Type: TABLE DATA; Schema: core; Owner: sns
--

COPY core.user_tenants (id, user_id, tenant_id, role, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: core; Owner: sns
--

COPY core.users (id, email, status, created_at, last_login_at) FROM stdin;
\.


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.accounts (id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.alembic_version (version_num) FROM stdin;
d45a0696e85b
\.


--
-- Data for Name: amendments; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.amendments (clinical_note_id, author_id, reason, content, created_at, id, updated_at, created_by, original_finalized_at) FROM stdin;
\.


--
-- Data for Name: assessment_discrepancies; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.assessment_discrepancies (id, tenant_id, patient_id, domain, baseline_assessment_id, comparing_assessment_id, discrepancy_summary, requires_idg_reconciliation, resolved, resolved_at, resolved_in_idg_meeting_id, resolution_note, created_at, resolution_type, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: assessment_references; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.assessment_references (id, assessment_id, referenced_assessment_id, reference_kind, reviewed_ack, reviewed_at, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: assessments; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.assessments (id, tenant_id, patient_id, discipline, assessment_type, occurred_at, status, signed_at, signed_by, risk_score, risk_level, data_json, document_id, visit_id, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.audit_logs (user_id, role, action, entity_type, entity_id, ip_address, created_at, id, updated_at, created_by, request_id, description, metadata, tenant_id) FROM stdin;
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	b575ca78-65fb-4b88-a532-173ce12e7979	\N	2026-06-13 20:06:12.595565	e2964edb-0455-4a60-8f59-ccbaccbda987	2026-06-13 20:06:12.596416	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	1d73c10c-c898-435b-a805-ea4242a8247b	\N	2026-06-13 20:13:01.440325	f75ca40e-bd7f-434f-9f7c-18674fbb12c4	2026-06-13 20:13:01.441168	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	56066446-e7d4-4697-baa1-08aa94bd9778	\N	2026-06-13 20:14:23.207955	5731cb4d-659f-4264-a583-f19cf60cb9ef	2026-06-13 20:14:23.208615	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	56066446-e7d4-4697-baa1-08aa94bd9778	\N	2026-06-13 20:19:08.32417	3828ad33-f438-4ae6-a975-347c6a654cb0	2026-06-13 20:19:08.325085	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:27:00.71068	faeea54a-fa04-4074-b90e-64579fd43c2f	2026-06-16 01:27:00.715032	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:28:59.427465	9e3deed3-ab64-4dde-bffe-13c76ce6e44f	2026-06-16 01:28:59.430509	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:29:32.935096	e0b0beda-42a9-4b9d-a77c-d88b5afa087c	2026-06-16 01:29:32.936135	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:29:47.599958	82ca408a-52b3-4be7-b5cf-5a98a31c4314	2026-06-16 01:29:47.601908	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:30:14.144885	97dfca62-128c-4a35-8495-6812b9002040	2026-06-16 01:30:14.146903	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:51:29.100742	c5493050-c117-4f6a-97ce-427dc54130ab	2026-06-16 01:51:29.10285	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:51:58.575211	69b01dc1-57fe-4668-9bc5-7a1e472b813d	2026-06-16 01:51:58.577408	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:52:28.419316	854306f7-ef11-4c6e-b0d6-677b5da0a6d0	2026-06-16 01:52:28.420703	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:52:57.436156	97df1342-bb9b-4295-a786-07530b792239	2026-06-16 01:52:57.4375	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:53:26.819829	79fb2907-9ae5-4627-a442-d9c46c777972	2026-06-16 01:53:26.821295	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 01:53:45.647155	5f91425d-3d8d-4ff9-bafd-83af944f1930	2026-06-16 01:53:45.6484	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:02:00.106899	4d2b0515-3b54-46d2-ab60-6512d39a8cae	2026-06-16 02:02:00.110025	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:13:29.244421	c646f3cd-d82d-432a-ad6c-158bb7eba478	2026-06-16 02:13:29.249126	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:14:13.193168	b554ccf4-afe8-4a83-8385-dcd7552dc98c	2026-06-16 02:14:13.196711	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:19:58.393398	b12fd05c-bf4e-4925-bec5-dcaae9e65e2d	2026-06-16 02:19:58.396055	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:23:00.298446	b2671d32-34f1-4fa5-b330-43eea93566ac	2026-06-16 02:23:00.307142	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:25:23.286502	1b98314b-c44e-415f-98af-327367481e8a	2026-06-16 02:25:23.288417	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:26:26.965303	3594b82a-6eea-4a52-917d-8c6c3aa65e80	2026-06-16 02:26:26.967424	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	RECORD_REFUSAL	patient	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	2026-06-16 02:52:24.172975	dea2473a-e534-4943-af18-6dc24104deff	2026-06-16 02:52:24.178629	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	d5151e20-1957-4110-b382-d440973e159e	\N	2026-06-16 07:18:37.498923	41316c28-15f3-4001-8081-8b4c573fa114	2026-06-16 07:18:37.500462	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	d5151e20-1957-4110-b382-d440973e159e	\N	2026-06-16 08:15:50.463667	83b27acc-859b-4f17-939b-c838317671ed	2026-06-16 08:15:50.464849	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	d5151e20-1957-4110-b382-d440973e159e	\N	2026-06-16 08:15:50.501221	96d922fd-a30d-4e09-b365-974f295ff33f	2026-06-16 08:15:50.502763	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	52ef334a-bd94-44ca-9076-324dd35140f5	\N	2026-06-16 08:20:48.774845	04001947-8967-48bd-a466-a1afef0a1687	2026-06-16 08:20:48.775407	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	52ef334a-bd94-44ca-9076-324dd35140f5	\N	2026-06-16 09:40:38.297153	9d905b57-f077-48f2-a2f4-e4fbf04f52c8	2026-06-16 09:40:38.299058	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	52ef334a-bd94-44ca-9076-324dd35140f5	\N	2026-06-16 09:40:38.320459	5956020a-dc65-4367-9ae0-c62edf0bdbce	2026-06-16 09:40:38.322515	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	REOPEN_VISIT	visit	52ef334a-bd94-44ca-9076-324dd35140f5	\N	2026-06-16 09:50:06.118595	82622d9f-697b-47d2-9cc5-49b0186d2af2	2026-06-16 09:50:06.119147	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	070aed57-54e2-4ff5-ada7-b74078c57074	\N	2026-06-16 21:36:26.393658	27499df6-f65a-41ac-a39c-bb3a7b049dc8	2026-06-16 21:36:26.395077	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE	clinical_note	439af6a6-b6ad-4fcb-a436-09fb116979a0	\N	2026-06-16 21:42:13.028113	6b247bd2-2c58-4d65-9239-8b8640382e2d	2026-06-16 21:42:13.028764	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	2c644177-b526-4f98-8dcc-a2d8d97cf9ce	\N	2026-06-16 21:42:13.030263	580b0b82-c79c-44a6-b289-bcd6bbf27da1	2026-06-16 21:42:13.030939	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	6816fa02-27b0-466d-b265-47a64b7dda1b	\N	2026-06-16 21:48:42.234505	bc39cd63-1b26-4682-90f4-615aabfc6209	2026-06-16 21:48:42.235392	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE	clinical_note	8b4ddb14-5573-4209-8925-a9e9ac8821dc	\N	2026-06-16 21:49:03.524809	14b63227-9c19-46fe-abf0-3924e2c1ff1b	2026-06-16 21:49:03.525248	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	207696ae-c5c2-4064-a7c6-5c7a7297d16b	\N	2026-06-17 17:03:05.943614	2a39b03c-97fa-4034-a022-ea8b781efccc	2026-06-17 17:03:05.943614	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	4eacb9e7-59d7-4147-b1ff-1cbe4bd2c94f	\N	2026-06-16 21:49:03.534103	a0b1de98-754d-4a6f-8db1-1d4857b7941c	2026-06-16 21:49:03.534606	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE	clinical_note	c8ea6fe3-0fbc-4368-90cf-7ab81a89efc6	\N	2026-06-16 21:53:37.721022	3c9ef9c2-c92d-467b-ae2f-d2e29053fd00	2026-06-16 21:53:37.723713	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	2dc97c3c-e0f2-4ad6-bbb1-f29be19a2757	\N	2026-06-16 21:53:37.726249	daf116b1-78d3-4b9b-b537-2e65eb5434ba	2026-06-16 21:53:37.727015	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	6816fa02-27b0-466d-b265-47a64b7dda1b	\N	2026-06-16 21:58:37.626379	ddb84e8e-e3fc-4feb-ba40-d0b54b0c9317	2026-06-16 21:58:37.626944	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	6816fa02-27b0-466d-b265-47a64b7dda1b	\N	2026-06-16 21:58:37.660567	43007f5b-d43f-4258-a464-d72c11f1fb65	2026-06-16 21:58:37.667468	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE	clinical_note	c53ca917-8c81-42fb-a3fa-2e465c20858b	\N	2026-06-16 21:58:52.370602	733915c7-4b19-4415-a2fc-00ec0cf0c7ad	2026-06-16 21:58:52.371047	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	5a05b299-9569-4e46-8453-55a7e0956324	\N	2026-06-16 21:58:52.381207	57dc7cb0-097a-4008-92d9-2a98bdfc1ef9	2026-06-16 21:58:52.383402	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE	clinical_note	907c5379-61fc-46b5-9b47-dd86f76b425e	\N	2026-06-16 22:04:07.097494	d88930d3-e85a-4995-bc0e-f8934b8e0032	2026-06-16 22:04:07.097899	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	b86d6429-32db-4b4f-8ed4-e4c826ad5b9a	\N	2026-06-16 22:04:07.108346	34ee9ca1-e335-4981-b14f-18905286df9e	2026-06-16 22:04:07.109446	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	FINALIZE_NOTE	clinical_note	907c5379-61fc-46b5-9b47-dd86f76b425e	\N	2026-06-16 22:06:36.184803	204ef130-9daf-4f95-87df-193c1400d973	2026-06-16 22:06:36.188568	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	AMEND_NOTE	clinical_note	907c5379-61fc-46b5-9b47-dd86f76b425e	\N	2026-06-16 22:09:01.996863	79fed01d-696b-425d-9244-3c27d211e6ab	2026-06-16 22:09:01.997314	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	02354ac6-7cf2-48a9-b998-e71b12d2f613	\N	2026-06-16 22:09:02.006543	07187f6e-bb07-42f2-b508-1099f9a5807e	2026-06-16 22:09:02.007431	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	AMEND_NOTE	clinical_note	907c5379-61fc-46b5-9b47-dd86f76b425e	\N	2026-06-16 22:49:52.768555	831d339e-ae48-4b42-9568-c9e8b83af501	2026-06-16 22:49:52.769983	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	918a869a-3ca2-49a4-9c7c-917c2904a016	\N	2026-06-16 22:49:52.780746	b8a8f8fe-e3f0-49c2-a828-095c7bf0628b	2026-06-16 22:49:52.781781	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE	clinical_note	843e319b-3bb3-4ce2-a5c0-64888b141f51	\N	2026-06-17 01:25:35.566484	9e981fb3-c342-4fbb-b4f0-85334d7178d2	2026-06-17 01:25:35.568117	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	e1e80b2f-b078-4ea4-85cb-d5a7d8cd6d14	\N	2026-06-17 01:25:35.579171	24751dad-e687-42c6-aec3-68ed38f2d627	2026-06-17 01:25:35.580814	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	AMEND_NOTE	clinical_note	907c5379-61fc-46b5-9b47-dd86f76b425e	\N	2026-06-17 04:46:16.172487	91952763-debe-479b-8789-6432301a27c2	2026-06-17 04:46:16.173285	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	CREATE_NOTE_VERSION	clinical_note_version	74dc2158-01a8-47ae-b2e7-52e645254e67	\N	2026-06-17 04:46:16.175488	0503829c-8f99-4fbe-83a2-301ca9d7965d	2026-06-17 04:46:16.176293	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	ea768440-15e3-44f2-af2e-a59e3e9d2c3a	\N	2026-06-17 13:05:55.333934	84f6287d-db5c-4ede-a94e-82e0494a4e0b	2026-06-17 13:05:55.333934	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	2d8b14f3-495c-49a7-b725-73e13595a300	\N	2026-06-17 13:30:43.132063	559f4065-ac2d-4f3d-9469-d39a63e0c8a0	2026-06-17 13:30:43.132063	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	855499dd-6853-429c-a215-3f16b823ec34	\N	2026-06-17 13:42:39.493483	56763f27-fe86-4343-9422-6c4b8736c184	2026-06-17 13:42:39.493483	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	855499dd-6853-429c-a215-3f16b823ec34	\N	2026-06-17 14:03:03.207877	573d67e9-9837-4768-9ba6-a80ee0133f20	2026-06-17 14:03:03.207877	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	70859c47-f638-4c55-aabd-55785638ebbe	\N	2026-06-17 14:07:10.925998	c4bfbf8d-faac-46e2-825a-266b4bc6b62e	2026-06-17 14:07:10.925998	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	70859c47-f638-4c55-aabd-55785638ebbe	\N	2026-06-17 15:11:59.194159	1f9cd8da-e474-40b5-9651-7d086267e009	2026-06-17 15:11:59.194159	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	ab660c1d-1726-4d7d-8908-9efe5b6b63a2	\N	2026-06-17 15:15:06.026502	6c87f189-9580-425d-881b-a485a7fbe06a	2026-06-17 15:15:06.026502	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	6b070683-5c39-49a3-b9c4-ad22759b3725	\N	2026-06-17 15:20:04.294652	02ca6212-50e7-48f7-b805-fe9d6e658a74	2026-06-17 15:20:04.294652	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	56645722-8484-4cbf-bf28-691a1613b37d	\N	2026-06-17 15:32:25.133638	4f3b6e07-d447-4083-b5ac-93dd9d9e8e8b	2026-06-17 15:32:25.133638	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	a9b00ad7-37cf-4cf3-9bcc-f33bd2b4620c	\N	2026-06-17 15:41:18.537461	3e986a7e-c84e-430c-a4c1-a1239e71efd5	2026-06-17 15:41:18.537461	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	ea90280f-567d-4620-a5e8-ea6c48ec2371	\N	2026-06-17 15:50:28.394965	e0643dbc-47b8-4a97-acd4-6f8e9305a3d8	2026-06-17 15:50:28.394965	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	0fc55794-4d18-4399-a77c-acade5384953	\N	2026-06-17 16:05:34.497516	f4502e5c-7125-4247-affc-7db2b1aea789	2026-06-17 16:05:34.497516	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	f2b96065-cbb3-41d7-b46d-2ce2254f0947	\N	2026-06-17 16:08:31.286215	5fddc121-e646-4dce-941f-41233e122afd	2026-06-17 16:08:31.286215	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	f2b96065-cbb3-41d7-b46d-2ce2254f0947	\N	2026-06-17 16:42:46.137939	78e4f73e-26e1-4b60-9bde-8bb768b3a402	2026-06-17 16:42:46.137939	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	207696ae-c5c2-4064-a7c6-5c7a7297d16b	\N	2026-06-17 17:07:58.041704	b91bd1c6-76b6-4bcf-bbbd-3d80e8757b4f	2026-06-17 17:07:58.041704	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	d8f716e6-adc3-49ca-905d-5f9b91605424	\N	2026-06-17 19:16:06.713206	52967b45-93b0-4fba-a941-807b891b10e8	2026-06-17 19:16:06.713206	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	4c1c0ac2-b8d4-4d39-a70e-06d3742000ed	\N	2026-06-17 20:22:13.752853	3f1c2526-a832-4e3d-99a0-460b56c8baeb	2026-06-17 20:22:13.752853	\N	\N	\N	\N	\N
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	a4848a92-2146-4379-9136-a683be161d3c	\N	2026-06-18 03:41:59.772674	7fa6dc1a-7e2d-403c-86da-bdfab024bd96	2026-06-18 03:41:59.774282	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	3148a86c-95ef-42ff-a76e-be5c2062f1da	\N	2026-06-17 20:42:17.348239	30c5fa48-2977-4bd6-99bb-a41ced2e95ad	2026-06-17 20:42:17.348239	\N	\N	\N	\N	\N
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	3148a86c-95ef-42ff-a76e-be5c2062f1da	\N	2026-06-17 20:48:02.818511	ba28bb42-b0e0-47b8-bbbc-91ec931b9bd2	2026-06-17 20:48:02.818511	\N	\N	\N	\N	\N
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	6eec7c79-2c3b-41c2-a546-64752f4b4037	\N	2026-06-18 04:03:41.883593	448bc1e0-d4b3-4925-aae4-d9adb03abd77	2026-06-18 04:03:41.885428	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	610e1d35-970e-48ea-8d80-ff8258aac9b8	\N	2026-06-18 19:00:51.623222	43aadd94-ba67-48fa-997e-0f844c8eee91	2026-06-18 19:00:51.643081	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	94aca749-cfb9-428f-b18b-766ef2d8b3aa	\N	2026-06-18 19:15:49.348783	23d998f0-7cff-4f4a-9b5f-597c61d11294	2026-06-18 19:15:49.354144	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	e81d76c0-d4e1-45e2-ac7f-08e8494396b8	\N	2026-06-18 19:43:44.357424	adb35cc1-bd42-46e1-8ea3-6b476a80c34e	2026-06-18 19:43:44.362209	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	COMPLETE_TASK	task	c5888177-6514-4853-8ee8-351ed13c7842	\N	2026-06-18 19:52:27.200424	21115dff-f820-4bc3-83c7-34bf8a6d09aa	2026-06-18 19:52:27.200957	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
86ed90d6-69d5-594f-bff7-f07dbdaeac9c	ADMIN	COMPLETE_TASK_BY_NOTE	task	c5888177-6514-4853-8ee8-351ed13c7842	\N	2026-06-18 20:30:39.850929	ee66d48b-ab6d-4bb3-b564-2e64d4295da8	2026-06-18 20:30:39.852641	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	0c9914fa-3013-4c0f-b7f1-7589b91a16b7	\N	2026-06-18 20:47:51.453067	0238e3cf-a1b5-4601-b70b-51723af11126	2026-06-18 20:47:51.459121	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	b9b18e20-1785-4277-b0a6-9ab3b5394e04	\N	2026-06-18 20:53:03.518977	e611b6ea-499e-49b8-a7a4-a2926603ec21	2026-06-18 20:53:03.521892	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	80e134d7-19cc-4d1d-b448-ac81ae82dd66	\N	2026-06-18 23:25:34.45389	c7194e5d-6c5b-4bdd-a33e-37fb58cb4fe3	2026-06-18 23:25:34.457968	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	c0e454c2-a409-466f-a855-82a7091516bb	\N	2026-06-18 23:29:04.627661	6cdf8f92-962a-406f-b8bf-481a41c561af	2026-06-18 23:29:04.631528	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	96a4d4cc-4dcd-48a7-b24b-12f0dae0a6d6	\N	2026-06-18 23:32:41.898544	6895cb61-3908-4ed0-a5e6-ad2792831c73	2026-06-18 23:32:41.901264	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	799ea183-d231-44d2-9137-0eae10c9c69d	\N	2026-06-18 23:36:03.191686	eacec39d-7961-43fd-b9b1-d50cc6d00e50	2026-06-18 23:36:03.192699	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	ea1b79c1-1cfb-4269-890a-1d88c65917ea	\N	2026-06-19 23:09:35.934709	a6ca806f-23cf-4093-9fa6-327e054caf9d	2026-06-19 23:09:35.934709	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	9f0a7767-cc83-4748-a28a-62fc1def4425	\N	2026-06-19 23:21:21.426045	a4d61ab0-fae9-4abe-8dd2-b692c7f85e79	2026-06-19 23:21:21.426045	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	01f634d4-dc96-4fc9-846c-0ee5a4c00fff	\N	2026-06-19 23:31:30.416223	b6873927-06f6-4389-be65-973805841e81	2026-06-19 23:31:30.416223	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	0bb94777-ed94-498a-90d9-55714e6cef49	\N	2026-06-19 23:32:21.422978	04e36cf6-6643-4e37-8a3e-8b50d8dc164c	2026-06-19 23:32:21.422978	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	6abaf367-63bb-4d7f-bd91-8db9cf7a57e7	\N	2026-06-20 02:26:09.529916	f9c3d495-f9ce-44be-8400-8f1f76d26246	2026-06-20 02:26:09.529916	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	9e45de7e-382a-46f9-ac1d-42ccb14e9689	\N	2026-06-20 02:45:11.175965	be8b6d93-1cb8-434a-a4f1-8bcf67dc1d04	2026-06-20 02:45:11.175965	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	9519d771-8935-46ee-b347-eda56f5a3328	\N	2026-06-20 03:17:09.607572	a6e99571-ffb3-4528-809d-26286ed2e1f3	2026-06-20 03:17:09.607572	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	a3bae172-7158-46b0-8a40-5f766623cf32	\N	2026-06-20 03:21:39.389158	9c5592ee-634c-4a4c-b26a-5fb3928ecd35	2026-06-20 03:21:39.389158	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	7eb5dc66-52ef-448b-a5bc-71ff496f512a	\N	2026-06-20 03:40:52.959578	f01093ce-dd84-4cd8-87f1-fdc87b18780f	2026-06-20 03:40:52.959578	\N	\N	\N	\N	\N
28b66dcb-3ff0-5868-b147-b24f63db74a6	CLINICIAN	CLINICAL_NOTE_VALIDATED	clinical_note	31d710cc-f9aa-4c68-b0c9-6079fc932cf5	\N	2026-06-20 03:44:40.491072	43861cd2-dc2f-4179-ac2d-ccf80c04d68f	2026-06-20 03:44:40.491072	\N	\N	\N	\N	\N
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	8c5499c4-0c33-41b1-ba10-8ac856202e8a	\N	2026-06-20 20:16:36.861829	51852731-0a31-4010-beb3-7680df4bdc18	2026-06-20 20:16:36.863334	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	8c5499c4-0c33-41b1-ba10-8ac856202e8a	\N	2026-06-20 21:48:52.320818	346e9d90-302e-4ab0-bae7-d33c0a85eab4	2026-06-20 21:48:52.321784	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	8c5499c4-0c33-41b1-ba10-8ac856202e8a	\N	2026-06-20 21:48:52.35769	ea8af52c-920e-400a-a20a-f06dd04608a5	2026-06-20 21:48:52.35812	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	ef9ea898-dc36-4b3d-a054-59fc74140e41	\N	2026-06-22 16:41:21.198377	2379c7b0-9802-48ec-9d17-b7e90a34df89	2026-06-22 16:41:21.202645	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	ef9ea898-dc36-4b3d-a054-59fc74140e41	\N	2026-06-22 16:47:42.344584	d5d8a59a-1a6f-4da2-bfad-03ef813a3f33	2026-06-22 16:47:42.346885	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	ef9ea898-dc36-4b3d-a054-59fc74140e41	\N	2026-06-22 16:47:42.361869	bc17515c-42a9-4c74-afaf-6464297d232b	2026-06-22 16:47:42.362292	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	05150a42-348e-44d5-8564-fcb277f42ae8	\N	2026-06-22 17:17:13.717164	4da97400-8ca6-4ccf-b387-90a3f76b8f58	2026-06-22 17:17:13.723958	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	70bbcd3b-5679-4f03-bc57-9c994ce75804	\N	2026-06-22 17:17:56.795812	b1404a58-377b-49e0-806f-d4ab058c2612	2026-06-22 17:17:56.797548	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	938c4bcb-2365-4b12-8254-a70521d88f26	\N	2026-06-22 17:53:49.078454	47b5122a-6368-4064-ad8d-86e85dc8094a	2026-06-22 17:53:49.083048	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	f05d7cab-5732-42c5-8f00-aec71ca234a9	\N	2026-06-22 18:39:38.436559	d3b95679-1f36-47f3-8be7-7a1062dd176b	2026-06-22 18:39:38.439494	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	b0bd85ab-f8b9-4591-89a3-14a6fc4ffafb	\N	2026-06-23 21:08:09.538639	09411ed7-49ef-42fb-b2b3-bded4b302b96	2026-06-23 21:08:09.542421	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	ee91b5df-8472-4611-ae03-ef44cdd50528	\N	2026-06-23 21:44:28.452126	9588c42d-5f32-45a8-b384-62686d04c706	2026-06-23 21:44:28.458776	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	a9cafd3e-f6ce-42b0-9c3f-fc3134b09c8e	\N	2026-06-24 05:24:18.734522	73d03d43-adbb-4286-9aa4-40fd0464be06	2026-06-24 05:24:18.74164	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	2ba784d0-84a5-4800-9506-5c45f8c56716	\N	2026-06-24 05:25:12.782607	2a1b2eff-34ab-46c6-9db1-4aa520687bad	2026-06-24 05:25:12.783815	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	60e55b0b-775c-429c-ab30-6a35507499f3	\N	2026-06-24 05:25:26.246915	46a6e66c-544b-4a24-840a-3cb9d3bfcd1d	2026-06-24 05:25:26.248561	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	7f2f22e4-b3d5-483d-a8c2-9128c7b1e331	\N	2026-06-24 05:42:19.218317	3a254dc6-6746-49ba-b4ac-835a2df74c25	2026-06-24 05:42:19.22293	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	8707140c-c0cf-4f8c-b42a-76dd5b18e831	\N	2026-06-24 05:43:15.489775	cffd4eb8-7834-48ec-b60a-240602138d13	2026-06-24 05:43:15.491002	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	d80c9896-5965-4900-adf7-80a60e7c6431	\N	2026-06-24 05:43:37.009688	5eea1b21-c57c-4005-9d15-f772f9cf8661	2026-06-24 05:43:37.011883	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	3700a014-85f9-4c89-904e-c98fb586f148	\N	2026-06-24 06:25:42.758617	6e600114-22a9-4c4e-a1b9-06a1726efeef	2026-06-24 06:25:42.763604	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	97d6b905-8c88-44f8-bf02-2e9a4eda6d0b	\N	2026-06-24 06:29:43.024479	e22db8f7-978c-4763-a518-4717caf30d2a	2026-06-24 06:29:43.027132	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	2282f8b3-48d4-4854-9656-1441d8f8965e	\N	2026-06-24 06:31:43.660207	f0890c54-0fee-4e0b-b7ec-0bb14c688c6d	2026-06-24 06:31:43.66207	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	5b176a26-5824-43a9-b5f8-d07c4f4deb75	\N	2026-06-24 08:08:22.109201	8293ac4d-7622-44a2-a023-e800c7f74748	2026-06-24 08:08:22.114355	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	5b176a26-5824-43a9-b5f8-d07c4f4deb75	\N	2026-06-24 08:14:30.209873	4c4c2a84-9650-4731-85da-81e9a264697b	2026-06-24 08:14:30.210792	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	5b176a26-5824-43a9-b5f8-d07c4f4deb75	\N	2026-06-24 08:14:30.21855	02b92887-fc1d-40f5-b9f2-487524e6e4e4	2026-06-24 08:14:30.218847	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	14d75658-1319-4684-9096-8ceb7deaaf81	\N	2026-06-24 08:18:22.281069	d2190d15-b47d-437b-8b55-5cdc7a7b17de	2026-06-24 08:18:22.285517	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	14d75658-1319-4684-9096-8ceb7deaaf81	\N	2026-06-24 08:19:50.232138	1fdc403b-8ff7-44d7-8e15-ca32bc8b1b39	2026-06-24 08:19:50.23349	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	14d75658-1319-4684-9096-8ceb7deaaf81	\N	2026-06-24 08:19:50.25512	6746c8a1-20d9-4385-b00e-00a518a910e0	2026-06-24 08:19:50.255877	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	4c16871d-ddc9-490e-9493-f05de07e1238	\N	2026-06-24 08:28:02.410628	e37b275a-a064-47ea-87c5-41149b3ce85d	2026-06-24 08:28:02.417364	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	4c16871d-ddc9-490e-9493-f05de07e1238	\N	2026-06-24 08:28:39.830318	b64c2d74-7adc-4256-bfd5-6b0ccb2ee746	2026-06-24 08:28:39.831344	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	4c16871d-ddc9-490e-9493-f05de07e1238	\N	2026-06-24 08:28:39.847024	1cd73455-e830-44c0-988d-a2c00f04d4ce	2026-06-24 08:28:39.847601	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	44036a5e-2436-414f-8906-17cd5876e09d	\N	2026-06-24 08:51:47.803456	e871dd6f-3cb6-462e-af27-ec80d8898fa4	2026-06-24 08:51:47.808708	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	d4debd4b-ee7f-43c3-8af6-a1dd502fdee6	\N	2026-06-24 09:02:07.53899	5b75c54f-f90c-4b64-8717-54914a68f60c	2026-06-24 09:02:07.543795	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	8caa3d8b-222b-4a1a-ba1c-6c21cf72fbaf	\N	2026-06-24 09:29:57.974148	842f85a3-c66f-467c-bdac-6e8fdff7a48e	2026-06-24 09:29:57.977903	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	8caa3d8b-222b-4a1a-ba1c-6c21cf72fbaf	\N	2026-06-24 09:30:09.090087	62f55cf7-cd0b-4839-8124-ac403359a8ec	2026-06-24 09:30:09.090449	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	8caa3d8b-222b-4a1a-ba1c-6c21cf72fbaf	\N	2026-06-24 09:30:09.101742	bb08d19d-d9a5-48fe-9e64-aacd7ca65ada	2026-06-24 09:30:09.102293	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	3ef6c5f3-a786-4fb6-a84a-d0f68328e720	\N	2026-06-24 09:33:58.380867	34c227f4-9868-4f73-8fd3-a42567e4a9e3	2026-06-24 09:33:58.382947	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	3ef6c5f3-a786-4fb6-a84a-d0f68328e720	\N	2026-06-24 09:34:16.768285	bfb2ed47-b62b-4180-b172-31e76d5da8d3	2026-06-24 09:34:16.768869	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	3ef6c5f3-a786-4fb6-a84a-d0f68328e720	\N	2026-06-24 09:34:16.773849	923a0706-e86c-4b1b-802c-1c7f8467ee81	2026-06-24 09:34:16.774402	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	5247efd9-2b1e-4f1d-880f-cb56c3c3baf9	\N	2026-06-24 09:44:32.165303	1211664d-19d5-46d6-b516-28337cdff2f8	2026-06-24 09:44:32.171866	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	5247efd9-2b1e-4f1d-880f-cb56c3c3baf9	\N	2026-06-24 09:44:42.28668	a23052e3-7de4-4b7f-9532-868e47c3c55b	2026-06-24 09:44:42.287258	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	5247efd9-2b1e-4f1d-880f-cb56c3c3baf9	\N	2026-06-24 09:44:42.299839	af195345-e365-4a0f-bab4-1ec11e016036	2026-06-24 09:44:42.300313	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	862e8e53-9060-4ae2-af44-afff8b097154	\N	2026-06-24 22:09:38.58546	821e4534-8366-4750-a74a-e97e0eca40ef	2026-06-24 22:09:38.590713	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	862e8e53-9060-4ae2-af44-afff8b097154	\N	2026-06-24 22:13:38.226171	6e7fd44f-a31d-476d-b20a-0c5a621f1138	2026-06-24 22:13:38.22883	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	862e8e53-9060-4ae2-af44-afff8b097154	\N	2026-06-24 22:13:38.237111	f90ab9e1-355a-4a1c-9bb5-2a53ab70e1de	2026-06-24 22:13:38.237415	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	7879abe4-3d62-4da8-9243-eb7a514074bb	\N	2026-06-24 22:21:40.114197	be3d8135-e710-4d3f-a232-3128a3b1126e	2026-06-24 22:21:40.117556	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	7879abe4-3d62-4da8-9243-eb7a514074bb	\N	2026-06-24 22:21:59.311514	e7943d75-4596-4fe2-adf1-a5c1db854ea8	2026-06-24 22:21:59.311853	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	7879abe4-3d62-4da8-9243-eb7a514074bb	\N	2026-06-24 22:21:59.320714	67d6cf95-6bef-4107-b231-72679f85451d	2026-06-24 22:21:59.320966	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	f8e7aec1-a019-497e-ab51-50ef5c59fe10	\N	2026-06-24 23:02:27.384293	26dc8a48-d551-42c4-b7e1-51c16dd93134	2026-06-24 23:02:27.389543	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	f8e7aec1-a019-497e-ab51-50ef5c59fe10	\N	2026-06-24 23:04:31.207366	447b28a5-b09d-4466-9cf6-1ba198a95629	2026-06-24 23:04:31.207732	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	f8e7aec1-a019-497e-ab51-50ef5c59fe10	\N	2026-06-24 23:04:31.220854	6dd4591e-c04c-4e74-bbf5-8a8a31962cfb	2026-06-24 23:04:31.221823	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	9d0f1496-fc3e-4b95-a733-722d93174dc0	\N	2026-06-24 23:23:05.635843	ec064223-559f-4bf7-93ff-a604f47ed153	2026-06-24 23:23:05.637495	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	9d0f1496-fc3e-4b95-a733-722d93174dc0	\N	2026-06-24 23:47:50.498701	f962d10c-bbbe-4026-a226-43cadb7f077b	2026-06-24 23:47:50.499165	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	9d0f1496-fc3e-4b95-a733-722d93174dc0	\N	2026-06-24 23:47:50.504978	d9fcaf32-3272-4ecc-96b9-28153b9ec2a5	2026-06-24 23:47:50.50523	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CREATE_VISIT	visit	e3ebf064-66dd-40f2-92a9-5edf8fee4c72	\N	2026-06-25 00:00:58.52584	4d73ce9b-52dd-4b48-ad2f-b57543b358cd	2026-06-25 00:00:58.527684	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	97f0f7b2-dfd2-456a-8193-47aa421bd94b	\N	2026-06-25 03:43:59.544939	0b3bac6f-b6a6-4e50-812c-4bde2062fefe	2026-06-25 03:43:59.545666	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	97f0f7b2-dfd2-456a-8193-47aa421bd94b	\N	2026-06-25 03:46:30.527005	d424fd92-336c-415e-a46a-c7a0c3b4612b	2026-06-25 03:46:30.527293	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	97f0f7b2-dfd2-456a-8193-47aa421bd94b	\N	2026-06-25 03:46:30.535712	8651532f-434f-4368-81b7-634cdd9fe6c3	2026-06-25 03:46:30.535958	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	4bff4ba5-c00c-4f9e-afe4-98e5c7f175b1	\N	2026-06-25 04:03:12.473082	d16d2628-2380-48ee-88dd-9514a137387c	2026-06-25 04:03:12.474092	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	4bff4ba5-c00c-4f9e-afe4-98e5c7f175b1	\N	2026-06-25 04:03:35.405859	d056bc14-5dde-499f-b790-6875267d964c	2026-06-25 04:03:35.406163	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	4bff4ba5-c00c-4f9e-afe4-98e5c7f175b1	\N	2026-06-25 04:03:35.417156	37d52f7b-a45e-4441-8abb-ef395bf9ba11	2026-06-25 04:03:35.417456	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	790f4629-c251-4220-abdf-0876b9d3e610	\N	2026-06-25 04:44:41.594525	60492e4c-26bd-4477-adff-0214903165c9	2026-06-25 04:44:41.595226	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	b1517c60-6825-4d10-a385-22d33e058c50	\N	2026-06-25 05:40:25.003956	9f6e81a5-434f-4c74-aa82-eb03b866002e	2026-06-25 05:40:25.004653	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	b1517c60-6825-4d10-a385-22d33e058c50	\N	2026-06-25 05:55:34.326999	b969851e-4f60-4c4e-99e7-99f461246d12	2026-06-25 05:55:34.327859	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	b1517c60-6825-4d10-a385-22d33e058c50	\N	2026-06-25 05:55:34.335701	ef7a4299-2e3e-4180-bac3-36ba0328aaf4	2026-06-25 05:55:34.336004	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	00e5b620-2546-4c70-bfa0-33eaf1a20bcb	\N	2026-06-25 05:59:16.872366	80ac13c4-3b49-429b-9465-014036fcce61	2026-06-25 05:59:16.873856	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	00e5b620-2546-4c70-bfa0-33eaf1a20bcb	\N	2026-06-25 05:59:29.968377	8414a59a-6f33-41f7-a262-10e8ddc9e760	2026-06-25 05:59:29.969323	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	00e5b620-2546-4c70-bfa0-33eaf1a20bcb	\N	2026-06-25 05:59:29.995936	efa361b9-c544-4578-8475-a55b3ff3c762	2026-06-25 05:59:29.996301	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	738def69-e0dd-4426-85d2-46c3b5b1b561	\N	2026-06-25 06:13:19.71686	72d79dff-395a-4e11-8c50-8a4edc9751ba	2026-06-25 06:13:19.718114	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	738def69-e0dd-4426-85d2-46c3b5b1b561	\N	2026-06-25 06:13:32.600926	64cbe64e-44f0-4fa2-9712-b3f33fc52665	2026-06-25 06:13:32.601723	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	738def69-e0dd-4426-85d2-46c3b5b1b561	\N	2026-06-25 06:13:32.617705	e9314dd0-f9b4-4032-a694-a62ba78aff6d	2026-06-25 06:13:32.618242	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	1f42ca93-5e25-4bf1-8822-b7a06cf1feee	\N	2026-06-25 06:18:05.202447	fe5be5f0-b9f2-4deb-b84b-c7d2bfec05b4	2026-06-25 06:18:05.202801	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	1f42ca93-5e25-4bf1-8822-b7a06cf1feee	\N	2026-06-25 06:18:37.584968	116eab1a-4bb4-4192-abe4-1993b6c182a3	2026-06-25 06:18:37.585655	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	1f42ca93-5e25-4bf1-8822-b7a06cf1feee	\N	2026-06-25 06:18:37.592046	f45e8de2-17d0-411a-92d7-3d844879d928	2026-06-25 06:18:37.592559	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	b00954fc-14c5-43cd-a331-66658d17a886	\N	2026-06-25 06:33:12.336247	4eba5aab-ea27-4b7e-9112-d75b1b7c5b71	2026-06-25 06:33:12.336958	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	b00954fc-14c5-43cd-a331-66658d17a886	\N	2026-06-25 06:33:31.668804	449a68ff-ce8b-4461-99eb-726bc8f14a7d	2026-06-25 06:33:31.669128	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	b00954fc-14c5-43cd-a331-66658d17a886	\N	2026-06-25 06:33:31.677963	c0bde4ca-1641-4b84-ba63-8ec8c24fbc3b	2026-06-25 06:33:31.678465	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	b96d6e24-84a6-48d0-a1ec-6158c87f77eb	\N	2026-06-25 19:33:50.305399	d113796f-1a70-4ce2-b117-b2c21898c85b	2026-06-25 19:33:50.305399	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	b96d6e24-84a6-48d0-a1ec-6158c87f77eb	\N	2026-06-25 19:33:50.322972	dddfbcab-7454-4e9f-af4d-11c035c854f5	2026-06-25 19:33:50.322972	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	cbc13298-ca80-4bf1-aa84-8136b02fab00	\N	2026-06-26 03:36:48.174595	79687e5f-11b3-4dd1-b0df-f66326342461	2026-06-26 03:36:48.174595	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	cbc13298-ca80-4bf1-aa84-8136b02fab00	\N	2026-06-26 03:49:35.061359	9e3ee4fc-0c87-450a-818c-5cd28e4b1b2a	2026-06-26 03:49:35.061359	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	cbc13298-ca80-4bf1-aa84-8136b02fab00	\N	2026-06-26 03:49:35.071942	f50fb01c-f228-49c2-85e2-e9fb307314ea	2026-06-26 03:49:35.071942	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	67f6ac2e-1e6b-4a03-a7af-6c80279be394	\N	2026-06-26 03:54:24.847489	8efd0a86-a66e-402b-9fdb-164930b96a74	2026-06-26 03:54:24.847489	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	FINALIZE_VISIT	visit	67f6ac2e-1e6b-4a03-a7af-6c80279be394	\N	2026-06-26 03:54:38.342434	e9990e8d-27a3-4c56-ac6b-b3e1225fce3d	2026-06-26 03:54:38.342434	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	\N	\N	01271980-0000-0000-0000-000005101977
d7b8a870-891d-56ac-8bf1-c14a151ff7ea	SYSTEM	CONDITION_ENGINE_EVALUATED	visit	67f6ac2e-1e6b-4a03-a7af-6c80279be394	\N	2026-06-26 03:54:38.345645	7cf069ce-8c1d-48c6-989c-9a5f4832469e	2026-06-26 03:54:38.345645	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	6333dbb9-04e5-4064-aae1-a26ee9ec6a75	\N	2026-06-28 17:42:51.29763	32421648-8c9a-4ea3-919e-d81dec367d07	2026-06-28 17:42:51.29763	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	8d198a2d-1620-4acf-99c2-f64660022e97	\N	2026-06-28 18:02:24.75525	3047dcaf-e95f-4b52-a658-556b12b03791	2026-06-28 18:02:24.75525	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	28be0c20-149e-4de5-b0e0-f5cbcc449e1b	\N	2026-06-28 18:05:00.676829	5092230c-fd4b-403d-bf05-47e6a168a5fd	2026-06-28 18:05:00.676829	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	5a0897a5-cd08-47d1-9246-ea8e86999bdb	\N	2026-06-28 18:13:50.626383	e58561c2-2149-453b-a991-7abeb789169e	2026-06-28 18:13:50.626383	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	bfa7c066-9dc9-48b6-9f33-5186e7419b24	\N	2026-06-28 18:19:50.465552	9cfa1aba-f0ae-4ec0-8470-4fcf941f6298	2026-06-28 18:19:50.465552	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	70751c0b-6318-4ce3-9b1b-d05c77a083cc	\N	2026-06-28 18:24:43.142649	8ae94f32-b9f5-42a3-a5b6-408af1ba9077	2026-06-28 18:24:43.142649	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	56cc3beb-8fce-42f5-8c87-9d3a5869c955	\N	2026-06-28 18:31:20.704905	e8da6c8c-be63-4668-8c6e-046d18af71b7	2026-06-28 18:31:20.704905	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	a8de4983-b448-4556-af72-65c5543ef055	\N	2026-06-28 18:56:47.808976	80698fde-08ae-429c-9e6a-7dcfa4f95a38	2026-06-28 18:56:47.808976	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	5f1040c5-192b-4965-865c-cfe72f3b7ecb	\N	2026-06-28 19:15:10.036488	26eb4fe4-f0d4-4117-ba28-4ec00ac9588c	2026-06-28 19:15:10.036488	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
28b66dcb-3ff0-5868-b147-b24f63db74a6	SYSTEM	CREATE_VISIT	visit	56e33c56-34dd-4ce4-9183-7d2564460ab7	\N	2026-06-29 03:57:45.244355	926f8fb0-ed9f-4c4a-8f0a-c0f59546979c	2026-06-29 03:57:45.244355	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	\N	\N	01271980-0000-0000-0000-000005101977
\.


--
-- Data for Name: authorization_records; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.authorization_records (id, patient_id, payer_name, auth_status, tenant_id, created_at, updated_at, authorization_number, service_type, status, created_by) FROM stdin;
\.


--
-- Data for Name: benefit_periods; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.benefit_periods (id, patient_id, start_date, end_date, is_current, created_at, updated_at, tenant_id, created_by, benefit_type, period_number, election_date) FROM stdin;
3ac2b8e3-676b-48fa-afeb-ee3ab7bd223c	1af2861b-49ca-4c53-90f7-751d67222978	2026-06-22	2026-09-19	t	2026-06-22 14:13:42.049693-07	2026-06-22 14:13:42.049693-07	01271980-0000-0000-0000-000005101977	\N	INITIAL	1	2026-06-22
\.


--
-- Data for Name: bereavement_cases; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.bereavement_cases (id, patient_id, start_date, end_date, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: bereavement_declines; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.bereavement_declines (id, bereavement_task_id, declined_role, decline_reason, recorded_by_user_id, recorded_at) FROM stdin;
\.


--
-- Data for Name: bereavement_tasks; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.bereavement_tasks (id, bereavement_case_id, task_subtype, due_date, status, primary_roles_allowed, fallback_role, decline_record_exists, completed_by_user_id, completed_by_role, completed_at, evidence_id, exception_reason, billable, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: billing_cycles; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.billing_cycles (id, tenant_id, month, year, start_date, end_date, status, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: billing_snapshot; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.billing_snapshot (id, patient_id, data) FROM stdin;
\.


--
-- Data for Name: billing_snapshots; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.billing_snapshots (id, tenant_id, patient_id, billing_cycle_id, snapshot_type, version, data, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: billing_summaries; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.billing_summaries (id, tenant_id, patient_id, billing_cycle_id, total_units, total_amount, risk_score, status, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: billing_summary; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.billing_summary (id, patient_id, billing_cycle_id, total_units, status, risk_score) FROM stdin;
\.


--
-- Data for Name: certifications; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.certifications (id, patient_id, benefit_period_id, cert_type, signed_at, effective_date, signed_by_role, signed_by_user_id, status, created_at, updated_at, created_by, certification_type, effective_start_date, effective_end_date, primary_dx, narrative) FROM stdin;
fd400d68-bf06-4d48-a280-8e1dfe32c021	1af2861b-49ca-4c53-90f7-751d67222978	3ac2b8e3-676b-48fa-afeb-ee3ab7bd223c	INITIAL	2026-06-22 14:24:58.603631	2026-06-22	MEDICAL_DIRECTOR	\N	COMPLETED	2026-06-22 14:24:58.603631	2026-06-22 14:24:58.603631	\N	INITIAL	2026-06-22	2026-09-19	G31.1	Patient demonstrates progressive decline, functional impairment, and dependence in ADLs consistent with prognosis of less than six months.
\.


--
-- Data for Name: change_of_condition; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.change_of_condition (id, visit_id, severity, reason, created_at) FROM stdin;
\.


--
-- Data for Name: chha_pocs; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.chha_pocs (id, patient_id, status, effective_start, effective_end, frequency, adl_scope, instructions, safety_precautions, finalized_at, finalized_by, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: chha_visit_outcomes; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.chha_visit_outcomes (id, tenant_id, patient_id, visit_id, poc_reference_id, tolerance_to_care, condition_during_visit, skin_outcome, pain_or_change_observed, rn_notification_required, rn_notified, rn_notified_at, rn_notified_name, caregiver_instruction_provided, caregiver_understanding_confirmed, exception_narrative, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: chha_visit_task_results; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.chha_visit_task_results (id, outcome_id, section_code, task_code, was_assigned, completed, refused, not_done, observation_code, result_note, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: claim_export_log; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.claim_export_log (id, patient_id, billing_cycle_id, file_path, override_used, override_reason, created_at) FROM stdin;
\.


--
-- Data for Name: claim_export_logs; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.claim_export_logs (id, tenant_id, patient_id, billing_cycle_id, file_path, export_type, status, override_used, override_reason, override_approved_by, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: clinical_note_versions; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.clinical_note_versions (id, clinical_note_id, version_number, content, amend_reason, created_at, created_by, is_active, updated_at) FROM stdin;
\.


--
-- Data for Name: clinical_notes; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.clinical_notes (visit_id, author_id, note_type, content, status, finalized_at, id, created_at, updated_at, created_by, finalized_by, tenant_id, finalized_role_id, finalized_interface_id, patient_id, care_level, visit_type, visit_origin, note_category, encounter_type, discipline, encounter_date, observed_data, patient_reported, caregiver_reported, assessment, interventions, plan_of_care_updates, needs_clarification, red_flags, audit_flags, incident_required, incident_status, incident_id, signed_by, signed_at, current_version_id, form_family, form_key, module_payload, is_primary_form, parent_form_id, is_primary, parent_note_id, requires_countersign, countersigned_by, countersigned_at) FROM stdin;
7879abe4-3d62-4da8-9243-eb7a514074bb	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN_ASSESS	{"symptom_impact": {"pain": "SEVERE"}}	DRAFT	\N	30087d22-b9a9-469d-9ca8-4b56685773ca	2026-06-24 15:21:40.048	2026-06-24 15:21:40.048	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	01271980-0000-0000-0000-000005101977	\N	\N	1af2861b-49ca-4c53-90f7-751d67222978	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-24	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
9d0f1496-fc3e-4b95-a733-722d93174dc0	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN_ASSESS	{"symptom_impact": {"pain": "SEVERE"}}	DRAFT	\N	7f4f0719-9246-4596-96a9-f670c30299bd	2026-06-24 16:23:05.631364	2026-06-24 16:23:05.631364	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-24	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
f8e7aec1-a019-497e-ab51-50ef5c59fe10	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN_ASSESS	{}	DRAFT	\N	93a8111b-fffa-4af0-b71c-b6309657760e	2026-06-24 16:02:27.317786	2026-06-24 16:02:27.317786	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	01271980-0000-0000-0000-000005101977	\N	\N	8ea3481a-4dbd-4709-be11-bfbb4d4da12c	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-24	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
e3ebf064-66dd-40f2-92a9-5edf8fee4c72	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN_ASSESS	{}	DRAFT	\N	6357d7b5-afc4-452a-9c0b-eac6fe9aca65	2026-06-24 17:00:58.52175	2026-06-24 17:00:58.52175	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	01271980-0000-0000-0000-000005101977	\N	\N	8ea3481a-4dbd-4709-be11-bfbb4d4da12c	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
862e8e53-9060-4ae2-af44-afff8b097154	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN_ASSESS	{"symptom_impact": {"pain": "SEVERE"}}	DRAFT	\N	f6d4d397-b740-412f-b28c-f345c199aa37	2026-06-24 15:09:38.516876	2026-06-24 15:09:38.516876	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	01271980-0000-0000-0000-000005101977	\N	\N	f6774a7f-ef3c-4e29-b716-c3a9cc8c9012	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-24	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
97f0f7b2-dfd2-456a-8193-47aa421bd94b	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"issues": [{"poc": {"goals": ["Pain < 4/10"], "interventions": ["Administer morphine"], "orders_required": false}, "issue": "Uncontrolled pain", "severity": "SEVERE"}], "present": true, "severity": "SEVERE"}}}	DRAFT	\N	45ede8ce-d63d-405a-b9d7-bed0cd7388c3	2026-06-24 20:43:59.467657	2026-06-24 20:43:59.467657	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
4bff4ba5-c00c-4f9e-afe4-98e5c7f175b1	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"issues": [{"poc": {"goals": ["Pain < 4/10"], "interventions": ["Administer morphine"], "orders_required": false}, "issue": "Uncontrolled pain", "severity": "SEVERE"}], "present": true, "severity": "SEVERE"}}}	DRAFT	\N	d91c71a8-6890-470f-bd9c-28220499e927	2026-06-24 21:03:12.40589	2026-06-24 21:03:12.40589	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
790f4629-c251-4220-abdf-0876b9d3e610	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"issues": [{"poc": {"goals": ["Pain < 4/10"], "interventions": ["Administer morphine"], "orders_required": false}, "issue": "Uncontrolled pain", "severity": "SEVERE"}], "present": true, "severity": "SEVERE"}}}	DRAFT	\N	132bb95d-c6d3-4b69-8e72-45fb5983bce7	2026-06-24 21:44:41.52088	2026-06-24 21:44:41.52088	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
b1517c60-6825-4d10-a385-22d33e058c50	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"issues": [{"poc": {"goals": ["Pain < 4/10"], "interventions": ["Administer morphine"], "orders_required": false}, "issue": "Uncontrolled pain", "severity": "SEVERE"}], "present": true, "severity": "SEVERE"}}}	DRAFT	\N	305ba457-1a45-41e1-aff9-6cface81bacf	2026-06-24 22:40:24.919246	2026-06-24 22:40:24.919246	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
00e5b620-2546-4c70-bfa0-33eaf1a20bcb	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"issues": [{"poc": {"goals": ["Pain < 4/10"], "interventions": ["Administer morphine"], "orders_required": false}, "issue": "Uncontrolled pain", "severity": "SEVERE"}], "present": true, "severity": "SEVERE"}}}	DRAFT	\N	31affde6-71c8-43c8-a499-5847563bd383	2026-06-24 22:59:16.8015	2026-06-24 22:59:16.8015	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
738def69-e0dd-4426-85d2-46c3b5b1b561	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"issues": [{"poc": {"goals": ["Pain < 4/10"], "interventions": ["Administer morphine"], "orders_required": false}, "issue": "Uncontrolled pain", "severity": "SEVERE"}], "present": true, "severity": "SEVERE"}}}	DRAFT	\N	39450d07-d0c5-4a46-b698-9263bd3066d7	2026-06-24 23:13:19.640381	2026-06-24 23:13:19.640381	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
1f42ca93-5e25-4bf1-8822-b7a06cf1feee	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{}	DRAFT	\N	bd73bad3-b396-4c0f-a77a-4becc30a4b43	2026-06-24 23:18:05.193949	2026-06-24 23:18:05.193949	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
b00954fc-14c5-43cd-a331-66658d17a886	28b66dcb-3ff0-5868-b147-b24f63db74a6	LVN_ROUTINE	{}	DRAFT	\N	72ab4c07-b9b8-4474-b8e4-eb95959a2bf5	2026-06-24 23:33:12.269087	2026-06-24 23:33:12.269087	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	LVN_ROUTINE	VISIT	LVN	2026-06-25	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
b96d6e24-84a6-48d0-a1ec-6158c87f77eb	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"notes": "RN assessment visit", "assessment": {"pain": {"severity": "MILD"}}}	DRAFT	\N	f2fb2551-6b65-4929-a12f-f3caed459b87	2026-06-25 19:24:58.214471	2026-06-25 19:24:58.214471	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-26	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
cbc13298-ca80-4bf1-aa84-8136b02fab00	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"severity": "MODERATE"}}}	DRAFT	\N	11d26b9b-bd15-4ab5-b55d-99c49d8d72ab	2026-06-26 03:36:48.109304	2026-06-26 03:36:48.109304	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-26	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
67f6ac2e-1e6b-4a03-a7af-6c80279be394	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"assessment": {"pain": {"severity": "MODERATE"}}}	DRAFT	\N	bdac003f-500f-4891-ab6e-995573249758	2026-06-26 03:54:24.774069	2026-06-26 03:54:24.774069	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-26	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
6333dbb9-04e5-4064-aae1-a26ee9ec6a75	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{"note": "PRN visit. Patient stable. No issues identified.", "vitals": {"bp": "120/80", "resp": 16, "temp": 98.6, "pulse": 72}}	DRAFT	\N	4393dc50-b953-482e-a2eb-20e35af4a88a	2026-06-28 17:42:51.201799	2026-06-28 17:42:51.201799	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
8d198a2d-1620-4acf-99c2-f64660022e97	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{"note": "PRN visit. Patient stable. No issues identified.", "vitals": {"bp": "120/80", "resp": 16, "temp": 98.6, "pulse": 72}}	DRAFT	\N	55369da7-11d7-4432-a003-d9c040fa84cb	2026-06-28 18:02:24.684476	2026-06-28 18:02:24.684476	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
28be0c20-149e-4de5-b0e0-f5cbcc449e1b	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{"note": "Patient in distress. Increased pain and difficulty breathing."}	DRAFT	\N	11429b98-e17c-4146-b8c3-ce3fb1499fd2	2026-06-28 18:05:00.66809	2026-06-28 18:05:00.66809	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
5a0897a5-cd08-47d1-9246-ea8e86999bdb	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{"note": "Patient in distress. Increased pain and difficulty breathing."}	DRAFT	\N	26c25de7-2748-4a6f-97b2-29a508b72a99	2026-06-28 18:13:50.560197	2026-06-28 18:13:50.560197	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
bfa7c066-9dc9-48b6-9f33-5186e7419b24	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{"note": "Patient in distress. Increased pain and difficulty breathing."}	DRAFT	\N	c10bf95a-94d1-4e9b-9800-cf408c6565e9	2026-06-28 18:19:50.395385	2026-06-28 18:19:50.395385	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
70751c0b-6318-4ce3-9b1b-d05c77a083cc	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{"note": "Patient in distress. Increased pain and difficulty breathing."}	DRAFT	\N	0c3d0a13-e623-4f24-9fe5-79b69bfcd105	2026-06-28 18:24:43.066238	2026-06-28 18:24:43.066238	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
56cc3beb-8fce-42f5-8c87-9d3a5869c955	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ROUTINE	{"note": "Patient in distress. Increased pain and difficulty breathing."}	DRAFT	\N	45287a1c-94cd-4d0a-8e3f-dc854a29e06c	2026-06-28 18:31:20.646844	2026-06-28 18:31:20.646844	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ROUTINE	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
a8de4983-b448-4556-af72-65c5543ef055	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"note": "Patient in distress. Increased pain and difficulty breathing."}	DRAFT	\N	d195b1cc-a2d2-4883-beff-613f01227af2	2026-06-28 18:56:47.717457	2026-06-28 18:56:47.717457	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
5f1040c5-192b-4965-865c-cfe72f3b7ecb	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"note": "Initial skilled nursing visit. Patient reports pain 8/10. Caregiver stressed.", "vitals": {"bp": "130/80", "resp": 18, "temp": 98.6, "pulse": 78}, "assessment": {"spiritual": "Requested prayer support", "pain_score": 8, "psychosocial": "Caregiver overwhelmed"}}	DRAFT	\N	1e7f5339-4a20-43cd-bb5a-69f0ed7191d9	2026-06-28 19:15:09.974335	2026-06-28 19:15:09.974335	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	VISIT_CREATE	RN_ASSESS	VISIT	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
56e33c56-34dd-4ce4-9183-7d2564460ab7	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN_ASSESS	{"note": "Initial skilled nursing visit. Patient reports pain 8/10. Caregiver stressed.", "vitals": {"bp": "130/80", "resp": 18, "temp": 98.6, "pulse": 78}, "assessment": {"spiritual": "Requested prayer support", "pain_score": 8, "psychosocial": "Caregiver overwhelmed"}}	DRAFT	\N	81b9e6ca-0a9b-4496-ba7d-a84aa8607797	2026-06-29 03:57:45.174976	2026-06-29 03:57:45.174976	28b66dcb-3ff0-5868-b147-b24f63db74a6	\N	01271980-0000-0000-0000-000005101977	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	\N	\N	\N	\N	RN	2026-06-29	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	CLINICAL	\N	\N	t	\N	t	\N	f	\N	\N
\.


--
-- Data for Name: communications_logs; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.communications_logs (id, tenant_id, patient_id, channel, direction, subject, body, status, external_reference, sent_at, created_at, created_by, event_type, focus_area, event_time, summary, details, acknowledged_by, acknowledged_at, verified_by, verified_at, resolved_by, resolved_at) FROM stdin;
129a1683-e134-4b21-a5fc-cc48d77761b8	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 15:14:22.863784	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
d2c9df3f-1e29-489a-9b2f-f6fabc871edb	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 15:16:24.902245	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
f37fb65e-3bc4-4e15-abea-b6479c5d67c1	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 15:25:28.883934	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
19252276-47ed-4dfa-bf64-9880510148dd	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 15:27:38.031624	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
5828d87b-7459-45f8-a1e1-b020614e1064	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 16:02:26.856243	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
b5f6e2e9-1a86-473b-9080-ae3f3a88329c	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 16:11:20.640656	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
183faa08-4b17-4cd5-a461-523b795b22dc	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 16:21:44.913196	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
513e4ab4-0930-421d-bf50-f3e97ea0c92f	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RECEIVED	\N	\N	2026-06-19 16:25:00.186286	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"trigger_type": "CHANGE_OF_CONDITION", "reports": [{"source_type": "CHHA", "method": "IN_PERSON_OBSERVATION"}, {"source_type": "PCG", "method": "PHONE_CALL"}, {"source_type": "LVN", "action": "ESCALATED_TO_RN"}], "required_actions": ["VERIFY", "INVESTIGATE", "RN_VISIT_REQUIRED"]}	\N	\N	\N	\N	\N	\N
a478234f-ce9d-4325-a648-a0d04c7cf064	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RESOLVED	\N	\N	2026-06-19 16:33:16.344006	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"workflow_notes": [{"status": "RESOLVED", "actor_id": "28b66dcb-3ff0-5868-b147-b24f63db74a6", "note": "RN follow-up completed and patient condition addressed", "recorded_at": "2026-06-20T00:25:13.472925"}]}	28b66dcb-3ff0-5868-b147-b24f63db74a6	2026-06-20 00:20:41.394724-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	2026-06-20 00:23:41.531555-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	2026-06-20 00:25:13.472912-07
200116ec-1c68-4730-a0bb-6f6ad110a59b	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	\N	\N	\N	\N	RESOLVED	\N	\N	2026-06-19 16:28:57.079362	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	Phone Call	Neurological/Mental	2026-06-19 12:30:00	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	{"workflow_notes": [{"status": "RESOLVED", "actor_id": "28b66dcb-3ff0-5868-b147-b24f63db74a6", "note": "RN acknowledged and will assess immediately", "recorded_at": "2026-06-20T00:56:28.886787"}]}	28b66dcb-3ff0-5868-b147-b24f63db74a6	2026-06-20 00:55:02.814298-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	2026-06-20 00:55:50.680124-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	2026-06-20 00:56:28.886773-07
\.


--
-- Data for Name: continuous_care_events; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.continuous_care_events (id, patient_id, start_date, end_date, reason, tenant_id, visit_id, service_level, status, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: diagnoses; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.diagnoses (id, patient_id, diagnosis_name, onset_date, infection_source, created_by, created_at) FROM stdin;
e0a52b77-c9c9-42b1-ae86-dbd645dfe19c	fa32ac63-40b1-40d7-a261-3909bad67733	UTI	2026-06-26 23:26:11.823299	ACQUIRED_UNDER_SERVICE	\N	\N
cf2b2024-efd8-46d9-ac63-b535e4d0fdb0	58f1664a-1cea-49c9-9e59-96e2d6e744f4	Pneumonia	2026-06-26 23:33:20.169811	ACQUIRED_UNDER_SERVICE	\N	\N
\.


--
-- Data for Name: diagnosis_discrepancies; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.diagnosis_discrepancies (id, patient_id, referral_primary, rn_primary, cti_primary, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: diagnosis_reconciliations; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.diagnosis_reconciliations (id, discrepancy_id, resolution_choice, narrative, attested_by_account_id, attested_at) FROM stdin;
\.


--
-- Data for Name: diagnosis_sources; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.diagnosis_sources (id, patient_id, source, dx_type, icd_code, description, documented_by_account_id, documented_at, is_active) FROM stdin;
\.


--
-- Data for Name: discharge_reasons; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.discharge_reasons (code, label, cms_category, active, created_at, updated_at) FROM stdin;
DEATH	Death	DEATH	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
HOSPITALIZED	Hospitalized	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
TRANSFER_TO_ANOTHER_HOSPICE	Transferred to Another Hospice	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
TRANSFER_TO_SNF	Transfer to Skilled Nursing Facility	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
TRANSFER_TO_HOSPITAL	Transfer to Hospital	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
TRANSFER_TO_REHAB	Transfer to Rehab / Outpatient Rehab Facility	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
TRANSFER_TO_HOME_HEALTH	Transferred to Home Health	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
TRANSFER_TO_PALLIATIVE_CARE	Transferred to Palliative Care	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
REFERRED_BACK_TO_PCP	Referred Back to Primary Care Physician	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
MOVED_OUT_OF_AREA	Moved Out of Service Area	TRANSFER	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
PROGNOSIS_EXTENDED	Prognosis Extended	NO_LONGER_TERMINAL	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
STATUS_IMPROVED	Status Improved	NO_LONGER_TERMINAL	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
SYMPTOMS_MANAGED	Symptoms Managed	NO_LONGER_TERMINAL	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
REVOCATION_OF_HOSPICE	Revocation of Hospice	REVOCATION	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
DECLINED_FURTHER_SERVICES	Declined Further Services	REVOCATION	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
PATIENT_REFUSED_SERVICE	Patient Refused Services	REVOCATION	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
CHANGE_IN_PAYER	Change in Payer	REVOCATION	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
DISCHARGED_WITH_CAUSE	Discharged With Cause	DISCHARGE_FOR_CAUSE	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
NON_COMPLIANT_WITH_POC	Non-Compliant with Treatment / Plan of Care	DISCHARGE_FOR_CAUSE	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
UNSAFE_ENVIRONMENT_FOR_STAFF	Unsafe Environment for Staff	DISCHARGE_FOR_CAUSE	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
UNABLE_TO_MEET_CARE_NEEDS	Unable to Meet Patient / Family Care Needs	DISCHARGE_FOR_CAUSE	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
ADMINISTRATIVE_DISCHARGE	Administrative Discharge	DISCHARGE_FOR_CAUSE	t	2026-06-04 19:43:47.033461-07	2026-06-04 19:43:47.033461-07
\.


--
-- Data for Name: discharges; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.discharges (id, patient_id, discharge_reason_code, cms_category, status, effective_at, recorded_at, recorded_by_user_id, transfer_destination_type, transfer_destination_name, transfer_destination_notes, physician_discharge_order_id, supporting_clinical_note_id, documentation_note_id, remediation_attempts_documented, patient_notified, medical_director_approval, revocation_statement_signed, initiated_by, death_documentation_present, notes) FROM stdin;
\.


--
-- Data for Name: document_idg_resolution; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.document_idg_resolution (document_id, tenant_id, resolution_status, resolved_by, resolved_at, resolution_note, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: document_notifications; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.document_notifications (id, tenant_id, document_id, notification_id, status, created_at, created_by, recipient_role, recipient_user_id, notified_at, acknowledged_at, reminder_count, last_reminder_at, resolution_status, resolution_note, resolved_at, resolved_by) FROM stdin;
\.


--
-- Data for Name: document_records; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.document_records (id, created_at, updated_at, created_by, tenant_id, patient_id, document_type, source, file_name, file_path, extracted_values, document_text, is_flagged, flag_tier, matched_rule_ids, uploaded_at, uploaded_by) FROM stdin;
\.


--
-- Data for Name: drug_aliases; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.drug_aliases (alias_text, canonical_text, created_at, updated_at, created_by, id) FROM stdin;
\.


--
-- Data for Name: dx_primary_policies; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.dx_primary_policies (id, diagnosis_code, diagnosis_name, allowed_primary, rationale, active, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: dx_primary_policy; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.dx_primary_policy (id, tenant_id, code_pattern, pattern_type, allow_primary, allow_secondary, reason, created_at) FROM stdin;
4c6aacaa-09ac-4188-a270-99ab50877841	\N	F%	LIKE	f	t	Mental/behavioral codes not allowed as hospice primary dx	2026-06-04 19:48:42.864857-07
6116a9f8-54d8-4389-89bb-e8558610e92f	\N	R%	LIKE	f	t	Signs/symptoms not allowed as hospice primary dx	2026-06-04 19:48:42.864857-07
79ef906b-cbe3-4671-9278-39b05ae6e7a6	\N	V%	LIKE	f	t	External cause codes not allowed as hospice primary dx	2026-06-04 19:48:42.864857-07
c64bb617-ddb3-4c4a-9292-ffcdda98da3c	\N	W%	LIKE	f	t	External cause codes not allowed as hospice primary dx	2026-06-04 19:48:42.864857-07
61e430eb-92b5-472b-bd9e-13ced1a6578e	\N	X%	LIKE	f	t	External cause codes not allowed as hospice primary dx	2026-06-04 19:48:42.864857-07
22ca2dd4-1c12-4244-b432-43f6a504acfe	\N	Y%	LIKE	f	t	External cause codes not allowed as hospice primary dx	2026-06-04 19:48:42.864857-07
22220311-9cd9-4fbb-b92c-1deea006e16d	\N	Z%	LIKE	f	t	Encounter/status Z codes not allowed as hospice primary dx	2026-06-04 19:48:42.864857-07
\.


--
-- Data for Name: eligibility_assessments; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.eligibility_assessments (id, patient_id, ruleset_id, ruleset_version, eligible, score, observations_snapshot, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: eligibility_decisions; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.eligibility_decisions (id, patient_id, decision, lcd_id, mac, mac_type, lcd_effective_date, decision_timestamp, config_hash, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: eligibility_rulesets; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.eligibility_rulesets (id, ruleset_id, ruleset_version, condition, jurisdiction, ruleset_json, is_active, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: external_substances; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.external_substances (id, tenant_id, patient_id, substance_name, category, notes, recorded_at, created_at, created_by, name, substance_type, initiated_by, ordered_by_provider, purpose, known_interactions, clinician_reviewed, clinician_action, clinician_notes, coverage_intent, financial_responsibility, reviewed_at, reviewed_by, updated_at) FROM stdin;
\.


--
-- Data for Name: f2f_encounters; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.f2f_encounters (id, patient_id, benefit_period_id, encounter_date, performed_by_role, performed_by_user_id, summary, status, finalized_at, created_at, updated_at, created_by, pps_score_previous, pps_score_current, weight_loss_lbs, adl_dependency_level, is_bedbound, oral_intake_decline, dysphagia, hospitalizations_30d, oxygen_lpm_previous, oxygen_lpm_current, primary_diagnosis, secondary_conditions, clinical_decline_summary, kps_score, fast_score, nyha_class, adl_dependency_count, attested_at, attesting_provider_user_id) FROM stdin;
06f3d1aa-6c5c-4f47-8ab0-3f77120e2c88	1af2861b-49ca-4c53-90f7-751d67222978	3ac2b8e3-676b-48fa-afeb-ee3ab7bd223c	2026-06-22	MD	28b66dcb-3ff0-5868-b147-b24f63db74a6	Face-to-face encounter completed for continued hospice eligibility. Patient demonstrates progressive decline, worsening functional dependence, and terminal disease trajectory consistent with prognosis of six months or less.	DRAFT	\N	2026-06-22 22:29:35.557694	2026-06-22 22:29:35.557696	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: form_modules; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.form_modules (id, name, module_key, created_at, description, is_active, updated_at, deleted_at) FROM stdin;
080661e6-f740-48f0-83ec-f3de6ef581e9	General Assessment	general_assessment	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
25e021fb-d9c2-4c34-a66d-e4ec7277c0b2	Neurological / Mental	neuro_mental	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
eaa3b111-96bc-4790-a1a7-9cccc28cdced	Cardiovascular	cardiovascular	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
372dc165-457d-4069-af77-b17954a59af3	Respiratory	respiratory	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
29e93979-6e1d-4f75-a5b0-50a97efdc0d9	Gastrointestinal	gi	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
8d2d927f-1101-4b87-83d8-b0d58bde7e1c	Genitourinary	gu	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
94eb2f0e-2bfd-45fe-a705-794881253331	Endocrine	endocrine	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
7bd59e7f-dbef-4191-b0b0-41608cdd142d	Musculoskeletal	musculoskeletal	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
26fa63e0-7d53-4b84-b5f8-da23288a0f29	Skin / Integumentary	skin	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
5de11dfd-0637-4577-93aa-8477467306b9	Pain Assessment (PAINAD)	pain_assessment	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
dfc7fd41-2ced-43ae-a397-39f99c8ae677	Infection / Immunological	infection	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
bdc899e2-4c3b-4701-99ea-b6110eb4edad	Nutrition	nutrition	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
fe57b15b-404f-4cac-82ad-b0e09393a54d	Vitals	vitals	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
c860fbaf-b856-4e1f-b037-4ff75e43fe66	Medication Review	med_review	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
ec79ab9d-6a8e-45c5-b6c5-5dfd1d7dead7	Fall Risk Assessment	fall_risk	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
b89720f5-9256-43bf-b41c-99ed6eea866f	Safety Assessment	safety	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
eb3685c2-070f-4043-ace9-66ac0356295c	Oxygen Therapy	oxygen_therapy	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
75ee10c3-a009-4ae5-bc0e-cb5b9738e915	Symptom Impact (HOPE)	symptom_hope	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
ab5457af-247c-49f8-8cb5-cb7147aeb508	Psychosocial Assessment	psychosocial	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
ffc5ac6b-fbcc-4dfb-bc49-d1a0c18d357e	Caregiver Support	caregiver_support	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
64175f01-1b4d-4c90-ba90-9baed3ababf7	Advance Care Planning	advance_planning	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
411bf3b8-2069-4f15-806b-0924b83d5b19	Bereavement Risk	bereavement	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
1860cd50-0c12-4c14-9c16-bf9c10529974	Spiritual Assessment	spiritual_assessment	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
9e64c27c-dfab-4b93-9923-4074c5dfc4bd	Spiritual Distress	spiritual_distress	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
a9b7c6e9-4354-476f-909e-0a6008e816fc	ADL Assessment	adl_assessment	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
c3910d21-6e89-40f4-8707-c70ec3ff23d7	Personal Care	personal_care	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
0f1a7358-cb91-4131-a736-217351b7b635	Mobility Assistance	mobility	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
b5a2c92f-2233-4f73-8cf4-19d416fd90db	Visit Summary	visit_summary	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
9b73eba0-9ebf-4ad5-8c53-56df7bed1c4c	Plan of Care	plan_of_care	2026-06-23 21:54:28.675265-07	\N	t	\N	\N
911e0b8b-3cdf-43ed-8074-e297e5366cd0	New Clinical Section	new_section	2026-06-23 22:03:14.935418-07	\N	t	\N	\N
e6abfad4-aa38-4a0d-86a3-9458467ec772	Supervisory Summary	supervisory_summary	2026-06-23 23:25:04.68177-07	\N	t	\N	\N
8765c089-61fb-4aff-adcf-55d6d3a9ca45	Neurological	neurological	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
3d9deb31-0d4a-4d76-bd99-e13f83ac0a5a	Gastrointestinal	gastrointestinal	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
da3e4a87-f4a2-43c5-971c-3d0fd4b7f4c9	Genitourinary	genitourinary	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
170643bd-da47-4b16-ab77-d6a9b9dd530c	Skin/Integumentary	integumentary	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
f3a8b490-ff61-4b9f-b75d-721718c920be	Infection Control	infection_control	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
6552038d-f946-44ff-bbc3-8f65cf4a10f3	ADL Assessment	adl	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
30397137-e708-41f6-83e9-16c458636e4d	Environment Safety	environment_safety	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
85ee10ec-30cd-4fa2-844f-327afe81924d	Symptom Follow Up	symptom_follow_up	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
090cba48-fd07-4297-b37c-9943ddc491fb	Teaching/Education	teaching	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
82b5f7ff-b90c-44ea-b966-e117efafeec4	Narrative	narrative	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
73b5bef2-a7a6-4483-a435-22ec070e9e2a	Spiritual	spiritual	2026-06-23 23:37:12.677335-07	\N	t	\N	\N
\.


--
-- Data for Name: form_package_modules; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.form_package_modules (id, form_registry_id, module_id, display_order, is_required, is_active, created_at, updated_at, deleted_at) FROM stdin;
1e864756-359c-479b-b6b8-ef6eded50bd0	d7ccde90-44bb-4334-a247-1e39fe33a3df	080661e6-f740-48f0-83ec-f3de6ef581e9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
0889e7e9-bdfc-444b-944e-e0462cc4066e	d7ccde90-44bb-4334-a247-1e39fe33a3df	25e021fb-d9c2-4c34-a66d-e4ec7277c0b2	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
cce3d22e-2748-4917-94af-7b3cf0d9a2d1	d7ccde90-44bb-4334-a247-1e39fe33a3df	eaa3b111-96bc-4790-a1a7-9cccc28cdced	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
dbf18b93-87c0-4672-9ee1-dc55c1c060b0	d7ccde90-44bb-4334-a247-1e39fe33a3df	372dc165-457d-4069-af77-b17954a59af3	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
ff11f9d4-b7b2-40b5-a360-bb87fe4947de	d7ccde90-44bb-4334-a247-1e39fe33a3df	29e93979-6e1d-4f75-a5b0-50a97efdc0d9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
d5fac3b1-15a0-4fa3-93e1-19f0516972bf	d7ccde90-44bb-4334-a247-1e39fe33a3df	8d2d927f-1101-4b87-83d8-b0d58bde7e1c	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
a9db08e1-0015-484b-9de2-734b7ac813d6	d7ccde90-44bb-4334-a247-1e39fe33a3df	94eb2f0e-2bfd-45fe-a705-794881253331	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
b099b1b1-192d-42e4-9a71-70579daaf24f	d7ccde90-44bb-4334-a247-1e39fe33a3df	7bd59e7f-dbef-4191-b0b0-41608cdd142d	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
5c11a14d-1c1c-446e-bcf1-c6a506c0a975	d7ccde90-44bb-4334-a247-1e39fe33a3df	26fa63e0-7d53-4b84-b5f8-da23288a0f29	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
6f8a440c-9ee2-4628-808f-84f5385c6225	d7ccde90-44bb-4334-a247-1e39fe33a3df	5de11dfd-0637-4577-93aa-8477467306b9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
c1dfa04c-40ab-4b14-a003-bea3cae9d2c3	d7ccde90-44bb-4334-a247-1e39fe33a3df	dfc7fd41-2ced-43ae-a397-39f99c8ae677	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
95e06ad3-54b0-44e6-9f70-07291608d977	d7ccde90-44bb-4334-a247-1e39fe33a3df	bdc899e2-4c3b-4701-99ea-b6110eb4edad	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
6239f71b-7413-4271-bc3c-9c0b3f19a599	d7ccde90-44bb-4334-a247-1e39fe33a3df	fe57b15b-404f-4cac-82ad-b0e09393a54d	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
650dd65e-124b-4d42-b57e-06ad02cba23c	d7ccde90-44bb-4334-a247-1e39fe33a3df	ec79ab9d-6a8e-45c5-b6c5-5dfd1d7dead7	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
c296c646-205e-465d-86a4-a5506dade555	d7ccde90-44bb-4334-a247-1e39fe33a3df	b89720f5-9256-43bf-b41c-99ed6eea866f	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
af956104-706f-405b-9550-27b01786eeb0	d7ccde90-44bb-4334-a247-1e39fe33a3df	eb3685c2-070f-4043-ace9-66ac0356295c	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
fd6726ca-68bd-414e-a830-95faab4651d5	d7ccde90-44bb-4334-a247-1e39fe33a3df	75ee10c3-a009-4ae5-bc0e-cb5b9738e915	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
ecc7ceed-d944-4e54-96ba-ba03fca5d60f	d7ccde90-44bb-4334-a247-1e39fe33a3df	b5a2c92f-2233-4f73-8cf4-19d416fd90db	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
c3d875f3-78e1-44d8-bd8b-d4daae605794	d7ccde90-44bb-4334-a247-1e39fe33a3df	9b73eba0-9ebf-4ad5-8c53-56df7bed1c4c	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
d4b9a180-47e2-4b16-abb5-86092fa0528c	8e15f4bf-9960-4275-a856-b12c39c2a0b8	080661e6-f740-48f0-83ec-f3de6ef581e9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
1342987b-d814-4c5b-a928-e5ac973182f8	8e15f4bf-9960-4275-a856-b12c39c2a0b8	eaa3b111-96bc-4790-a1a7-9cccc28cdced	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
6807720b-cb98-4628-83b5-2064f65faa06	8e15f4bf-9960-4275-a856-b12c39c2a0b8	372dc165-457d-4069-af77-b17954a59af3	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
a88267f0-7af8-4071-9c0c-2dc48d757aae	8e15f4bf-9960-4275-a856-b12c39c2a0b8	5de11dfd-0637-4577-93aa-8477467306b9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
8ab0bccb-afa9-473d-bfc2-408901f48a25	8e15f4bf-9960-4275-a856-b12c39c2a0b8	fe57b15b-404f-4cac-82ad-b0e09393a54d	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
47767353-7710-4980-9c93-feeb70c3af85	8e15f4bf-9960-4275-a856-b12c39c2a0b8	c860fbaf-b856-4e1f-b037-4ff75e43fe66	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
0831e502-0e8f-4f0c-be8a-84f37c9315f1	8e15f4bf-9960-4275-a856-b12c39c2a0b8	b5a2c92f-2233-4f73-8cf4-19d416fd90db	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
39730cbe-d9aa-4116-95b1-0f46d7940873	770a64a7-21c6-4cf8-9252-cd7a5d9fbd6e	ab5457af-247c-49f8-8cb5-cb7147aeb508	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
a2d4bfcb-02ba-4577-9afd-bd3d4ff54d9a	770a64a7-21c6-4cf8-9252-cd7a5d9fbd6e	ffc5ac6b-fbcc-4dfb-bc49-d1a0c18d357e	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
95cf801b-d4ba-4c8d-9b18-0c6c656fd3f3	770a64a7-21c6-4cf8-9252-cd7a5d9fbd6e	64175f01-1b4d-4c90-ba90-9baed3ababf7	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
3008533a-9f13-45d2-ae8f-1b69d12ba200	770a64a7-21c6-4cf8-9252-cd7a5d9fbd6e	411bf3b8-2069-4f15-806b-0924b83d5b19	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
177f2293-3b03-4399-a890-f2f83c65d796	770a64a7-21c6-4cf8-9252-cd7a5d9fbd6e	b5a2c92f-2233-4f73-8cf4-19d416fd90db	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
64820d85-6929-4ab2-8170-fe0230322e18	ddc24e72-e1a8-4045-8700-0d263a684273	1860cd50-0c12-4c14-9c16-bf9c10529974	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
9b32adbb-a039-4df6-a10d-82fc825e8286	ddc24e72-e1a8-4045-8700-0d263a684273	9e64c27c-dfab-4b93-9923-4074c5dfc4bd	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
caa5d6ef-8b6d-45c1-b5b6-885e9a1ef1ff	ddc24e72-e1a8-4045-8700-0d263a684273	b5a2c92f-2233-4f73-8cf4-19d416fd90db	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
887e4b88-63b8-4f5d-954c-2a90819b5a03	b133ecb9-907a-49f1-b0af-e40381080e9d	26fa63e0-7d53-4b84-b5f8-da23288a0f29	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
096d8084-ccc4-4ec5-9f21-fbd1b8913e1a	b133ecb9-907a-49f1-b0af-e40381080e9d	bdc899e2-4c3b-4701-99ea-b6110eb4edad	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
6bd2df7b-ca5d-4a42-a94c-cfb491b1bf2f	b133ecb9-907a-49f1-b0af-e40381080e9d	a9b7c6e9-4354-476f-909e-0a6008e816fc	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
67b2bc14-7d87-41e3-bd2d-226c9cff61e0	b133ecb9-907a-49f1-b0af-e40381080e9d	c3910d21-6e89-40f4-8707-c70ec3ff23d7	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
34645140-bcc7-4575-897f-f3ec48287d02	b133ecb9-907a-49f1-b0af-e40381080e9d	0f1a7358-cb91-4131-a736-217351b7b635	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
aff05696-e8de-4c5b-b7f9-81d9062cc4c8	b133ecb9-907a-49f1-b0af-e40381080e9d	b5a2c92f-2233-4f73-8cf4-19d416fd90db	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
3a3f24d7-ec28-4b95-8d57-4f5d1b51e35e	d7ccde90-44bb-4334-a247-1e39fe33a3df	911e0b8b-3cdf-43ed-8074-e297e5366cd0	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
f38f68bd-0190-49ff-9c37-bade18c0418e	b28a07f6-187e-446b-90f8-1162c449ef56	080661e6-f740-48f0-83ec-f3de6ef581e9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
19f799b8-1b70-463d-8a87-30d507b481e8	b28a07f6-187e-446b-90f8-1162c449ef56	eaa3b111-96bc-4790-a1a7-9cccc28cdced	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
04324160-dd00-46c6-ac7a-5e6a3e9cd6fb	b28a07f6-187e-446b-90f8-1162c449ef56	372dc165-457d-4069-af77-b17954a59af3	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
4c319136-fa48-452b-ad9f-3f1f933f7140	b28a07f6-187e-446b-90f8-1162c449ef56	5de11dfd-0637-4577-93aa-8477467306b9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
94ccb521-6694-4527-afb8-637d92d83128	b28a07f6-187e-446b-90f8-1162c449ef56	fe57b15b-404f-4cac-82ad-b0e09393a54d	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
d3a8abf5-96aa-4de6-8f27-f75271bfa2ae	b28a07f6-187e-446b-90f8-1162c449ef56	c860fbaf-b856-4e1f-b037-4ff75e43fe66	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
7e72233d-061b-45c5-b326-8ffab737c5d6	b28a07f6-187e-446b-90f8-1162c449ef56	b5a2c92f-2233-4f73-8cf4-19d416fd90db	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
aac5f018-72f9-4e92-abce-9f602fd96e89	b28a07f6-187e-446b-90f8-1162c449ef56	9b73eba0-9ebf-4ad5-8c53-56df7bed1c4c	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
95ce4287-3490-485a-999f-5e549c42eb9b	b28a07f6-187e-446b-90f8-1162c449ef56	e6abfad4-aa38-4a0d-86a3-9458467ec772	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
3dd3813e-130e-4e69-a184-adcadd5b6e31	b28a07f6-187e-446b-90f8-1162c449ef56	94eb2f0e-2bfd-45fe-a705-794881253331	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
aabafffd-cfa5-4c4f-8052-29f007df4b5a	b28a07f6-187e-446b-90f8-1162c449ef56	7bd59e7f-dbef-4191-b0b0-41608cdd142d	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
45f7741f-a321-4369-97fe-f0e809406299	b28a07f6-187e-446b-90f8-1162c449ef56	bdc899e2-4c3b-4701-99ea-b6110eb4edad	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
88615fb6-cb6e-4af9-a26f-b7cbd6422d30	b28a07f6-187e-446b-90f8-1162c449ef56	ec79ab9d-6a8e-45c5-b6c5-5dfd1d7dead7	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
9f9f6725-f2c6-45fe-95e6-bd087f0bba1b	b28a07f6-187e-446b-90f8-1162c449ef56	ab5457af-247c-49f8-8cb5-cb7147aeb508	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
65538854-9e17-4ed2-8167-ccf53d11d885	b28a07f6-187e-446b-90f8-1162c449ef56	411bf3b8-2069-4f15-806b-0924b83d5b19	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
5000f6be-2c43-436c-b055-2e3f4ea4db80	b28a07f6-187e-446b-90f8-1162c449ef56	8765c089-61fb-4aff-adcf-55d6d3a9ca45	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
55325322-deb7-428f-866d-2b6ed9a9f783	b28a07f6-187e-446b-90f8-1162c449ef56	3d9deb31-0d4a-4d76-bd99-e13f83ac0a5a	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
e1842b2a-ecf1-4bf5-91fb-bcea7e7818e4	b28a07f6-187e-446b-90f8-1162c449ef56	da3e4a87-f4a2-43c5-971c-3d0fd4b7f4c9	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
07b76c4f-c45a-409b-aeca-788aa39d3221	b28a07f6-187e-446b-90f8-1162c449ef56	170643bd-da47-4b16-ab77-d6a9b9dd530c	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
cd6917c6-d3bd-4812-88a2-8484f3c26fab	b28a07f6-187e-446b-90f8-1162c449ef56	f3a8b490-ff61-4b9f-b75d-721718c920be	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
91dba078-25f0-4bf4-a27c-13d736e47c90	b28a07f6-187e-446b-90f8-1162c449ef56	6552038d-f946-44ff-bbc3-8f65cf4a10f3	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
5dcb8d0a-034e-4369-8d2e-1b0bca2f73b8	b28a07f6-187e-446b-90f8-1162c449ef56	30397137-e708-41f6-83e9-16c458636e4d	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
6443fabb-9e9d-4f80-b769-f8a61be6a1e6	b28a07f6-187e-446b-90f8-1162c449ef56	85ee10ec-30cd-4fa2-844f-327afe81924d	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
71e5ebef-def4-4a95-9515-3ee96c79e30b	b28a07f6-187e-446b-90f8-1162c449ef56	090cba48-fd07-4297-b37c-9943ddc491fb	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
05bbb8a1-2cdb-4a7f-b866-7dd25fcb7927	b28a07f6-187e-446b-90f8-1162c449ef56	82b5f7ff-b90c-44ea-b966-e117efafeec4	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
cf1ea369-96b7-4f19-8fdb-57b18aabd948	b28a07f6-187e-446b-90f8-1162c449ef56	73b5bef2-a7a6-4483-a435-22ec070e9e2a	\N	f	t	2026-06-25 18:28:34.19218-07	\N	\N
\.


--
-- Data for Name: form_registry; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.form_registry (id, form_type, form_family, discipline, level_of_care, form_key, is_primary, is_active, created_at, updated_at, deleted_at, attached_forms, version) FROM stdin;
770a64a7-21c6-4cf8-9252-cd7a5d9fbd6e	MSW Psychosocial Visit	PSYCHOSOCIAL	MSW	ROUTINE	MSW_ROUTINE	t	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
ddc24e72-e1a8-4045-8700-0d263a684273	Chaplain Visit	SPIRITUAL	CHAPLAIN	ROUTINE	CHAPLAIN_ROUTINE	t	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
b133ecb9-907a-49f1-b0af-e40381080e9d	Home Health Aide Visit	SUPPORT	AIDE	ROUTINE	HHA_VISIT	t	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
d7ccde90-44bb-4334-a247-1e39fe33a3df	ASSESS	CLINICAL	RN	ROUTINE	RN_ASSESS	t	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
b28a07f6-187e-446b-90f8-1162c449ef56	ROUTINE_VISIT	CLINICAL	RN	ROUTINE	RN_ROUTINE	f	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
2b61324b-a042-4f2a-a3f3-2aa831044095	SUPV_VISIT_ONLY	CLINICAL	RN	ROUTINE	RN_SUPV	f	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
8e15f4bf-9960-4275-a856-b12c39c2a0b8	ROUTINE_VISIT	CLINICAL	LVN	ROUTINE	LVN_ROUTINE	t	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
96281fc9-5313-45f3-ab91-6b129996dbd6	SHORT_FORM	CLINICAL	LVN	ROUTINE	LVN_SHORT	f	t	2026-06-23 21:58:17.392723-07	\N	\N	\N	1
\.


--
-- Data for Name: forms; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.forms (id, visit_id, form_registry_id, is_primary, content, created_at, updated_at, form_key, form_family, form_type, status, finalized_at, finalized_by, tenant_id) FROM stdin;
\.


--
-- Data for Name: gip_periods; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.gip_periods (id, patient_id, start_date, end_date, reason, tenant_id, visit_id, service_level, status, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: guardrail_policies; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.guardrail_policies (id, tenant_id, policy_key, value, description, value_type, is_active, effective_date, created_at, updated_at, created_by, updated_by) FROM stdin;
9bd6137f-ef46-45d3-9b20-e756e862c5ff	01271980-0000-0000-0000-000005101977	MIN_NARRATIVE_LENGTH	200	Minimum characters required for clinical eligibility narrative	INTEGER	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
790fa7a2-5c4d-43ce-b829-61f5ceba680f	01271980-0000-0000-0000-000005101977	REQUIRE_MEASURABLE_DECLINE	true	Require documented measurable evidence of decline for admission support	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
93fd387b-fbd2-42e8-9896-c0f8e445b98f	01271980-0000-0000-0000-000005101977	ENFORCE_LCD_RULES	true	Apply LCD/documentation consistency rules during admission guardrail evaluation	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
84a20de1-5a6d-47e3-bc73-23e13acbabea	01271980-0000-0000-0000-000005101977	GUARDRAIL_MODE	GUIDANCE	Guardrail enforcement mode: OFF, SILENT, GUIDANCE, STRICT	STRING	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
638e5c6d-c702-4c50-bef3-873e636b1c47	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	MIN_NARRATIVE_LENGTH	200	Minimum characters required for clinical eligibility narrative	INTEGER	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
f825e6ac-a440-42a8-9e5d-82aa5db6a34f	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	REQUIRE_MEASURABLE_DECLINE	true	Require documented measurable evidence of decline for admission support	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
e84ebd68-7d85-4552-94fe-5a022fe0e348	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	ENFORCE_LCD_RULES	true	Apply LCD/documentation consistency rules during admission guardrail evaluation	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
aa6898d1-1e41-47e9-b5c8-ab4c722306fd	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	GUARDRAIL_MODE	GUIDANCE	Guardrail enforcement mode: OFF, SILENT, GUIDANCE, STRICT	STRING	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
23f39058-a46f-418a-a16b-7364df27cd48	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	MIN_NARRATIVE_LENGTH	200	Minimum characters required for clinical eligibility narrative	INTEGER	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
e4a66683-1d6c-4a4b-8e96-2bf032c801ef	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	REQUIRE_MEASURABLE_DECLINE	true	Require documented measurable evidence of decline for admission support	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
80378a7b-e1b5-4989-b795-cdbeb8b97230	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	ENFORCE_LCD_RULES	true	Apply LCD/documentation consistency rules during admission guardrail evaluation	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
15217eec-e3af-4705-acf7-97b308cc6393	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	GUARDRAIL_MODE	GUIDANCE	Guardrail enforcement mode: OFF, SILENT, GUIDANCE, STRICT	STRING	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
ce76f76e-fcc2-4792-ac4b-7de5b4445693	5224ceb6-e29d-4841-858e-e77f1b67fe65	MIN_NARRATIVE_LENGTH	200	Minimum characters required for clinical eligibility narrative	INTEGER	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
886a7205-0911-440b-941d-1a09064bcfcd	5224ceb6-e29d-4841-858e-e77f1b67fe65	REQUIRE_MEASURABLE_DECLINE	true	Require documented measurable evidence of decline for admission support	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
7084f072-0224-4a89-917f-78f7fc5d4828	5224ceb6-e29d-4841-858e-e77f1b67fe65	ENFORCE_LCD_RULES	true	Apply LCD/documentation consistency rules during admission guardrail evaluation	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
ddf1889b-95a5-4764-8947-d86ef8f60830	5224ceb6-e29d-4841-858e-e77f1b67fe65	GUARDRAIL_MODE	GUIDANCE	Guardrail enforcement mode: OFF, SILENT, GUIDANCE, STRICT	STRING	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
d387b2b3-8a68-4e6b-804d-c51cf2c2d0fb	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	MIN_NARRATIVE_LENGTH	200	Minimum characters required for clinical eligibility narrative	INTEGER	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
0195d1e1-30f5-40c9-92e6-5b23ba88f720	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	REQUIRE_MEASURABLE_DECLINE	true	Require documented measurable evidence of decline for admission support	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
ac15aa24-a478-4a4e-b5d6-debbb36bcabb	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	ENFORCE_LCD_RULES	true	Apply LCD/documentation consistency rules during admission guardrail evaluation	BOOLEAN	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
8c83e1b3-013f-4670-a023-043a0872aed7	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	GUARDRAIL_MODE	GUIDANCE	Guardrail enforcement mode: OFF, SILENT, GUIDANCE, STRICT	STRING	t	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	2026-06-26 13:25:45.524451-07	\N	\N
\.


--
-- Data for Name: hope_records; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.hope_records (id, patient_id, created_at, updated_at, previous_hope_record_id) FROM stdin;
\.


--
-- Data for Name: hope_symptom_assessments; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.hope_symptom_assessments (id, hope_record_id, symptom_code, severity, assessed_at, assessed_by_user_id) FROM stdin;
\.


--
-- Data for Name: hope_symptom_followups; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.hope_symptom_followups (id, hope_record_id, symptom_code, followup_required, followup_completed, determined_at) FROM stdin;
\.


--
-- Data for Name: hope_symptom_visits; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.hope_symptom_visits (id, hope_symptom_followup_id, visit_id, completed_by_user_id, completed_at) FROM stdin;
\.


--
-- Data for Name: idg_attendance; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_attendance (id, idg_session_id, user_id, participant_name, discipline, attendance_mode, attended, created_at) FROM stdin;
\.


--
-- Data for Name: idg_justification_notes; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_justification_notes (id, patient_id, eligibility_assessment_id, text, created_at) FROM stdin;
\.


--
-- Data for Name: idg_md_attestations; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_md_attestations (attestation_id, idg_id, md_user_id, attestation_text, signed_at, idg_review_id, created_at, updated_at, created_by, id) FROM stdin;
\.


--
-- Data for Name: idg_meetings; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_meetings (idg_id, patient_id, benefit_period_id, meeting_date, status, finalized_at, rn_required, physician_required, social_worker_required, chaplain_required, rn_present, physician_present, social_worker_present, chaplain_present, summary, created_at, updated_at, created_by, id) FROM stdin;
\.


--
-- Data for Name: idg_notes; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_notes (idg_note_id, idg_id, discipline, author_user_id, summary, recommendations, change_in_condition, poc_change_recommended, signed_at, created_at, updated_at, created_by, idg_review_id, id, note_text) FROM stdin;
\.


--
-- Data for Name: idg_participants; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_participants (participant_id, idg_id, discipline, user_id, participation_status, reason_if_excused, created_at) FROM stdin;
\.


--
-- Data for Name: idg_reviews; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_reviews (patient_id, review_date, rn_present, physician_present, social_worker_present, chaplain_present, id, created_at, updated_at, created_by, finalized_at, benefit_period_id, summary, poc_action, idg_meeting_id, tenant_id, is_finalized, finalized_by) FROM stdin;
\.


--
-- Data for Name: idg_session; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_session (id, plan_of_care_id, started_at, ended_at, facilitator_user_id, idg_status, ai_assist_status, summary_note, review_prompt_shown, ready_for_review, reviewed_by_user_id, reviewed_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: idg_signatures; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.idg_signatures (id, idg_review_id, discipline, user_id, signed_at, created_at, updated_at, created_by, idg_meeting_id, idg_session_id, signature_role) FROM stdin;
\.


--
-- Data for Name: incident_reports; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.incident_reports (id, tenant_id, patient_id, clinical_note_id, incident_type, incident_severity, incident_date, reported_date, incident_time, reported_by, witnessed_by, place, area, surface, medication_used, activity_at_time, injury_level, injury_type, other_injury_text, narrative, entered_by, signed_by, signed_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: interfaces; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.interfaces (id, name, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: med_reconciliation_audit_logs; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.med_reconciliation_audit_logs (id, tenant_id, patient_id, import_id, item_id, stage, event_type, med_name_raw, input_payload, normalized_payload, comparison_payload, decision_payload, created_by, created_at, hash_version, prev_signature_hash, signature_hash) FROM stdin;
9a79c714-cbeb-4287-af43-ae2ab16d5927	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	1823877b-d0e5-403e-9e9c-ed81ba00d940	\N	NORMALIZATION	NORMALIZATION_COMPLETED	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 01:49:52.92809-07	sha256-v1	\N	a477a8a789deaae6412986e8abbf8ccac509651901be1580b052b532ddb647a4
ced7aefe-4d9f-4773-ab90-2df407cc2a0e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	1823877b-d0e5-403e-9e9c-ed81ba00d940	\N	COMPARISON	COMPARISON_COMPLETED	Morphine	null	null	{"flags": [], "match_type": "NO_MATCH"}	null	\N	2026-06-26 01:49:52.937607-07	sha256-v1	a477a8a789deaae6412986e8abbf8ccac509651901be1580b052b532ddb647a4	1914175af72ee00e01f6b12da233b43bdaab8ea23c56557aad2597cc6aae583d
0752a188-7db3-45c2-9a09-a23af46d19bc	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	1823877b-d0e5-403e-9e9c-ed81ba00d940	5854de55-beae-4009-9fac-47085f69d8da	DECISION	ITEM_CREATED	Morphine	null	null	{"flags": [], "match_type": "NO_MATCH", "signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b"}	null	\N	2026-06-26 01:49:52.942061-07	sha256-v1	1914175af72ee00e01f6b12da233b43bdaab8ea23c56557aad2597cc6aae583d	6ecbb580f5b9da11115140120bb2124b34945de4b48263f3984c78af750c14c8
f77d1535-d6f5-4265-aaea-e214c46351c0	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	1823877b-d0e5-403e-9e9c-ed81ba00d940	5854de55-beae-4009-9fac-47085f69d8da	TASK	TASK_CREATED	\N	null	null	{"flags": [], "task_id": "b2585d32-7f86-4147-bf94-2da88184399e", "match_type": "NO_MATCH"}	null	\N	2026-06-26 01:49:52.94829-07	sha256-v1	6ecbb580f5b9da11115140120bb2124b34945de4b48263f3984c78af750c14c8	287acfced66abe19f516e41e7cc5924a5a2e8f06ac0511fcbc6f2e806139f860
804443f0-381e-4a37-823c-5c1046970374	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	1823877b-d0e5-403e-9e9c-ed81ba00d940	5854de55-beae-4009-9fac-47085f69d8da	TASK	TASK_DEDUP_CLEANUP_FAILED	\N	null	null	{"error": "name 'dose_normalized' is not defined", "med_name_normalized": "morphine"}	null	\N	2026-06-26 01:49:52.952942-07	sha256-v1	287acfced66abe19f516e41e7cc5924a5a2e8f06ac0511fcbc6f2e806139f860	5b0c05a16ce81ea6184ebc6d9c6e24461ccc7b7c6771e83103d0c324e08c257f
028e1934-f045-4bc1-b690-cc590aca5dee	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	836c916f-7163-47c9-9bdf-77c502f46f8a	\N	DEDUP	DUPLICATE_PRECHECK	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 01:52:43.372604-07	sha256-v1	5b0c05a16ce81ea6184ebc6d9c6e24461ccc7b7c6771e83103d0c324e08c257f	800a8e2534f167e4759951ded22d0566ddd608cb9396e08cfbc5c087a83f3646
228a4fc2-167b-4384-b3e0-3372f07cd75a	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	836c916f-7163-47c9-9bdf-77c502f46f8a	5854de55-beae-4009-9fac-47085f69d8da	DEDUP	DUPLICATE_PRECHECK	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 01:52:43.37862-07	sha256-v1	800a8e2534f167e4759951ded22d0566ddd608cb9396e08cfbc5c087a83f3646	c83774a9293cec9d4e09fb19f71892f018ec5a498b18e664106dc52a51560560
500fdbdb-03b4-463b-8f47-7eff4bdde491	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	9fe264ae-162b-42cf-817b-3237081151aa	\N	NORMALIZATION	NORMALIZATION_COMPLETED	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 02:06:26.615044-07	sha256-v1	c83774a9293cec9d4e09fb19f71892f018ec5a498b18e664106dc52a51560560	64a72364f68fd51ac832b8155ca6b47bf77bd7b29d614cc50f6e717cb33f7759
3cc382e5-050f-4532-a924-4d7e83b5d504	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	9fe264ae-162b-42cf-817b-3237081151aa	\N	DEDUP	DUPLICATE_PRECHECK	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "existing_item_id": "5854de55-beae-4009-9fac-47085f69d8da", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 02:06:26.625775-07	sha256-v1	64a72364f68fd51ac832b8155ca6b47bf77bd7b29d614cc50f6e717cb33f7759	0568b13ec9385c2a9c15e1b1b41c977ff3697858904e748d1b9e6e9118c83f45
1e26ebe2-160c-4053-8eaa-fd52d2e6bede	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	bf242b73-a599-4418-807e-e9c3d85f848c	\N	NORMALIZATION	NORMALIZATION_COMPLETED	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 02:08:26.20836-07	sha256-v1	0568b13ec9385c2a9c15e1b1b41c977ff3697858904e748d1b9e6e9118c83f45	172266a624685525c932141f2afdefb9cb9ec6f2e6fbbdbdcd3a33f363d27267
28a9f829-3175-47a3-8a52-93ba21536213	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	bf242b73-a599-4418-807e-e9c3d85f848c	\N	DEDUP	DUPLICATE_PRECHECK	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "existing_item_id": "5854de55-beae-4009-9fac-47085f69d8da", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 02:08:26.216512-07	sha256-v1	172266a624685525c932141f2afdefb9cb9ec6f2e6fbbdbdcd3a33f363d27267	86aea3d33ed7e69f0237ccaaaa272e64c50370989cafb6ae02d01aa7c56e1d12
3218746c-9029-4464-b5cb-8e8e4e2c3244	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	158da0ac-00b9-492d-8541-38b41fcd3fe8	\N	NORMALIZATION	NORMALIZATION_COMPLETED	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 02:19:13.798265-07	sha256-v1	86aea3d33ed7e69f0237ccaaaa272e64c50370989cafb6ae02d01aa7c56e1d12	30bb125c9d8bf4f2b4f56dbbedf7dc29bb4311eefb640891073a8aec60c0662c
745c178e-1c47-462b-b6be-679890f413a9	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	158da0ac-00b9-492d-8541-38b41fcd3fe8	\N	DEDUP	DUPLICATE_PRECHECK	Morphine	null	{"signature_hash": "9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b", "dose_normalized": "100mg", "existing_item_id": "5854de55-beae-4009-9fac-47085f69d8da", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 02:19:13.806229-07	sha256-v1	30bb125c9d8bf4f2b4f56dbbedf7dc29bb4311eefb640891073a8aec60c0662c	101785d8744027facba1e1469e5d4e2f57427821064abee08b48d618d455844b
b210a5b4-90fd-4322-8251-201747f3571c	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	8bc62fd1-b553-4b9f-af20-5e06ceba8b69	\N	NORMALIZATION	NORMALIZATION_COMPLETED	Morphine	null	{"signature_hash": "97a1add142390c3f4e7660d766a80eca53178bc67f17672dc58f4c49f5b9e277", "dose_normalized": "100mg", "route_normalized": "PO", "med_name_normalized": "morphine", "frequency_normalized": "Q1H"}	null	null	\N	2026-06-26 02:25:45.7731-07	sha256-v1	101785d8744027facba1e1469e5d4e2f57427821064abee08b48d618d455844b	71fc8ca85b4abc669e1a29d0dca2c699b1c58fab9a71a803c72ae1a81051f1fb
a58af039-203c-4e48-b6de-a3fa20f0061f	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	8bc62fd1-b553-4b9f-af20-5e06ceba8b69	\N	COMPARISON	COMPARISON_COMPLETED	Morphine	null	null	{"flags": [], "match_type": "NO_MATCH"}	null	\N	2026-06-26 02:25:45.776136-07	sha256-v1	71fc8ca85b4abc669e1a29d0dca2c699b1c58fab9a71a803c72ae1a81051f1fb	e001b2b1052418fedd27bda6594998163dc5f474dccc9e0ea4a174b112c232af
77521f4e-f46a-4d52-83e7-eab8f28d1959	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	8bc62fd1-b553-4b9f-af20-5e06ceba8b69	\N	DECISION	ITEM_CREATED	Morphine	null	null	{"flags": [], "item_id": "2ff29b75-a986-43af-af42-b52f79366f49", "match_type": "NO_MATCH", "signature_hash": "97a1add142390c3f4e7660d766a80eca53178bc67f17672dc58f4c49f5b9e277"}	null	\N	2026-06-26 02:25:45.781955-07	sha256-v1	e001b2b1052418fedd27bda6594998163dc5f474dccc9e0ea4a174b112c232af	bf6d0bc6ff86c99ccaabc40c6bedd1dc9ad8b85cc273109162238989eceed7d8
2908e431-3973-46e7-af98-b698d3b8240e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	8bc62fd1-b553-4b9f-af20-5e06ceba8b69	\N	TASK	TASK_CREATED	\N	null	null	{"flags": [], "item_id": "2ff29b75-a986-43af-af42-b52f79366f49", "task_id": "bf8a75ed-489d-4c2d-aae7-7bfc36f3bb47", "match_type": "NO_MATCH"}	null	\N	2026-06-26 02:25:45.787972-07	sha256-v1	bf6d0bc6ff86c99ccaabc40c6bedd1dc9ad8b85cc273109162238989eceed7d8	1cad771f391de56868695c25420eebeb0cf6704f2c85d70449ce13111ffcd3c6
7af61977-176c-4b6b-8fc8-59165f5bedec	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	89632919-d6cc-4359-ab96-bc089200709a	\N	NORMALIZATION	NORMALIZATION_COMPLETED	Morphine	null	{"signature_hash": "7f10dd866147afd57435e7fc1df8e559a35f3ee0e1b1740f8c14fffcc8e9c789", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q4H"}	null	null	\N	2026-06-26 02:26:23.512463-07	sha256-v1	1cad771f391de56868695c25420eebeb0cf6704f2c85d70449ce13111ffcd3c6	3bfcd5e8840b10a821b841165f7455ac0f75400a9d909b99b7a172661175996d
501d7fe7-0f2c-4ef4-a997-fd5d81225064	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	89632919-d6cc-4359-ab96-bc089200709a	\N	COMPARISON	COMPARISON_COMPLETED	Morphine	null	null	{"flags": [], "match_type": "NO_MATCH"}	null	\N	2026-06-26 02:26:23.515551-07	sha256-v1	3bfcd5e8840b10a821b841165f7455ac0f75400a9d909b99b7a172661175996d	0d75e4c5399e8a2c285235596ef3cc82c1ba62eda4adafd347c760a520e8ff30
38ea702f-7140-4c5e-9803-f9ce18cc4dcf	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	89632919-d6cc-4359-ab96-bc089200709a	\N	DECISION	ITEM_CREATED	Morphine	null	null	{"flags": [], "item_id": "9100a543-2a57-46b5-9506-7164effd8b3e", "match_type": "NO_MATCH", "signature_hash": "7f10dd866147afd57435e7fc1df8e559a35f3ee0e1b1740f8c14fffcc8e9c789"}	null	\N	2026-06-26 02:26:23.51848-07	sha256-v1	0d75e4c5399e8a2c285235596ef3cc82c1ba62eda4adafd347c760a520e8ff30	15dc7eaee5a746347be47ce5727aa5f2494f1828e8d0d02ee81900e16c859efc
8c29e6fe-787d-4a61-908a-148e6b665d94	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	89632919-d6cc-4359-ab96-bc089200709a	\N	TASK	TASK_CREATED	\N	null	null	{"flags": [], "item_id": "9100a543-2a57-46b5-9506-7164effd8b3e", "task_id": "e5ca49d5-8252-4211-899f-d596a09958cb", "match_type": "NO_MATCH"}	null	\N	2026-06-26 02:26:23.522389-07	sha256-v1	15dc7eaee5a746347be47ce5727aa5f2494f1828e8d0d02ee81900e16c859efc	eff3354b97176870b7f7d4a26bf4e31894c6602afa325e042efe2f0bb45a4ff5
1ac62c28-fa69-4207-ba97-7112e6cb9202	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	f6547be7-fb2d-400d-a1ee-d32fc710c881	\N	NORMALIZATION	NORMALIZATION_COMPLETED	Morphine	null	{"signature_hash": "a069277b2528d21e6b38dbe6aad95b2e1153dd025a73aeb1f4666befffd959d0", "dose_normalized": "100mg", "route_normalized": "IV", "med_name_normalized": "morphine", "frequency_normalized": "Q1H PRN"}	null	null	\N	2026-06-26 02:26:55.619813-07	sha256-v1	eff3354b97176870b7f7d4a26bf4e31894c6602afa325e042efe2f0bb45a4ff5	b52a51d192d921d5b74a339dcc0b6cb9e90a253e40712a629acaa0d8688e96d9
97a9599e-be10-49e4-af67-f90efc75f84e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	f6547be7-fb2d-400d-a1ee-d32fc710c881	\N	COMPARISON	COMPARISON_COMPLETED	Morphine	null	null	{"flags": [], "match_type": "NO_MATCH"}	null	\N	2026-06-26 02:26:55.622882-07	sha256-v1	b52a51d192d921d5b74a339dcc0b6cb9e90a253e40712a629acaa0d8688e96d9	cdee0790859c60744a462f874f0a77c94ef48e518a530dfefa986fbe84394b13
54f8a9f1-57a3-4605-96f1-c6e228119dfc	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	f6547be7-fb2d-400d-a1ee-d32fc710c881	\N	DECISION	ITEM_CREATED	Morphine	null	null	{"flags": [], "item_id": "6976e769-f9f7-4d4f-b728-40ac7177e6ea", "match_type": "NO_MATCH", "signature_hash": "a069277b2528d21e6b38dbe6aad95b2e1153dd025a73aeb1f4666befffd959d0"}	null	\N	2026-06-26 02:26:55.626652-07	sha256-v1	cdee0790859c60744a462f874f0a77c94ef48e518a530dfefa986fbe84394b13	ad33f94b72093e172caedfe4aa1c51517fb876b22ce347a48de969041bf00664
3a785ef2-96f5-433e-a9ba-76c965c9d31d	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	f6547be7-fb2d-400d-a1ee-d32fc710c881	\N	TASK	TASK_CREATED	\N	null	null	{"flags": [], "item_id": "6976e769-f9f7-4d4f-b728-40ac7177e6ea", "task_id": "b28c983d-2a74-4aca-902a-52660e10ceb4", "match_type": "NO_MATCH"}	null	\N	2026-06-26 02:26:55.633253-07	sha256-v1	ad33f94b72093e172caedfe4aa1c51517fb876b22ce347a48de969041bf00664	cc2feb0f5412c0fbf5c5f0a6c50aed4ea7f428454c244b27957221626bc64b11
\.


--
-- Data for Name: med_reconciliation_imports; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.med_reconciliation_imports (id, tenant_id, patient_id, source_type, source_context, status, source_file_name, uploaded_by, uploaded_at, parsed_at, reviewed_at, reviewed_by, raw_summary, created_at, updated_at, created_by) FROM stdin;
1823877b-d0e5-403e-9e9c-ed81ba00d940	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	task-test.pdf	\N	2026-06-26 01:49:52.920927-07	\N	\N	\N	force task test	2026-06-26 01:49:52.920927-07	2026-06-26 01:49:52.954948-07	\N
836c916f-7163-47c9-9bdf-77c502f46f8a	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	task-test.pdf	\N	2026-06-26 01:52:43.36636-07	\N	\N	\N	force task test	2026-06-26 01:52:43.36636-07	2026-06-26 01:52:43.380645-07	\N
9fe264ae-162b-42cf-817b-3237081151aa	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	task-test.pdf	\N	2026-06-26 02:06:26.608388-07	\N	\N	\N	force task test	2026-06-26 02:06:26.608388-07	2026-06-26 02:06:26.629035-07	\N
bf242b73-a599-4418-807e-e9c3d85f848c	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	task-test.pdf	\N	2026-06-26 02:08:26.201432-07	\N	\N	\N	force task test	2026-06-26 02:08:26.201432-07	2026-06-26 02:08:26.219676-07	\N
158da0ac-00b9-492d-8541-38b41fcd3fe8	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	task-test.pdf	\N	2026-06-26 02:19:13.790812-07	\N	\N	\N	force task test	2026-06-26 02:19:13.790812-07	2026-06-26 02:19:13.809441-07	\N
8bc62fd1-b553-4b9f-af20-5e06ceba8b69	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	route-test.pdf	\N	2026-06-26 02:25:45.770173-07	\N	\N	\N	route test	2026-06-26 02:25:45.770173-07	2026-06-26 02:25:45.793257-07	\N
89632919-d6cc-4359-ab96-bc089200709a	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	frequency-test.pdf	\N	2026-06-26 02:26:23.508684-07	\N	\N	\N	frequency test	2026-06-26 02:26:23.508684-07	2026-06-26 02:26:23.524857-07	\N
f6547be7-fb2d-400d-a1ee-d32fc710c881	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	PDF	HOSPITAL_DISCHARGE	PENDING_REVIEW	prn-test.pdf	\N	2026-06-26 02:26:55.615478-07	\N	\N	\N	prn test	2026-06-26 02:26:55.615478-07	2026-06-26 02:26:55.637236-07	\N
\.


--
-- Data for Name: med_reconciliation_items; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.med_reconciliation_items (id, import_id, tenant_id, patient_id, list_type, med_name_raw, med_name_normalized, dose, route, frequency, indication, reaction_description, severity, reaction_category_suggested, reaction_category_final, is_discharge_candidate, requires_immediate_review, is_critical_reaction, review_status, notes, created_at, updated_at, dose_normalized, route_normalized, frequency_normalized, comparison_status, comparison_flags, matched_medication_id, comparison_review_reason, created_by, signature_hash) FROM stdin;
9100a543-2a57-46b5-9506-7164effd8b3e	89632919-d6cc-4359-ab96-bc089200709a	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	DISCHARGE_LIST	Morphine	morphine	100 mg	IV	q4h	\N	\N	\N	\N	\N	f	t	f	REVIEWED	\N	2026-06-26 02:26:23.508684-07	2026-06-26 02:26:23.508684-07	100mg	IV	Q4H	\N	\N	\N	\N	\N	7f10dd866147afd57435e7fc1df8e559a35f3ee0e1b1740f8c14fffcc8e9c789
2ff29b75-a986-43af-af42-b52f79366f49	8bc62fd1-b553-4b9f-af20-5e06ceba8b69	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	DISCHARGE_LIST	Morphine	morphine	100 mg	PO	q1h	\N	\N	\N	\N	\N	f	t	f	REVIEWED	\N	2026-06-26 02:25:45.770173-07	2026-06-26 02:25:45.770173-07	100mg	PO	Q1H	\N	\N	\N	\N	\N	97a1add142390c3f4e7660d766a80eca53178bc67f17672dc58f4c49f5b9e277
5854de55-beae-4009-9fac-47085f69d8da	1823877b-d0e5-403e-9e9c-ed81ba00d940	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	DISCHARGE_LIST	Morphine	morphine	100 mg	IV	q1h	\N	\N	\N	\N	\N	f	t	f	REVIEWED	\N	2026-06-26 01:49:52.920927-07	2026-06-26 01:49:52.920927-07	100mg	IV	Q1H	\N	\N	\N	\N	\N	9f6b0ceeff239e5fe1eed554cab4193b10a23ff2974d8d2ab319063d5ab0853b
6976e769-f9f7-4d4f-b728-40ac7177e6ea	f6547be7-fb2d-400d-a1ee-d32fc710c881	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	DISCHARGE_LIST	Morphine	morphine	100 mg	IV	q1h PRN	\N	\N	\N	\N	\N	f	t	f	REVIEWED	\N	2026-06-26 02:26:55.615478-07	2026-06-26 02:26:55.615478-07	100mg	IV	Q1H PRN	\N	\N	\N	\N	\N	a069277b2528d21e6b38dbe6aad95b2e1153dd025a73aeb1f4666befffd959d0
\.


--
-- Data for Name: medications; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.medications (patient_id, medication_name, dosage, route, frequency, start_date, end_date, id, created_at, updated_at, created_by, canonical_name, tenant_id, is_active, is_prn, discontinued_at) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.notifications (id, tenant_id, patient_id, user_id, notification_type, status, payload, created_at, updated_at, created_by, source_type, source_id, message, seen_at, title, is_read, read_at) FROM stdin;
50398cbb-3126-49c1-bb0a-f6fca776dfc4	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	95981b4d-d9d9-4601-9914-c0f71aa7cc52	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
d6c0d489-7da3-4802-9b2b-811bc69aa77e	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	8a7f8ac0-9a5d-4fa4-8c51-cab431a26a5e	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
d462470f-a37e-4e7d-b6c2-dc2b87ddab55	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	eec28bbe-3f2b-4848-8d26-7c75864c44ce	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
bf174c49-d031-418a-8caf-71c0a2a7d95c	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	e0b8e8b8-9b05-4da3-8362-875b9f0f7dfd	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
93981b7c-a92a-4ba3-82d7-9b617e4c79ad	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	630e6ee8-5fbf-5222-b26a-4570328d3444	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
9c648bd7-dacc-4c08-97c3-e5beb98004ac	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	ed1f8707-dec1-4c5e-b185-471cca75b9ea	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
7d05196a-5d98-4993-844d-61822e265a65	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	3696cc99-4d82-43e3-8a19-9fd725a526b2	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
a90ac8d0-8d84-4143-acc3-52d8ac4103cb	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	46eb1c21-25e8-4e86-9f8a-35eb9ca500b9	\N	\N	\N	2026-06-19 16:28:57.079362	\N	\N	COMMUNICATIONS_LOG	200116ec-1c68-4730-a0bb-6f6ad110a59b	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
000aaf1f-6386-4905-a417-7999aaa9b75d	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	95981b4d-d9d9-4601-9914-c0f71aa7cc52	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
654e711c-5609-43c0-9107-deafd848f211	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	8a7f8ac0-9a5d-4fa4-8c51-cab431a26a5e	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
c59011c0-0452-4695-8d01-b2cb0a33d981	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	eec28bbe-3f2b-4848-8d26-7c75864c44ce	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
2bd69e7c-1a93-434e-bdd2-2e63b9f03377	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	e0b8e8b8-9b05-4da3-8362-875b9f0f7dfd	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
4d365f69-eec7-430e-97e2-901773f3f3ec	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	630e6ee8-5fbf-5222-b26a-4570328d3444	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
fefca6f5-c50c-44b7-818f-6dfbbf3445ee	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	ed1f8707-dec1-4c5e-b185-471cca75b9ea	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
a33ad2df-841d-4f48-be5e-b8de321f0e15	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	3696cc99-4d82-43e3-8a19-9fd725a526b2	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
28927b76-1a56-4e1c-91d9-71a6210d096a	01271980-0000-0000-0000-000005101977	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	46eb1c21-25e8-4e86-9f8a-35eb9ca500b9	\N	\N	\N	2026-06-19 16:33:16.344006	\N	\N	COMMUNICATIONS_LOG	a478234f-ce9d-4325-a648-a0d04c7cf064	Caregiver reported patient unresponsive; CHHA observed decline; LVN escalated to RN	\N	\N	f	\N
5f4234c4-550d-4d2c-a41a-ab74ce833c45	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	630e6ee8-5fbf-5222-b26a-4570328d3444	TASK_ASSIGNED	\N	\N	2026-06-20 09:26:09.543468	\N	\N	TASK	ac714c6e-d6ed-4019-aace-7d5b5589ac92	You have been assigned a MEDIUM priority task.	\N	New Task: PAIN_MANAGEMENT	f	\N
1fafaa07-e470-40e5-9449-fd222765c478	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	95981b4d-d9d9-4601-9914-c0f71aa7cc52	TASK_ASSIGNED	\N	\N	2026-06-20 09:45:11.203239	\N	\N	TASK	828aa7ff-20d2-4a40-b72f-a6bda96cfef1	You have been assigned a CRITICAL priority task for POC problem PAIN.	\N	New Task: CLINICAL_REVIEW_REQUIRED	f	\N
6243a592-ce57-4f3a-8b30-b340977c81ac	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	95981b4d-d9d9-4601-9914-c0f71aa7cc52	TASK_ASSIGNED	\N	\N	2026-06-20 10:40:53.042061	\N	\N	TASK	703e897a-9ef0-4b6a-84b7-89059e38adf8	You have been assigned a CRITICAL priority task for POC problem PAIN.	\N	New Task: CLINICAL_REVIEW_REQUIRED	f	\N
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.orders (id, visit_id, order_text, created_at, order_category, order_name, medication_class, indication, diagnosis_id, status, discontinued_at, discontinued_by, discontinued_reason, ordered_by, ordered_at, signed_by, signed_at, route, dose, unit, frequency) FROM stdin;
e58d0b4b-d24a-45c9-a513-e99ce8fddb89	36766f29-7a9f-4f61-a0cb-3b3a7c1a05a8	\N	\N	MEDICATION	Ciprofloxacin	\N	UTI	7ccdf762-10ea-4acf-854d-96272ebb6c8d	ACTIVE	\N	\N	\N	\N	2026-06-27 00:03:07.996244-07	\N	2026-06-27 00:03:07.996244-07	PO	500 mg	\N	BID
ba3613e0-4bd9-4252-9fda-56d55a2eadb5	46900246-1522-45be-a0e5-9781fc0b6c4c	\N	\N	MEDICATION	Levofloxacin	\N	UTI	f279290d-fad9-4341-93a8-ba226e24956c	ACTIVE	\N	\N	\N	\N	2026-06-27 00:03:15.492458-07	\N	\N	PO	500 mg	\N	BID
9c0c02d4-3823-4f0d-a818-efcd40c2a2e9	32b40a63-cacd-4a24-af39-7e03aebee34c	\N	\N	MEDICATION	Vancomycin	\N	MRSA	057494fe-08e0-4968-a52c-78d1f08b6311	DISCONTINUED	2026-06-27 00:03:26.10629-07	\N	Per family request	\N	2026-06-27 00:03:26.10629-07	\N	2026-06-27 00:03:26.10629-07	IV	1 g	\N	Q12H
\.


--
-- Data for Name: orders_snapshot; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.orders_snapshot (id, patient_id, discipline, visits_per_week, effective_date, end_date) FROM stdin;
\.


--
-- Data for Name: orders_snapshots; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.orders_snapshots (id, tenant_id, patient_id, discipline, visits_per_week, status, effective_date, end_date, snapshot_type, version, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: patient_allergies; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.patient_allergies (id, patient_id, allergy_name, reaction, severity, is_active, recorded_at, recorded_by_account_id) FROM stdin;
\.


--
-- Data for Name: patient_allergy_profiles; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.patient_allergy_profiles (id, patient_id, is_nkda, last_updated_at, last_updated_by_account_id) FROM stdin;
\.


--
-- Data for Name: patient_assignments; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.patient_assignments (id, tenant_id, patient_id, discipline, user_id, service_area, status, assigned_at, assigned_by, note, created_at, updated_at, created_by, is_primary, active, deactivated_at) FROM stdin;
32cf8b0b-fde8-43e6-ad19-229d83fd36eb	01271980-0000-0000-0000-000005101977	1af2861b-49ca-4c53-90f7-751d67222978	RN	8a7f8ac0-9a5d-4fa4-8c51-cab431a26a5e	\N	ASSIGNED	2026-06-22 23:24:14.082152-07	\N	\N	\N	\N	\N	f	t	\N
\.


--
-- Data for Name: patient_insurances; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.patient_insurances (id, tenant_id, patient_id, payer_type, payer_name, subscriber_id, subscriber_id_type, group_number, coverage_scope, priority_order, is_active, effective_date, end_date, notes, created_at, updated_at, verified_at, verified_by, created_by) FROM stdin;
\.


--
-- Data for Name: patient_payers; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.patient_payers (id, patient_id, payer_name, payer_type, subscriber_id, subscriber_id_type, facility_name, effective_start_date, end_date, is_primary, created_at, updated_at, created_by) FROM stdin;
89fd3831-c362-4910-87a0-0dc8f5c5f37b	8857c8e3-acd9-4398-87af-eef99a7b6cd5	Medicare	PRIMARY	\N	\N	\N	\N	\N	t	\N	\N	\N
\.


--
-- Data for Name: patient_pos; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.patient_pos (id, patient_id, pos_type, facility_name, effective_date, end_date, tenant_id, status, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.patients (mrn, full_name, date_of_birth, primary_diagnosis, status, discharge_date, discharge_reason, id, created_at, updated_at, created_by, acuity_state, crisis_started_at, crisis_ended_at, hospice_election_date, current_discharge_id, tenant_id, records_release_signed_at, election_signed_at, soc_date, admission_status, admission_authorized_at, admission_authorized_by, not_admitted_at, not_admitted_reason, ssn_last4, on_service_at, has_wounds, has_chha, has_lvn, deleted_at) FROM stdin;
LF-002	Juana Dela Cruz	1925-12-16	C79.9	ACTIVE	\N	\N	877d0c25-5e5b-4ccc-be64-7e41c8d4fcd8	2026-06-05 21:37:07.465831-07	2026-06-05 21:37:07.465831-07	\N	ROUTINE	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
LF-003	Pedro Reyes	1942-07-21	C34.90	ACTIVE	\N	\N	8ea3481a-4dbd-4709-be11-bfbb4d4da12c	2026-06-05 21:37:07.465831-07	2026-06-05 21:37:07.465831-07	\N	ROUTINE	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
LF-005	Jose Ramirez	1948-11-02	N18.6	ACTIVE	\N	\N	1af2861b-49ca-4c53-90f7-751d67222978	2026-06-05 21:37:07.465831-07	2026-06-05 21:37:07.465831-07	\N	ROUTINE	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-001	Angela Ortega	1940-04-01	C50.919	ACTIVE	\N	\N	8f417606-bb7f-4191-b656-219ce22e39f0	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-002	Luis Fernandez	1939-09-02	I63.9	ACTIVE	\N	\N	5c5459fc-7780-427a-b716-2dbcd6d9e357	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-003	Carla Gomez	1945-11-03	J44.9	ACTIVE	\N	\N	b0698cda-69e9-40e1-9748-d04668030947	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-004	Ramon Salazar	1936-07-22	G20	ACTIVE	\N	\N	ee74696e-3a99-4577-848a-28aa881eac2a	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-005	Isabel Navarro	1941-02-17	I48.91	ACTIVE	\N	\N	2fd9fa65-f5c1-4610-8a8b-8095c31275b0	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
SH-001	Carlos Silva	1937-08-14	C18.9	ACTIVE	\N	\N	0e538b9e-c54e-421e-a0fc-83a50d4b341f	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
SH-002	Elena Silva	1942-01-09	J96.10	ACTIVE	\N	\N	4036bbd9-230a-48dd-ba9a-44e770ea4617	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
SH-003	Manuel Torres	1931-06-20	I25.10	ACTIVE	\N	\N	6746e36f-c25b-45b7-b9a8-f25a63d4dedd	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
SH-004	Lucia Perez	1944-03-12	G31.83	ACTIVE	\N	\N	7881aa1b-8aee-449b-a9aa-ba2e00ae3b73	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
SH-005	Fernando Diaz	1939-12-05	N18.6	ACTIVE	\N	\N	6f6febf6-9fdb-4c13-ab50-8d749f0869eb	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TA-001	Daniel Lopez	1941-10-10	C34.90	ACTIVE	\N	\N	1ea0f4b7-07db-4914-a18b-41d493ace304	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	5224ceb6-e29d-4841-858e-e77f1b67fe65	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TA-002	Rosa Garcia	1938-05-22	I50.9	ACTIVE	\N	\N	dbbaca43-44b9-4375-93c1-c8db7bf20231	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	5224ceb6-e29d-4841-858e-e77f1b67fe65	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TA-003	Jose Morales	1947-03-18	G30.9	ACTIVE	\N	\N	089008e8-6ae4-48f9-b1cc-1a37bbe22821	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	5224ceb6-e29d-4841-858e-e77f1b67fe65	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TA-004	Miguel Cruz	1950-07-09	J44.9	ACTIVE	\N	\N	f5efa7b6-fa9c-45d1-8b0d-2817932af58e	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	5224ceb6-e29d-4841-858e-e77f1b67fe65	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TA-005	Lola Santos	1936-11-30	I63.9	ACTIVE	\N	\N	cb77ac6c-8105-4ad6-b488-f1f2dcd4c9db	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	5224ceb6-e29d-4841-858e-e77f1b67fe65	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TB-001	Victor Ramos	1935-02-25	C79.9	ACTIVE	\N	\N	d47ea378-4f4d-4b9a-9fcc-a582e664ad40	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TB-002	Sofia Cruz	1948-09-13	J96.10	ACTIVE	\N	\N	c38186e7-ccb2-4d33-bf1e-97cc1aed34d5	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TB-003	Marco Reyes	1942-04-07	I25.10	ACTIVE	\N	\N	3a182640-83ae-491e-a9bf-4ae5ad651b25	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TB-004	Carmen Bautista	1939-01-03	G20	ACTIVE	\N	\N	74e4770e-486e-4bae-9fe4-a4f26258d2fd	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
TB-005	Eduardo Diaz	1933-08-19	N18.6	ACTIVE	\N	\N	9acb61f1-175e-4cb1-b4de-c3c42fed1dc0	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	85282f8b-fd5b-45e6-bb82-45394ef7a2f8	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
LF-001	Juan Dela Cruz	1925-12-16	J44.9	ACTIVE	\N	\N	f6774a7f-ef3c-4e29-b716-c3a9cc8c9012	2026-06-05 21:37:07.465831-07	2026-06-13 19:16:21.422312-07	\N	ROUTINE	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	2026-06-13 12:16:21.421213-07	f	f	f	\N
LF-004	Ana Cruz	1935-09-15	G30.9	ACTIVE	\N	\N	8857c8e3-acd9-4398-87af-eef99a7b6cd5	2026-06-05 21:37:07.465831-07	2026-06-13 19:16:45.873733-07	\N	ROUTINE	\N	\N	2026-06-26	\N	01271980-0000-0000-0000-000005101977	\N	\N	2026-06-26 12:26:39.903772-07	ADMITTED	\N	\N	\N	\N	\N	\N	f	t	f	\N
\.


--
-- Data for Name: patients_snapshot_angela; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patients_snapshot_angela (mrn, full_name, date_of_birth, primary_diagnosis, status, discharge_date, discharge_reason, id, created_at, updated_at, created_by, acuity_state, crisis_started_at, crisis_ended_at, hospice_election_date, current_discharge_id, tenant_id, records_release_signed_at, election_signed_at, soc_date, admission_status, admission_authorized_at, admission_authorized_by, not_admitted_at, not_admitted_reason, ssn_last4, on_service_at, has_wounds, has_chha, has_lvn, deleted_at) FROM stdin;
AH-001	Angela Ortega	1940-04-01	C50.919	ACTIVE	\N	\N	8f417606-bb7f-4191-b656-219ce22e39f0	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-002	Luis Fernandez	1939-09-02	I63.9	ACTIVE	\N	\N	5c5459fc-7780-427a-b716-2dbcd6d9e357	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-003	Carla Gomez	1945-11-03	J44.9	ACTIVE	\N	\N	b0698cda-69e9-40e1-9748-d04668030947	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-004	Ramon Salazar	1936-07-22	G20	ACTIVE	\N	\N	ee74696e-3a99-4577-848a-28aa881eac2a	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
AH-005	Isabel Navarro	1941-02-17	I48.91	ACTIVE	\N	\N	2fd9fa65-f5c1-4610-8a8b-8095c31275b0	2026-06-05 21:40:26.487676-07	2026-06-05 21:40:26.487676-07	\N	ROUTINE	\N	\N	\N	\N	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	\N	\N	\N	ADMITTED	\N	\N	\N	\N	\N	\N	f	f	f	\N
\.


--
-- Data for Name: payer_contracts; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.payer_contracts (id, tenant_id, payer_name, has_contract, payer_id, contract_number, status, start_date, end_date, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: payers; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.payers (id, tenant_id, name, code, payer_type, status, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: plan_of_care; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.plan_of_care (id, patient_id, tenant_id, status, version_number, effective_at, review_due_at, last_reviewed_at, rn_coordinator_user_id, attending_physician_name, medical_director_user_id, approval_status, approved_at, approved_by_user_id, supersedes_plan_of_care_id, current_version_id, poc_content_json, created_at, updated_at) FROM stdin;
31dd99d6-e65b-4555-acd9-f455bce4b47c	8857c8e3-acd9-4398-87af-eef99a7b6cd5	01271980-0000-0000-0000-000005101977	DRAFT	1	2026-06-26 17:12:19.09902-07	2026-07-11 17:12:19.09902-07	\N	\N	Dr. Test	\N	PENDING	\N	\N	\N	10524b00-1730-4ae4-bc1a-d72ea73a011b	{"services": [{"frequency": "daily", "discipline": "RN"}], "symptoms": ["Pain"], "diagnoses": [{"code": "R52", "label": "Pain"}], "limitations": {"adl": "Assist required"}, "instructions": ["Report increased pain immediately"], "health_status": {"summary": "Terminal decline"}, "pain_management": {"plan": "Morphine PRN"}, "safety_measures": ["Fall precautions"]}	2026-06-26 17:12:19.09902-07	2026-06-26 17:12:19.09902-07
\.


--
-- Data for Name: plan_of_care_approvals; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.plan_of_care_approvals (id, plan_of_care_id, version_id, approver_role, approver_user_id, decision, decision_note, decided_at) FROM stdin;
7f2ea65e-e59a-45f5-a6a6-d28213d5d447	31dd99d6-e65b-4555-acd9-f455bce4b47c	10524b00-1730-4ae4-bc1a-d72ea73a011b	ATTENDING_PHYSICIAN	\N	PENDING	\N	\N
\.


--
-- Data for Name: plan_of_care_goals; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.plan_of_care_goals (id, plan_of_care_id, problem_code, problem_label, goal_text, outcome_measure, target_date, status, discipline_owner, progress_summary, created_at, updated_at) FROM stdin;
ffb52019-8d16-4f38-93b5-667077c5d10d	31dd99d6-e65b-4555-acd9-f455bce4b47c	\N	Pain	Pain will remain controlled	Pain score < 3	\N	ACTIVE	\N	\N	2026-06-26 17:12:49.091065-07	2026-06-26 17:12:49.091065-07
\.


--
-- Data for Name: plan_of_care_versions; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.plan_of_care_versions (id, plan_of_care_id, version_number, snapshot_json, change_reason, trigger_source, created_at, created_by, approved_at, approved_by_user_id, based_on_version_id) FROM stdin;
10524b00-1730-4ae4-bc1a-d72ea73a011b	31dd99d6-e65b-4555-acd9-f455bce4b47c	1	{"services": [{"frequency": "daily", "discipline": "RN"}], "symptoms": ["Pain"], "diagnoses": [{"code": "R52", "label": "Pain"}], "limitations": {"adl": "Assist required"}, "instructions": ["Report increased pain immediately"], "health_status": {"summary": "Terminal decline"}, "pain_management": {"plan": "Morphine PRN"}, "safety_measures": ["Fall precautions"]}	Initial admission	ADMISSION	2026-06-26 17:12:30.266537-07	\N	\N	\N	\N
\.


--
-- Data for Name: poc_problem_templates; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.poc_problem_templates (id, condition, problem_label) FROM stdin;
\.


--
-- Data for Name: refusals; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.refusals (id, tenant_id, patient_id, discipline, reason, refused_at, was_reoffered, reoffered_at, created_by, updated_at) FROM stdin;
e1a1d36d-7b29-4cc6-95b0-a3d9ac75b79e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	CHAPLAIN	Patient declined chaplain visit today	2026-06-15 18:27:00.698325-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:27:00.698325-07
785fcbab-1787-493a-b2e3-b7e2e2806b9b	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	SW	Patient declined social work visit today	2026-06-15 18:28:59.4248-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:28:59.4248-07
070bfda4-d4ce-4f0b-bbad-70fd902ed3b9	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	CHAPLAIN	Patient declined spiritual care today	2026-06-15 18:29:32.93335-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:29:32.93335-07
bedd8cd9-d0f2-4dab-9ff7-f9a483d2221f	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	AIDE	Patient declined aide visit today	2026-06-15 18:29:47.59789-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:29:47.59789-07
6b0c74b1-c6d8-4f1c-be43-f41a1e9a1f3e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	RN	Patient refused RN visit	2026-06-15 18:30:14.143261-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:30:14.143261-07
287eb9fe-274f-4edc-8204-4dd8f719e242	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	CHAPLAIN	Patient declined spiritual care today	2026-06-15 18:51:29.093761-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:51:29.093761-07
56ee7b10-e072-4011-af3c-1f3e630c011e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	SW	Patient declined social work visit today	2026-06-15 18:51:58.572985-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:51:58.572985-07
8027bc5c-e0af-4553-8cb5-aa01af23403f	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	AIDE	Patient declined aide visit today	2026-06-15 18:52:28.417385-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:52:28.417385-07
728c8c7c-cef2-459e-829f-e67c0a9e5779	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	RN	Patient refused RN visit	2026-06-15 18:52:57.434665-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:52:57.434665-07
228e1905-17e4-4e3d-9402-bd425d92a3c1	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	MD	Patient refused MD visit	2026-06-15 18:53:26.818218-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:53:26.818218-07
b34ecf8d-ddf2-4c28-932f-10626f8189c6	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	F2F	Patient refused face-to-face visit	2026-06-15 18:53:45.644454-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 18:53:45.644454-07
8038bd4e-4e0c-4830-8eef-ec163d86d644	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	RN	final test	2026-06-15 19:02:00.10031-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:02:00.10031-07
c2875a70-92fd-40c6-9683-780b726e988a	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	RN	final correct test	2026-06-15 19:13:29.236892-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:13:29.236892-07
2e03c4bc-22ed-461d-86b1-663e80521f6e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	MD	final correct test	2026-06-15 19:14:13.190445-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:14:13.190445-07
27cbe08c-36ac-4f27-b300-e06050495482	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	F2F	final correct test	2026-06-15 19:19:58.392293-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:19:58.392293-07
3165816e-708e-4748-8297-083b16d04563	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	RN	audit test	2026-06-15 19:23:00.29022-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:23:00.29022-07
8b846e2f-242c-43c5-9d2d-dd584afa0f1d	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	F2F	audit test	2026-06-15 19:25:23.284628-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:25:23.284628-07
b2ff48f8-62d1-43c1-b319-268343a00a7e	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	MD	audit test	2026-06-15 19:26:26.96358-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:26:26.96358-07
d9aa37c6-a3cd-492b-9d0b-6c295f4bc384	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	SW	\N	2026-06-15 17:52:52.291338-07	f	\N	\N	2026-06-15 17:52:52.291338-07
5e85ae24-f566-4eb4-933e-6a962e4af8f4	01271980-0000-0000-0000-000005101977	8857c8e3-acd9-4398-87af-eef99a7b6cd5	SW	test	2026-06-15 19:52:24.163053-07	f	\N	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-15 19:52:24.163053-07
\.


--
-- Data for Name: regulatory_report_artifacts; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.regulatory_report_artifacts (id, report_id, artifact_type, file_path, checksum, generated_at) FROM stdin;
\.


--
-- Data for Name: regulatory_report_metrics; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.regulatory_report_metrics (id, report_id, section_id, metric_key, metric_value_numeric, metric_value_text, breakdown_json) FROM stdin;
\.


--
-- Data for Name: regulatory_report_sections; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.regulatory_report_sections (id, report_id, section_key, section_title, section_version, generated_at) FROM stdin;
\.


--
-- Data for Name: regulatory_reports; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.regulatory_reports (id, report_type, period_start, period_end, status, generated_at, generated_by, certified_at, certified_by, integrity_hash, metadata) FROM stdin;
\.


--
-- Data for Name: respite_periods; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.respite_periods (id, patient_id, start_date, end_date, reason, tenant_id, visit_id, service_level, status, created_at, updated_at, created_by, updated_by) FROM stdin;
\.


--
-- Data for Name: rn_recert_assessments; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.rn_recert_assessments (id, patient_id, benefit_period_id, created_by_user_id, form_type, form_family, discipline, status, created_at, updated_at, finalized_at, pps_score, kps_score, fast_stage, nyha_class, adl_level, adl_dependency_count, primary_diagnosis, eligibility_recommendation, raw_observations_json, clarification_items_json, normalized_observations_json, translation_output_json, translation_source_map_json, interpretation_output_json, translation_mode_used, translation_reviewed_by, translation_reviewed_at, translation_accepted, attested_at, attesting_provider_user_id) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.roles (id, interface_id, name, description, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: runbooks; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.runbooks (id, tenant_id, baseline_tag, generated_at, policy_snapshot, created_at) FROM stdin;
\.


--
-- Data for Name: safety_assessments; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.safety_assessments (id, patient_id, data_json, completed_at, signed_at, signed_by, created_at, updated_at, care_setting, safety_responsibility) FROM stdin;
\.


--
-- Data for Name: security_activity_events; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.security_activity_events (id, event_at, user_id, role, event_type, scope, patient_count, document_count, result, reason, metadata) FROM stdin;
\.


--
-- Data for Name: service_coverage_decisions; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.service_coverage_decisions (id, tenant_id, patient_id, payer_id, service_type, decision, effective_start_date, effective_end_date, rationale, created_at, created_by, service_id, coverage_intent, financial_responsibility, decision_source, decision_reason, evidence_reference_type, evidence_reference_id, selected_payer_id, decided_at, decided_by, updated_at) FROM stdin;
\.


--
-- Data for Name: sfv_requirements; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.sfv_requirements (id, tenant_id, patient_id, trigger_source_type, trigger_reference_id, trigger_symptom_group, trigger_datetime, due_at, task_id, completed_visit_id, completed_at, status, notes, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: survey_access; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.survey_access (patient_id, issued_by, token_jti, issued_at, expires_at, used, revoked, id, created_at, updated_at, created_by, tenant_id) FROM stdin;
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.tasks (id, patient_id, benefit_period_id, origin, discipline, assigned_user_id, regulatory_basis, due_date, status, completed_at, created_at, updated_at, created_by, excused_reason_code, excused_at, excused_source, completion_reference_type, completion_reference_id, tenant_id, alert_reason, scheduled_start_at, schedule_status, due_at, clinical_note_id, incident_id, requires_countersignature, countersigned_by, countersigned_at, sla_start_at, sla_due_at, escalation_level, escalated_at, escalation_reason, is_overdue, priority, clinical_severity, assigned_role, notification_required, reference_type, reference_id, task_type) FROM stdin;
27feb9f6-f12b-453d-815e-768a47022ff2	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:01:44.357215-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	ce572f4e-b31c-4d9b-ae31-834e067a8d6c	01271980-0000-0000-0000-000005101977	MED_RECON:94291108-60ee-4fcc-a37c-265f3255a155	\N	\N	2026-06-26 21:01:44.357215-07	\N	\N	f	\N	\N	2026-06-25 21:01:44.357215-07	2026-06-26 21:01:44.357215-07	0	\N	Historical duplicate reconciliation task superseded by active item ce572f4e-b31c-4d9b-ae31-834e067a8d6c	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	94291108-60ee-4fcc-a37c-265f3255a155	CLINICAL_REVIEW_REQUIRED
02b64b93-e071-4130-aaa6-7dd2d653202a	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:07:08.078924-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	ce572f4e-b31c-4d9b-ae31-834e067a8d6c	01271980-0000-0000-0000-000005101977	MED_RECON:4d251f36-db19-45ac-b834-988fae6011c4	\N	\N	2026-06-26 21:07:08.078924-07	\N	\N	f	\N	\N	2026-06-25 21:07:08.078924-07	2026-06-26 21:07:08.078924-07	0	\N	Historical duplicate reconciliation task superseded by active item ce572f4e-b31c-4d9b-ae31-834e067a8d6c	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	4d251f36-db19-45ac-b834-988fae6011c4	CLINICAL_REVIEW_REQUIRED
556701c3-1366-41f8-ac28-cf236e573b4e	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:10:13.218795-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	ce572f4e-b31c-4d9b-ae31-834e067a8d6c	01271980-0000-0000-0000-000005101977	MED_RECON:83e67ad9-fb9e-4f63-b302-4772b8c4b7e4	\N	\N	2026-06-26 21:10:13.218795-07	\N	\N	f	\N	\N	2026-06-25 21:10:13.218795-07	2026-06-26 21:10:13.218795-07	0	\N	Historical duplicate reconciliation task superseded by active item ce572f4e-b31c-4d9b-ae31-834e067a8d6c	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	83e67ad9-fb9e-4f63-b302-4772b8c4b7e4	CLINICAL_REVIEW_REQUIRED
7da3f6d7-398b-4cf4-afbc-8a7ff3521a48	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:13:48.175466-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	ce572f4e-b31c-4d9b-ae31-834e067a8d6c	01271980-0000-0000-0000-000005101977	MED_RECON:bdc473a1-2627-4301-9078-70649a2e45f7	\N	\N	2026-06-26 21:13:48.175466-07	\N	\N	f	\N	\N	2026-06-25 21:13:48.175466-07	2026-06-26 21:13:48.175466-07	0	\N	Historical duplicate reconciliation task superseded by active item ce572f4e-b31c-4d9b-ae31-834e067a8d6c	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	bdc473a1-2627-4301-9078-70649a2e45f7	CLINICAL_REVIEW_REQUIRED
0014bd39-addd-4f26-ad97-af80476436fd	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 21:16:39.814266-07	2026-06-26 22:50:16.005632-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:ce572f4e-b31c-4d9b-ae31-834e067a8d6c	\N	\N	2026-06-26 21:16:39.814266-07	\N	\N	f	\N	\N	2026-06-25 21:16:39.814266-07	2026-06-26 21:16:39.814266-07	1	2026-06-26 22:50:16.005632-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	ce572f4e-b31c-4d9b-ae31-834e067a8d6c	CLINICAL_REVIEW_REQUIRED
573d4292-c1c8-43cf-8c56-d3f97093756b	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 21:16:39.818969-07	2026-06-26 22:50:16.005632-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:4511628a-a49b-4b92-bba2-9ee47e996204	\N	\N	2026-06-26 21:16:39.818969-07	\N	\N	f	\N	\N	2026-06-25 21:16:39.818969-07	2026-06-26 21:16:39.818969-07	1	2026-06-26 22:50:16.005632-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	4511628a-a49b-4b92-bba2-9ee47e996204	CLINICAL_REVIEW_REQUIRED
84edd9ef-7ecb-435e-b9b0-9502454c037c	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 22:44:23.716236-07	2026-06-26 22:50:16.005632-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:bb527842-f8db-44a8-809b-ac791add1c05	\N	\N	2026-06-26 22:44:23.716236-07	\N	\N	f	\N	\N	2026-06-25 22:44:23.716236-07	2026-06-26 22:44:23.716236-07	1	2026-06-26 22:50:16.005632-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	bb527842-f8db-44a8-809b-ac791add1c05	CLINICAL_REVIEW_REQUIRED
93a92f58-3562-49ea-9a82-447bf7d5d0a5	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 22:44:23.719054-07	2026-06-26 22:50:16.005632-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:fd55e62e-4545-4942-a520-74db7b3b2c11	\N	\N	2026-06-26 22:44:23.719054-07	\N	\N	f	\N	\N	2026-06-25 22:44:23.719054-07	2026-06-26 22:44:23.719054-07	1	2026-06-26 22:50:16.005632-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	fd55e62e-4545-4942-a520-74db7b3b2c11	CLINICAL_REVIEW_REQUIRED
c91eedca-2517-48a0-a1ed-856658285d48	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 22:44:23.707554-07	2026-06-26 22:50:16.005632-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:dee58190-3152-4555-956b-e67ef9a90e2e	\N	\N	2026-06-26 22:44:23.707554-07	\N	\N	f	\N	\N	2026-06-25 22:44:23.707554-07	2026-06-26 22:44:23.707554-07	1	2026-06-26 22:50:16.005632-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	dee58190-3152-4555-956b-e67ef9a90e2e	CLINICAL_REVIEW_REQUIRED
efd89f57-9a06-43ff-b019-94d58c28fb3a	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 22:44:23.723433-07	2026-06-26 22:50:16.005632-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:d0dd0c12-bc0b-4a17-b23e-6ee2c718da69	\N	\N	2026-06-26 22:44:23.723433-07	\N	\N	f	\N	\N	2026-06-25 22:44:23.723433-07	2026-06-26 22:44:23.723433-07	1	2026-06-26 22:50:16.005632-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	d0dd0c12-bc0b-4a17-b23e-6ee2c718da69	CLINICAL_REVIEW_REQUIRED
22c42da0-49a0-4ff8-9b92-ae19cdbb7266	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-26	COMPLETED	2026-06-25 19:24:58.214471	2026-06-24 23:13:32.620914-07	2026-06-25 19:24:58.214471-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	\N	\N	VISIT	b96d6e24-84a6-48d0-a1ec-6158c87f77eb	01271980-0000-0000-0000-000005101977	SFV_TRIGGER	\N	\N	2026-06-26 23:13:19.640381-07	\N	\N	f	\N	\N	2026-06-24 23:13:32.620914-07	2026-06-26 23:13:19.640381-07	0	\N	\N	f	\N	\N	\N	f	\N	\N	SFV
fa57ac15-cacd-4b22-93b0-fa7781a9a863	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:01:44.365243-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	4511628a-a49b-4b92-bba2-9ee47e996204	01271980-0000-0000-0000-000005101977	MED_RECON:a3f36354-8da2-45c4-a6ad-97c75263134c	\N	\N	2026-06-26 21:01:44.365243-07	\N	\N	f	\N	\N	2026-06-25 21:01:44.365243-07	2026-06-26 21:01:44.365243-07	0	\N	Historical duplicate reconciliation task superseded by active item 4511628a-a49b-4b92-bba2-9ee47e996204	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	a3f36354-8da2-45c4-a6ad-97c75263134c	CLINICAL_REVIEW_REQUIRED
660ab538-baec-4811-89fa-e187132a3217	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:07:08.083771-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	4511628a-a49b-4b92-bba2-9ee47e996204	01271980-0000-0000-0000-000005101977	MED_RECON:eeb6c674-2bef-4244-b390-7ff62e990a1e	\N	\N	2026-06-26 21:07:08.083771-07	\N	\N	f	\N	\N	2026-06-25 21:07:08.083771-07	2026-06-26 21:07:08.083771-07	0	\N	Historical duplicate reconciliation task superseded by active item 4511628a-a49b-4b92-bba2-9ee47e996204	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	eeb6c674-2bef-4244-b390-7ff62e990a1e	CLINICAL_REVIEW_REQUIRED
666d9b84-0868-4e4c-a2c4-8c7bd718d703	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:10:13.225003-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	4511628a-a49b-4b92-bba2-9ee47e996204	01271980-0000-0000-0000-000005101977	MED_RECON:9462d4a3-377c-4d3c-ab2b-c52ca6559805	\N	\N	2026-06-26 21:10:13.225003-07	\N	\N	f	\N	\N	2026-06-25 21:10:13.225003-07	2026-06-26 21:10:13.225003-07	0	\N	Historical duplicate reconciliation task superseded by active item 4511628a-a49b-4b92-bba2-9ee47e996204	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	9462d4a3-377c-4d3c-ab2b-c52ca6559805	CLINICAL_REVIEW_REQUIRED
b84680db-3710-408e-86ba-87f36f802d27	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	COMPLETED	2026-06-25 21:54:10.159246	2026-06-25 21:13:48.181354-07	2026-06-25 21:54:10.159246-07	\N	DUPLICATE_SUPERSEDED	2026-06-25 21:54:10.159246-07	BACKFILL_DEDUP	DOCUMENT	4511628a-a49b-4b92-bba2-9ee47e996204	01271980-0000-0000-0000-000005101977	MED_RECON:92e75ded-b89e-4e23-87e1-8a14351bfb1f	\N	\N	2026-06-26 21:13:48.181354-07	\N	\N	f	\N	\N	2026-06-25 21:13:48.181354-07	2026-06-26 21:13:48.181354-07	0	\N	Historical duplicate reconciliation task superseded by active item 4511628a-a49b-4b92-bba2-9ee47e996204	f	HIGH	MODERATE	RN	f	MED_RECON_ITEM	92e75ded-b89e-4e23-87e1-8a14351bfb1f	CLINICAL_REVIEW_REQUIRED
93419ce9-3221-494f-b5a4-b94892bd80fb	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 23:03:58.717992-07	2026-06-27 00:38:40.118818-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:09261625-ea4b-4dd6-8a42-cd78865a1424	\N	\N	2026-06-26 23:03:58.717992-07	\N	\N	f	\N	\N	2026-06-25 23:03:58.717992-07	2026-06-26 23:03:58.717992-07	1	2026-06-27 00:38:40.118818-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	09261625-ea4b-4dd6-8a42-cd78865a1424	CLINICAL_REVIEW_REQUIRED
0c8f5874-4a46-4b5f-92da-25ea664f3bdf	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 23:04:42.616819-07	2026-06-27 00:38:40.118818-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:6561fdd0-f305-42e6-9180-9b4190c3c018	\N	\N	2026-06-26 23:04:42.616819-07	\N	\N	f	\N	\N	2026-06-25 23:04:42.616819-07	2026-06-26 23:04:42.616819-07	1	2026-06-27 00:38:40.118818-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	6561fdd0-f305-42e6-9180-9b4190c3c018	CLINICAL_REVIEW_REQUIRED
957b37d5-3020-4751-9505-bd7093a6dcbb	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-25 23:05:12.902467-07	2026-06-27 00:38:40.118818-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:90179d32-f700-4261-b6ed-848d944714e5	\N	\N	2026-06-26 23:05:12.902467-07	\N	\N	f	\N	\N	2026-06-25 23:05:12.902467-07	2026-06-26 23:05:12.902467-07	1	2026-06-27 00:38:40.118818-07	Imported medication not found in active medication list	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	90179d32-f700-4261-b6ed-848d944714e5	CLINICAL_REVIEW_REQUIRED
b2585d32-7f86-4147-bf94-2da88184399e	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-26 01:49:52.943353-07	2026-06-27 15:15:53.536826-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:5854de55-beae-4009-9fac-47085f69d8da	\N	\N	2026-06-27 01:49:52.943353-07	\N	\N	f	\N	\N	2026-06-26 01:49:52.943353-07	2026-06-27 01:49:52.943353-07	1	2026-06-27 15:15:53.536826-07	Medication reconciliation review required	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	5854de55-beae-4009-9fac-47085f69d8da	CLINICAL_REVIEW_REQUIRED
b28c983d-2a74-4aca-902a-52660e10ceb4	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-26 02:26:55.628958-07	2026-06-27 15:15:53.536826-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:6976e769-f9f7-4d4f-b728-40ac7177e6ea	\N	\N	2026-06-27 02:26:55.628958-07	\N	\N	f	\N	\N	2026-06-26 02:26:55.628958-07	2026-06-27 02:26:55.628958-07	1	2026-06-27 15:15:53.536826-07	Medication reconciliation review required	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	6976e769-f9f7-4d4f-b728-40ac7177e6ea	CLINICAL_REVIEW_REQUIRED
bf8a75ed-489d-4c2d-aae7-7bfc36f3bb47	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-26 02:25:45.783136-07	2026-06-27 15:15:53.536826-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:2ff29b75-a986-43af-af42-b52f79366f49	\N	\N	2026-06-27 02:25:45.783136-07	\N	\N	f	\N	\N	2026-06-26 02:25:45.783136-07	2026-06-27 02:25:45.783136-07	1	2026-06-27 15:15:53.536826-07	Medication reconciliation review required	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	2ff29b75-a986-43af-af42-b52f79366f49	CLINICAL_REVIEW_REQUIRED
e5ca49d5-8252-4211-899f-d596a09958cb	8857c8e3-acd9-4398-87af-eef99a7b6cd5	\N	SYSTEM	RN	\N	CONDITION_TRIGGER	2026-06-27	OVERDUE	\N	2026-06-26 02:26:23.520019-07	2026-06-27 15:15:53.536826-07	\N	\N	\N	\N	\N	\N	01271980-0000-0000-0000-000005101977	MED_RECON:9100a543-2a57-46b5-9506-7164effd8b3e	\N	\N	2026-06-27 02:26:23.520019-07	\N	\N	f	\N	\N	2026-06-26 02:26:23.520019-07	2026-06-27 02:26:23.520019-07	1	2026-06-27 15:15:53.536826-07	Medication reconciliation review required	t	HIGH	MODERATE	RN	f	MED_RECON_ITEM	9100a543-2a57-46b5-9506-7164effd8b3e	CLINICAL_REVIEW_REQUIRED
\.


--
-- Data for Name: tenant_rule_toggles; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.tenant_rule_toggles (id, tenant_id, workflow, rule_id, enabled, created_at, created_by, updated_at) FROM stdin;
\.


--
-- Data for Name: tenants; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.tenants (id, legal_name, display_name, status, created_at, updated_at, created_by, npi, tax_id, ptan, tenant_type, environment_tag, environment_type, allow_full_reset) FROM stdin;
01271980-0000-0000-0000-000005101977	Love and Faith Hospice Services Inc	Love and Faith Hospice Services Inc	ACTIVE	2026-06-04 22:52:53.194961-07	2026-06-04 22:52:53.194961-07	\N	0000000000	\N	\N	MANUAL	DEV	PRODUCTION	f
5224ceb6-e29d-4841-858e-e77f1b67fe65	Tenant A Hospice	Tenant A	ACTIVE	2026-06-05 09:14:09.972625-07	2026-06-05 09:14:09.972625-07	\N	1000000003	\N	\N	\N	\N	PRODUCTION	f
85282f8b-fd5b-45e6-bb82-45394ef7a2f8	Tenant B Hospice	Tenant B	ACTIVE	2026-06-05 09:14:09.972625-07	2026-06-05 09:14:09.972625-07	\N	1000000004	\N	\N	\N	\N	PRODUCTION	f
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	Angela Hospice	Angela Hospice	ACTIVE	2026-06-05 09:14:09.972625-07	2026-06-05 09:14:09.972625-07	\N	1000000001	\N	\N	\N	\N	PRODUCTION	t
bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	Silva Hospice	Silva Hospice	ACTIVE	2026-06-05 09:14:09.972625-07	2026-06-05 09:14:09.972625-07	\N	1000000002	\N	\N	\N	\N	PRODUCTION	t
\.


--
-- Data for Name: user_interface_roles; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.user_interface_roles (id, tenant_id, user_id, interface_id, role_id, assigned_at, revoked_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.users (email, full_name, role, license_number, active, id, created_at, updated_at, created_by, tenant_id, has_admin_access, access_level) FROM stdin;
8a7f8ac0-9a5d-4fa4-8c51-cab431a26a5e+01271980@sns.dev	8a7f8ac0-9a5d-4fa4-8c51-cab431a26a5e (DEV)	DPCS	\N	t	28b66dcb-3ff0-5868-b147-b24f63db74a6	2026-06-19 16:56:48.871021-07	2026-06-29 04:25:35.420647-07	\N	01271980-0000-0000-0000-000005101977	f	FULL_ACCESS
romel@sns.dev	ROMEL SUASON	DPCS	\N	t	8a7f8ac0-9a5d-4fa4-8c51-cab431a26a5e	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	t	FULL_ACCESS
louie@sns.dev	LOUIE PASTOR	ADMIN	\N	t	46eb1c21-25e8-4e86-9f8a-35eb9ca500b9	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	t	FULL_ACCESS
angela@sns.dev	ANGELA SUASON	LVN	\N	t	3696cc99-4d82-43e3-8a19-9fd725a526b2	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	f	FULL_ACCESS
stephen@sns.dev	STEPHEN PINE	MD	\N	t	71389d57-c53d-4fc9-8ad0-24dd7c67122b	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	f	FULL_ACCESS
romel+01271980@sns.dev	romel (DEV)	SW	\N	t	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	2026-06-04 22:53:18.31601-07	2026-06-05 09:06:16.486632-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
romel-clinical+01271980@sns.dev	romel-clinical (DEV)	RN	\N	t	630e6ee8-5fbf-5222-b26a-4570328d3444	2026-06-05 09:07:59.992232-07	2026-06-05 09:07:59.992232-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
devadmin+01271980@sns.dev	devadmin (DEV)	ADMIN	\N	t	86ed90d6-69d5-594f-bff7-f07dbdaeac9c	2026-06-13 11:41:05.263234-07	2026-06-19 16:47:40.788543-07	\N	01271980-0000-0000-0000-000005101977	t	ROLE_BASED
michael@sns.dev	MICHAEL SILVA	CHHA	\N	t	e0b8e8b8-9b05-4da3-8362-875b9f0f7dfd	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
grace@sns.dev	GRACE TRAN	BSW	\N	t	e713e31f-8fd8-4ae8-95bc-ca872db12362	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
jessie@sns.dev	JESSIE SARMIENTO	SC	\N	t	ed1f8707-dec1-4c5e-b185-471cca75b9ea	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
mariel@sns.dev	MARIEL NICOLE DUREN	LCSW	\N	t	5abb216f-1f0a-4417-9fee-211448342cda	2026-06-19 15:38:25.041016-07	2026-06-19 15:38:25.041016-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
david@sns.dev	DAVID RIVERA	RN	\N	t	95981b4d-d9d9-4601-9914-c0f71aa7cc52	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
lisa@sns.dev	LISA NGUYEN	LVN	\N	t	eec28bbe-3f2b-4848-8d26-7c75864c44ce	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
carlos@sns.dev	CARLOS MENDEZ	CHHA	\N	t	29a84e5c-6334-4c8d-b90b-cf48ccc2261c	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
emily@sns.dev	EMILY PARK	MSW	\N	t	bd4e0f79-ef33-4571-9e5b-654ef4362cda	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
maria@sns.dev	MARIA SANTOS	SC	\N	t	26ba0902-4abc-4f79-85c9-dc48a71d296e	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
jonathan@sns.dev	JONATHAN LEE	MSW	\N	t	0f10b15f-adee-4ccf-8067-db17214a1183	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
kristine@sns.dev	KRISTINE REYES	RN	\N	t	7f65cb49-dd86-4bc6-930d-6ac6bbc3cd89	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
andrew@sns.dev	ANDREW COLLINS	QA	\N	t	1419b6b0-d96f-4cac-ae41-a7dc487bcca7	2026-06-19 15:38:39.540606-07	2026-06-19 15:38:39.540606-07	\N	01271980-0000-0000-0000-000005101977	f	ROLE_BASED
\.


--
-- Data for Name: visit_minutes; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.visit_minutes (id, visit_id, discipline, minutes, units, tenant_id, service_date, status, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: visits; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.visits (patient_id, provider_id, visit_type, visit_datetime, status, id, created_at, updated_at, created_by, is_supervisory, finalized_at, finalized_by, chha_poc_id, acuity_state_at_visit, tenant_id, finalized_role_id, finalized_interface_id, visit_discipline, visit_mode, updated_by, deleted_at, deleted_by, form_type, start_time, end_time, documented_minutes, billing_units, is_billable, billing_cycle_id) FROM stdin;
f6774a7f-ef3c-4e29-b716-c3a9cc8c9012	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN	2026-06-24 15:09:38.516876-07	FINALIZED	862e8e53-9060-4ae2-af44-afff8b097154	2026-06-24 15:09:38.516876-07	2026-06-24 15:13:38.216597-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	f	2026-06-24 15:13:38.216597-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
1af2861b-49ca-4c53-90f7-751d67222978	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN	2026-06-24 15:21:40.048-07	FINALIZED	7879abe4-3d62-4da8-9243-eb7a514074bb	2026-06-24 15:21:40.048-07	2026-06-24 15:21:59.299281-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	f	2026-06-24 15:21:59.299281-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8ea3481a-4dbd-4709-be11-bfbb4d4da12c	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN	2026-06-24 16:02:27.317786-07	FINALIZED	f8e7aec1-a019-497e-ab51-50ef5c59fe10	2026-06-24 16:02:27.317786-07	2026-06-24 16:04:31.199322-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	f	2026-06-24 16:04:31.199322-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN	2026-06-24 16:23:05.631364-07	FINALIZED	9d0f1496-fc3e-4b95-a733-722d93174dc0	2026-06-24 16:23:05.631364-07	2026-06-24 16:47:50.491584-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	f	2026-06-24 16:47:50.491584-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8ea3481a-4dbd-4709-be11-bfbb4d4da12c	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	RN	2026-06-24 17:00:58.52175-07	DRAFT	e3ebf064-66dd-40f2-92a9-5edf8fee4c72	2026-06-24 17:00:58.52175-07	2026-06-24 17:00:58.52175-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-24 20:43:59.467657-07	FINALIZED	97f0f7b2-dfd2-456a-8193-47aa421bd94b	2026-06-24 20:43:59.467657-07	2026-06-24 20:46:30.52148-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-24 20:46:30.52148-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-24 21:03:12.40589-07	FINALIZED	4bff4ba5-c00c-4f9e-afe4-98e5c7f175b1	2026-06-24 21:03:12.40589-07	2026-06-24 21:03:35.400259-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-24 21:03:35.400259-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-24 21:44:41.52088-07	DRAFT	790f4629-c251-4220-abdf-0876b9d3e610	2026-06-24 21:44:41.52088-07	2026-06-24 21:44:41.52088-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-25 19:24:58.214471-07	FINALIZED	b96d6e24-84a6-48d0-a1ec-6158c87f77eb	2026-06-25 19:24:58.214471-07	2026-06-25 19:33:50.282463-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-25 19:33:50.282463-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-26 03:36:48.109304-07	FINALIZED	cbc13298-ca80-4bf1-aa84-8136b02fab00	2026-06-26 03:36:48.109304-07	2026-06-26 03:49:35.047465-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-26 03:49:35.047465-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-24 22:40:24.919246-07	FINALIZED	b1517c60-6825-4d10-a385-22d33e058c50	2026-06-24 22:40:24.919246-07	2026-06-24 22:55:34.317869-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-24 22:55:34.317869-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-24 22:59:16.8015-07	FINALIZED	00e5b620-2546-4c70-bfa0-33eaf1a20bcb	2026-06-24 22:59:16.8015-07	2026-06-24 22:59:29.953192-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-24 22:59:29.953192-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-24 23:13:19.640381-07	FINALIZED	738def69-e0dd-4426-85d2-46c3b5b1b561	2026-06-24 23:13:19.640381-07	2026-06-24 23:13:32.586128-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-24 23:13:32.586128-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-24 23:18:05.193949-07	FINALIZED	1f42ca93-5e25-4bf1-8822-b7a06cf1feee	2026-06-24 23:18:05.193949-07	2026-06-24 23:18:37.57863-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-24 23:18:37.57863-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ROUTINE_VISIT	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	LVN	2026-06-24 23:33:12.269087-07	FINALIZED	b00954fc-14c5-43cd-a331-66658d17a886	2026-06-24 23:33:12.269087-07	2026-06-24 23:33:31.661356-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-24 23:33:31.661356-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	LVN	IN_PERSON	\N	\N	\N	ROUTINE_VISIT	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-26 03:54:24.774069-07	FINALIZED	67f6ac2e-1e6b-4a03-a7af-6c80279be394	2026-06-26 03:54:24.774069-07	2026-06-26 03:54:38.338685-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	2026-06-26 03:54:38.338685-07	d7b8a870-891d-56ac-8bf1-c14a151ff7ea	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 17:42:51.201799-07	DRAFT	6333dbb9-04e5-4064-aae1-a26ee9ec6a75	2026-06-28 17:42:51.201799-07	2026-06-28 17:42:51.201799-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 18:02:24.684476-07	DRAFT	8d198a2d-1620-4acf-99c2-f64660022e97	2026-06-28 18:02:24.684476-07	2026-06-28 18:02:24.684476-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 18:05:00.66809-07	DRAFT	28be0c20-149e-4de5-b0e0-f5cbcc449e1b	2026-06-28 18:05:00.66809-07	2026-06-28 18:05:00.66809-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 18:13:50.560197-07	DRAFT	5a0897a5-cd08-47d1-9246-ea8e86999bdb	2026-06-28 18:13:50.560197-07	2026-06-28 18:13:50.560197-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 18:19:50.395385-07	DRAFT	bfa7c066-9dc9-48b6-9f33-5186e7419b24	2026-06-28 18:19:50.395385-07	2026-06-28 18:19:50.395385-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 18:24:43.066238-07	DRAFT	70751c0b-6318-4ce3-9b1b-d05c77a083cc	2026-06-28 18:24:43.066238-07	2026-06-28 18:24:43.066238-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 18:31:20.646844-07	DRAFT	56cc3beb-8fce-42f5-8c87-9d3a5869c955	2026-06-28 18:31:20.646844-07	2026-06-28 18:31:20.646844-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 18:56:47.717457-07	DRAFT	a8de4983-b448-4556-af72-65c5543ef055	2026-06-28 18:56:47.717457-07	2026-06-28 18:56:47.717457-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	SHORT_FORM	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-28 19:15:09.974335-07	DRAFT	5f1040c5-192b-4965-865c-cfe72f3b7ecb	2026-06-28 19:15:09.974335-07	2026-06-28 19:15:09.974335-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
8857c8e3-acd9-4398-87af-eef99a7b6cd5	28b66dcb-3ff0-5868-b147-b24f63db74a6	RN	2026-06-29 03:57:45.174976-07	DRAFT	56e33c56-34dd-4ce4-9183-7d2564460ab7	2026-06-29 03:57:45.174976-07	2026-06-29 03:57:45.174976-07	28b66dcb-3ff0-5868-b147-b24f63db74a6	f	\N	\N	\N	ROUTINE	01271980-0000-0000-0000-000005101977	\N	\N	RN	IN_PERSON	\N	\N	\N	ASSESS	\N	\N	\N	\N	t	\N
\.


--
-- Data for Name: volunteer_hours; Type: TABLE DATA; Schema: public; Owner: sns
--

COPY public.volunteer_hours (id, volunteer_user_id, date, hours, activity_type, supervised_by_user_id, counts_for_5_percent, notes, created_at, updated_at) FROM stdin;
\.


--
-- Name: eligibility_decisions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: sns
--

SELECT pg_catalog.setval('public.eligibility_decisions_id_seq', 1, false);


--
-- Name: billing_organizations billing_organizations_name_unique; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.billing_organizations
    ADD CONSTRAINT billing_organizations_name_unique UNIQUE (name);


--
-- Name: billing_organizations pk_billing_organizations; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.billing_organizations
    ADD CONSTRAINT pk_billing_organizations PRIMARY KEY (id);


--
-- Name: tenant_events pk_tenant_events; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.tenant_events
    ADD CONSTRAINT pk_tenant_events PRIMARY KEY (id);


--
-- Name: tenants pk_tenants; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.tenants
    ADD CONSTRAINT pk_tenants PRIMARY KEY (id);


--
-- Name: user_tenants pk_user_tenants; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.user_tenants
    ADD CONSTRAINT pk_user_tenants PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.users
    ADD CONSTRAINT pk_users PRIMARY KEY (id);


--
-- Name: tenants uq_tenants_schema_name; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.tenants
    ADD CONSTRAINT uq_tenants_schema_name UNIQUE (schema_name);


--
-- Name: tenants uq_tenants_tenant_code; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.tenants
    ADD CONSTRAINT uq_tenants_tenant_code UNIQUE (tenant_code);


--
-- Name: user_tenants uq_user_tenant_membership; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.user_tenants
    ADD CONSTRAINT uq_user_tenant_membership UNIQUE (user_id, tenant_id);


--
-- Name: users uq_users_email; Type: CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.users
    ADD CONSTRAINT uq_users_email UNIQUE (email);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: change_of_condition change_of_condition_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.change_of_condition
    ADD CONSTRAINT change_of_condition_pkey PRIMARY KEY (id);


--
-- Name: communications_logs communications_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.communications_logs
    ADD CONSTRAINT communications_logs_pkey PRIMARY KEY (id);


--
-- Name: diagnoses diagnoses_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnoses
    ADD CONSTRAINT diagnoses_pkey PRIMARY KEY (id);


--
-- Name: document_notifications document_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_notifications
    ADD CONSTRAINT document_notifications_pkey PRIMARY KEY (id);


--
-- Name: external_substances external_substances_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.external_substances
    ADD CONSTRAINT external_substances_pkey PRIMARY KEY (id);


--
-- Name: hope_records hope_records_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_records
    ADD CONSTRAINT hope_records_pkey PRIMARY KEY (id);


--
-- Name: idg_signatures idg_signatures_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_signatures
    ADD CONSTRAINT idg_signatures_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: patient_insurances patient_insurances_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_insurances
    ADD CONSTRAINT patient_insurances_pkey PRIMARY KEY (id);


--
-- Name: accounts pk_accounts; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT pk_accounts PRIMARY KEY (id);


--
-- Name: amendments pk_amendments; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.amendments
    ADD CONSTRAINT pk_amendments PRIMARY KEY (id);


--
-- Name: assessment_discrepancies pk_assessment_discrepancies; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_discrepancies
    ADD CONSTRAINT pk_assessment_discrepancies PRIMARY KEY (id);


--
-- Name: assessment_references pk_assessment_references; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_references
    ADD CONSTRAINT pk_assessment_references PRIMARY KEY (id);


--
-- Name: assessments pk_assessments; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT pk_assessments PRIMARY KEY (id);


--
-- Name: audit_logs pk_audit_logs; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT pk_audit_logs PRIMARY KEY (id);


--
-- Name: authorization_records pk_authorization_records; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.authorization_records
    ADD CONSTRAINT pk_authorization_records PRIMARY KEY (id);


--
-- Name: benefit_periods pk_benefit_periods; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.benefit_periods
    ADD CONSTRAINT pk_benefit_periods PRIMARY KEY (id);


--
-- Name: bereavement_cases pk_bereavement_cases; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_cases
    ADD CONSTRAINT pk_bereavement_cases PRIMARY KEY (id);


--
-- Name: bereavement_declines pk_bereavement_declines; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_declines
    ADD CONSTRAINT pk_bereavement_declines PRIMARY KEY (id);


--
-- Name: bereavement_tasks pk_bereavement_tasks; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_tasks
    ADD CONSTRAINT pk_bereavement_tasks PRIMARY KEY (id);


--
-- Name: billing_cycles pk_billing_cycles; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_cycles
    ADD CONSTRAINT pk_billing_cycles PRIMARY KEY (id);


--
-- Name: billing_snapshot pk_billing_snapshot; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_snapshot
    ADD CONSTRAINT pk_billing_snapshot PRIMARY KEY (id);


--
-- Name: billing_snapshots pk_billing_snapshots; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_snapshots
    ADD CONSTRAINT pk_billing_snapshots PRIMARY KEY (id);


--
-- Name: billing_summaries pk_billing_summaries; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_summaries
    ADD CONSTRAINT pk_billing_summaries PRIMARY KEY (id);


--
-- Name: billing_summary pk_billing_summary; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_summary
    ADD CONSTRAINT pk_billing_summary PRIMARY KEY (id);


--
-- Name: certifications pk_certifications; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.certifications
    ADD CONSTRAINT pk_certifications PRIMARY KEY (id);


--
-- Name: chha_pocs pk_chha_pocs; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_pocs
    ADD CONSTRAINT pk_chha_pocs PRIMARY KEY (id);


--
-- Name: chha_visit_outcomes pk_chha_visit_outcomes; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_visit_outcomes
    ADD CONSTRAINT pk_chha_visit_outcomes PRIMARY KEY (id);


--
-- Name: chha_visit_task_results pk_chha_visit_task_results; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_visit_task_results
    ADD CONSTRAINT pk_chha_visit_task_results PRIMARY KEY (id);


--
-- Name: claim_export_log pk_claim_export_log; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.claim_export_log
    ADD CONSTRAINT pk_claim_export_log PRIMARY KEY (id);


--
-- Name: claim_export_logs pk_claim_export_logs; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.claim_export_logs
    ADD CONSTRAINT pk_claim_export_logs PRIMARY KEY (id);


--
-- Name: clinical_note_versions pk_clinical_note_versions; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_note_versions
    ADD CONSTRAINT pk_clinical_note_versions PRIMARY KEY (id);


--
-- Name: clinical_notes pk_clinical_notes; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT pk_clinical_notes PRIMARY KEY (id);


--
-- Name: continuous_care_events pk_continuous_care_events; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.continuous_care_events
    ADD CONSTRAINT pk_continuous_care_events PRIMARY KEY (id);


--
-- Name: diagnosis_discrepancies pk_diagnosis_discrepancies; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_discrepancies
    ADD CONSTRAINT pk_diagnosis_discrepancies PRIMARY KEY (id);


--
-- Name: diagnosis_reconciliations pk_diagnosis_reconciliations; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_reconciliations
    ADD CONSTRAINT pk_diagnosis_reconciliations PRIMARY KEY (id);


--
-- Name: diagnosis_sources pk_diagnosis_sources; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_sources
    ADD CONSTRAINT pk_diagnosis_sources PRIMARY KEY (id);


--
-- Name: discharge_reasons pk_discharge_reasons; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.discharge_reasons
    ADD CONSTRAINT pk_discharge_reasons PRIMARY KEY (code);


--
-- Name: discharges pk_discharges; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.discharges
    ADD CONSTRAINT pk_discharges PRIMARY KEY (id);


--
-- Name: document_idg_resolution pk_document_idg_resolution; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_idg_resolution
    ADD CONSTRAINT pk_document_idg_resolution PRIMARY KEY (document_id);


--
-- Name: document_records pk_document_records; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_records
    ADD CONSTRAINT pk_document_records PRIMARY KEY (id);


--
-- Name: drug_aliases pk_drug_aliases; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.drug_aliases
    ADD CONSTRAINT pk_drug_aliases PRIMARY KEY (alias_text);


--
-- Name: dx_primary_policies pk_dx_primary_policies; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.dx_primary_policies
    ADD CONSTRAINT pk_dx_primary_policies PRIMARY KEY (id);


--
-- Name: dx_primary_policy pk_dx_primary_policy; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.dx_primary_policy
    ADD CONSTRAINT pk_dx_primary_policy PRIMARY KEY (id);


--
-- Name: eligibility_assessments pk_eligibility_assessments; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.eligibility_assessments
    ADD CONSTRAINT pk_eligibility_assessments PRIMARY KEY (id);


--
-- Name: eligibility_decisions pk_eligibility_decisions; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.eligibility_decisions
    ADD CONSTRAINT pk_eligibility_decisions PRIMARY KEY (id);


--
-- Name: eligibility_rulesets pk_eligibility_rulesets; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.eligibility_rulesets
    ADD CONSTRAINT pk_eligibility_rulesets PRIMARY KEY (id);


--
-- Name: f2f_encounters pk_f2f_encounters; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.f2f_encounters
    ADD CONSTRAINT pk_f2f_encounters PRIMARY KEY (id);


--
-- Name: form_modules pk_form_modules; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_modules
    ADD CONSTRAINT pk_form_modules PRIMARY KEY (id);


--
-- Name: form_package_modules pk_form_package_modules; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_package_modules
    ADD CONSTRAINT pk_form_package_modules PRIMARY KEY (id);


--
-- Name: form_registry pk_form_registry; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_registry
    ADD CONSTRAINT pk_form_registry PRIMARY KEY (id);


--
-- Name: forms pk_forms; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.forms
    ADD CONSTRAINT pk_forms PRIMARY KEY (id);


--
-- Name: gip_periods pk_gip_periods; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.gip_periods
    ADD CONSTRAINT pk_gip_periods PRIMARY KEY (id);


--
-- Name: guardrail_policies pk_guardrail_policies; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.guardrail_policies
    ADD CONSTRAINT pk_guardrail_policies PRIMARY KEY (id);


--
-- Name: hope_symptom_assessments pk_hope_symptom_assessments; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_symptom_assessments
    ADD CONSTRAINT pk_hope_symptom_assessments PRIMARY KEY (id);


--
-- Name: hope_symptom_followups pk_hope_symptom_followups; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_symptom_followups
    ADD CONSTRAINT pk_hope_symptom_followups PRIMARY KEY (id);


--
-- Name: hope_symptom_visits pk_hope_symptom_visits; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_symptom_visits
    ADD CONSTRAINT pk_hope_symptom_visits PRIMARY KEY (id);


--
-- Name: idg_attendance pk_idg_attendance; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_attendance
    ADD CONSTRAINT pk_idg_attendance PRIMARY KEY (id);


--
-- Name: idg_justification_notes pk_idg_justification_notes; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_justification_notes
    ADD CONSTRAINT pk_idg_justification_notes PRIMARY KEY (id);


--
-- Name: idg_md_attestations pk_idg_md_attestations; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_md_attestations
    ADD CONSTRAINT pk_idg_md_attestations PRIMARY KEY (attestation_id);


--
-- Name: idg_meetings pk_idg_meetings; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_meetings
    ADD CONSTRAINT pk_idg_meetings PRIMARY KEY (idg_id);


--
-- Name: idg_notes pk_idg_notes; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_notes
    ADD CONSTRAINT pk_idg_notes PRIMARY KEY (idg_note_id);


--
-- Name: idg_participants pk_idg_participants; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_participants
    ADD CONSTRAINT pk_idg_participants PRIMARY KEY (participant_id);


--
-- Name: idg_reviews pk_idg_reviews; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_reviews
    ADD CONSTRAINT pk_idg_reviews PRIMARY KEY (id);


--
-- Name: idg_session pk_idg_session; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_session
    ADD CONSTRAINT pk_idg_session PRIMARY KEY (id);


--
-- Name: incident_reports pk_incident_reports; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.incident_reports
    ADD CONSTRAINT pk_incident_reports PRIMARY KEY (id);


--
-- Name: interfaces pk_interfaces; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.interfaces
    ADD CONSTRAINT pk_interfaces PRIMARY KEY (id);


--
-- Name: med_reconciliation_audit_logs pk_med_reconciliation_audit_logs; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_audit_logs
    ADD CONSTRAINT pk_med_reconciliation_audit_logs PRIMARY KEY (id);


--
-- Name: med_reconciliation_imports pk_med_reconciliation_imports; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_imports
    ADD CONSTRAINT pk_med_reconciliation_imports PRIMARY KEY (id);


--
-- Name: med_reconciliation_items pk_med_reconciliation_items; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_items
    ADD CONSTRAINT pk_med_reconciliation_items PRIMARY KEY (id);


--
-- Name: medications pk_medications; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT pk_medications PRIMARY KEY (id);


--
-- Name: orders_snapshot pk_orders_snapshot; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.orders_snapshot
    ADD CONSTRAINT pk_orders_snapshot PRIMARY KEY (id);


--
-- Name: orders_snapshots pk_orders_snapshots; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.orders_snapshots
    ADD CONSTRAINT pk_orders_snapshots PRIMARY KEY (id);


--
-- Name: patient_allergies pk_patient_allergies; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT pk_patient_allergies PRIMARY KEY (id);


--
-- Name: patient_allergy_profiles pk_patient_allergy_profiles; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_allergy_profiles
    ADD CONSTRAINT pk_patient_allergy_profiles PRIMARY KEY (id);


--
-- Name: patient_assignments pk_patient_assignments; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_assignments
    ADD CONSTRAINT pk_patient_assignments PRIMARY KEY (id);


--
-- Name: patient_payers pk_patient_payers; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_payers
    ADD CONSTRAINT pk_patient_payers PRIMARY KEY (id);


--
-- Name: patient_pos pk_patient_pos; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_pos
    ADD CONSTRAINT pk_patient_pos PRIMARY KEY (id);


--
-- Name: patients pk_patients; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT pk_patients PRIMARY KEY (id);


--
-- Name: payer_contracts pk_payer_contracts; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.payer_contracts
    ADD CONSTRAINT pk_payer_contracts PRIMARY KEY (id);


--
-- Name: payers pk_payers; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.payers
    ADD CONSTRAINT pk_payers PRIMARY KEY (id);


--
-- Name: plan_of_care pk_plan_of_care; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care
    ADD CONSTRAINT pk_plan_of_care PRIMARY KEY (id);


--
-- Name: plan_of_care_approvals pk_plan_of_care_approvals; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_approvals
    ADD CONSTRAINT pk_plan_of_care_approvals PRIMARY KEY (id);


--
-- Name: plan_of_care_goals pk_plan_of_care_goals; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_goals
    ADD CONSTRAINT pk_plan_of_care_goals PRIMARY KEY (id);


--
-- Name: plan_of_care_versions pk_plan_of_care_versions; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_versions
    ADD CONSTRAINT pk_plan_of_care_versions PRIMARY KEY (id);


--
-- Name: poc_problem_templates pk_poc_problem_templates; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.poc_problem_templates
    ADD CONSTRAINT pk_poc_problem_templates PRIMARY KEY (id);


--
-- Name: regulatory_report_artifacts pk_regulatory_report_artifacts; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_artifacts
    ADD CONSTRAINT pk_regulatory_report_artifacts PRIMARY KEY (id);


--
-- Name: regulatory_report_metrics pk_regulatory_report_metrics; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_metrics
    ADD CONSTRAINT pk_regulatory_report_metrics PRIMARY KEY (id);


--
-- Name: regulatory_report_sections pk_regulatory_report_sections; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_sections
    ADD CONSTRAINT pk_regulatory_report_sections PRIMARY KEY (id);


--
-- Name: regulatory_reports pk_regulatory_reports; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_reports
    ADD CONSTRAINT pk_regulatory_reports PRIMARY KEY (id);


--
-- Name: respite_periods pk_respite_periods; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.respite_periods
    ADD CONSTRAINT pk_respite_periods PRIMARY KEY (id);


--
-- Name: rn_recert_assessments pk_rn_recert_assessments; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.rn_recert_assessments
    ADD CONSTRAINT pk_rn_recert_assessments PRIMARY KEY (id);


--
-- Name: roles pk_roles; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT pk_roles PRIMARY KEY (id);


--
-- Name: runbooks pk_runbooks; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.runbooks
    ADD CONSTRAINT pk_runbooks PRIMARY KEY (id);


--
-- Name: safety_assessments pk_safety_assessments; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.safety_assessments
    ADD CONSTRAINT pk_safety_assessments PRIMARY KEY (id);


--
-- Name: security_activity_events pk_security_activity_events; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.security_activity_events
    ADD CONSTRAINT pk_security_activity_events PRIMARY KEY (id);


--
-- Name: sfv_requirements pk_sfv_requirements; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.sfv_requirements
    ADD CONSTRAINT pk_sfv_requirements PRIMARY KEY (id);


--
-- Name: survey_access pk_survey_access; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT pk_survey_access PRIMARY KEY (id);


--
-- Name: tasks pk_tasks; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT pk_tasks PRIMARY KEY (id);


--
-- Name: tenant_rule_toggles pk_tenant_rule_toggles; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tenant_rule_toggles
    ADD CONSTRAINT pk_tenant_rule_toggles PRIMARY KEY (id);


--
-- Name: tenants pk_tenants; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT pk_tenants PRIMARY KEY (id);


--
-- Name: user_interface_roles pk_user_interface_roles; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.user_interface_roles
    ADD CONSTRAINT pk_user_interface_roles PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT pk_users PRIMARY KEY (id);


--
-- Name: visit_minutes pk_visit_minutes; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visit_minutes
    ADD CONSTRAINT pk_visit_minutes PRIMARY KEY (id);


--
-- Name: visits pk_visits; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT pk_visits PRIMARY KEY (id);


--
-- Name: volunteer_hours pk_volunteer_hours; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.volunteer_hours
    ADD CONSTRAINT pk_volunteer_hours PRIMARY KEY (id);


--
-- Name: refusals refusals_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.refusals
    ADD CONSTRAINT refusals_pkey PRIMARY KEY (id);


--
-- Name: service_coverage_decisions service_coverage_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.service_coverage_decisions
    ADD CONSTRAINT service_coverage_decisions_pkey PRIMARY KEY (id);


--
-- Name: billing_summaries uq_billing_summary_patient_cycle; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_summaries
    ADD CONSTRAINT uq_billing_summary_patient_cycle UNIQUE (patient_id, billing_cycle_id);


--
-- Name: chha_visit_outcomes uq_chha_visit_outcomes_visit_id; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_visit_outcomes
    ADD CONSTRAINT uq_chha_visit_outcomes_visit_id UNIQUE (visit_id);


--
-- Name: clinical_note_versions uq_clinical_note_versions_note_version; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_note_versions
    ADD CONSTRAINT uq_clinical_note_versions_note_version UNIQUE (clinical_note_id, version_number);


--
-- Name: dx_primary_policy uq_dx_primary_policy_tenant_code_pattern; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.dx_primary_policy
    ADD CONSTRAINT uq_dx_primary_policy_tenant_code_pattern UNIQUE (tenant_id, code_pattern);


--
-- Name: dx_primary_policy uq_dx_primary_policy_tenant_pattern; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.dx_primary_policy
    ADD CONSTRAINT uq_dx_primary_policy_tenant_pattern UNIQUE (tenant_id, code_pattern, pattern_type);


--
-- Name: form_modules uq_form_modules_module_key; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_modules
    ADD CONSTRAINT uq_form_modules_module_key UNIQUE (module_key);


--
-- Name: form_package_modules uq_form_package_modules_registry_module; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_package_modules
    ADD CONSTRAINT uq_form_package_modules_registry_module UNIQUE (form_registry_id, module_id);


--
-- Name: form_registry uq_form_registry_form_key; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_registry
    ADD CONSTRAINT uq_form_registry_form_key UNIQUE (form_key);


--
-- Name: form_registry uq_form_registry_unique_active; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_registry
    ADD CONSTRAINT uq_form_registry_unique_active UNIQUE (form_type, discipline, level_of_care, is_active);


--
-- Name: idg_attendance uq_idg_attendance_session_user; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_attendance
    ADD CONSTRAINT uq_idg_attendance_session_user UNIQUE (idg_session_id, user_id, discipline);


--
-- Name: idg_signatures uq_idg_signature_per_discipline; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_signatures
    ADD CONSTRAINT uq_idg_signature_per_discipline UNIQUE (idg_review_id, discipline);


--
-- Name: idg_signatures uq_idg_signatures_session_user_role; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_signatures
    ADD CONSTRAINT uq_idg_signatures_session_user_role UNIQUE (idg_session_id, user_id, signature_role);


--
-- Name: interfaces uq_interfaces_name; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.interfaces
    ADD CONSTRAINT uq_interfaces_name UNIQUE (name);


--
-- Name: patient_allergy_profiles uq_patient_allergy_profiles_patient_id; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_allergy_profiles
    ADD CONSTRAINT uq_patient_allergy_profiles_patient_id UNIQUE (patient_id);


--
-- Name: patients uq_patients_mrn; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT uq_patients_mrn UNIQUE (mrn);


--
-- Name: plan_of_care_versions uq_plan_of_care_versions_plan_version; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_versions
    ADD CONSTRAINT uq_plan_of_care_versions_plan_version UNIQUE (plan_of_care_id, version_number);


--
-- Name: regulatory_report_metrics uq_regulatory_report_metrics_report_section_key; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_metrics
    ADD CONSTRAINT uq_regulatory_report_metrics_report_section_key UNIQUE (report_id, section_id, metric_key);


--
-- Name: roles uq_roles_interface_name; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT uq_roles_interface_name UNIQUE (interface_id, name);


--
-- Name: survey_access uq_survey_access_token_jti; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT uq_survey_access_token_jti UNIQUE (token_jti);


--
-- Name: tenant_rule_toggles uq_tenant_rule_toggle_one; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tenant_rule_toggles
    ADD CONSTRAINT uq_tenant_rule_toggle_one UNIQUE (tenant_id, workflow, rule_id);


--
-- Name: users uq_users_email; Type: CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_email UNIQUE (email);


--
-- Name: idx_benefit_periods_current; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_benefit_periods_current ON public.benefit_periods USING btree (is_current);


--
-- Name: idx_benefit_periods_dates; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_benefit_periods_dates ON public.benefit_periods USING btree (start_date, end_date);


--
-- Name: idx_benefit_periods_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_benefit_periods_patient ON public.benefit_periods USING btree (patient_id);


--
-- Name: idx_clinical_note_countersign; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_clinical_note_countersign ON public.clinical_notes USING btree (countersigned_by);


--
-- Name: idx_patient_insurances_active; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_patient_insurances_active ON public.patient_insurances USING btree (is_active);


--
-- Name: idx_patient_insurances_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_patient_insurances_patient_id ON public.patient_insurances USING btree (patient_id);


--
-- Name: idx_patient_insurances_scope; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_patient_insurances_scope ON public.patient_insurances USING btree (coverage_scope);


--
-- Name: idx_patient_insurances_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_patient_insurances_tenant_id ON public.patient_insurances USING btree (tenant_id);


--
-- Name: idx_refusals_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_refusals_patient ON public.refusals USING btree (patient_id);


--
-- Name: idx_refusals_tenant; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_refusals_tenant ON public.refusals USING btree (tenant_id);


--
-- Name: idx_tasks_benefit_period; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_tasks_benefit_period ON public.tasks USING btree (benefit_period_id);


--
-- Name: idx_tasks_completed_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_tasks_completed_at ON public.tasks USING btree (completed_at);


--
-- Name: idx_tasks_completion_reference; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_tasks_completion_reference ON public.tasks USING btree (completion_reference_type, completion_reference_id);


--
-- Name: idx_tasks_due_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_tasks_due_date ON public.tasks USING btree (due_date);


--
-- Name: idx_tasks_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_tasks_patient ON public.tasks USING btree (patient_id);


--
-- Name: idx_tasks_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX idx_tasks_status ON public.tasks USING btree (status);


--
-- Name: ix_amendments_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_amendments_created_by ON public.amendments USING btree (created_by);


--
-- Name: ix_assessment_discrepancies_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_discrepancies_created_by ON public.assessment_discrepancies USING btree (created_by);


--
-- Name: ix_assessment_discrepancies_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_discrepancies_patient_id ON public.assessment_discrepancies USING btree (patient_id);


--
-- Name: ix_assessment_discrepancies_patient_resolved_domain; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_discrepancies_patient_resolved_domain ON public.assessment_discrepancies USING btree (patient_id, resolved, domain);


--
-- Name: ix_assessment_discrepancies_resolved; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_discrepancies_resolved ON public.assessment_discrepancies USING btree (resolved);


--
-- Name: ix_assessment_references_assessment_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_references_assessment_id ON public.assessment_references USING btree (assessment_id);


--
-- Name: ix_assessment_references_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_references_created_by ON public.assessment_references USING btree (created_by);


--
-- Name: ix_assessment_references_referenced_assessment_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_references_referenced_assessment_id ON public.assessment_references USING btree (referenced_assessment_id);


--
-- Name: ix_assessment_references_referenced_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessment_references_referenced_id ON public.assessment_references USING btree (referenced_assessment_id);


--
-- Name: ix_assessments_assessment_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessments_assessment_type ON public.assessments USING btree (assessment_type);


--
-- Name: ix_assessments_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessments_created_by ON public.assessments USING btree (created_by);


--
-- Name: ix_assessments_discipline; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessments_discipline ON public.assessments USING btree (discipline);


--
-- Name: ix_assessments_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessments_patient_id ON public.assessments USING btree (patient_id);


--
-- Name: ix_assessments_patient_type_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_assessments_patient_type_status ON public.assessments USING btree (patient_id, assessment_type, status);


--
-- Name: ix_audit_logs_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_audit_logs_created_by ON public.audit_logs USING btree (created_by);


--
-- Name: ix_authorization_records_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_authorization_records_patient_id ON public.authorization_records USING btree (patient_id);


--
-- Name: ix_benefit_periods_benefit_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_benefit_type ON public.benefit_periods USING btree (benefit_type);


--
-- Name: ix_benefit_periods_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_created_by ON public.benefit_periods USING btree (created_by);


--
-- Name: ix_benefit_periods_end_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_end_date ON public.benefit_periods USING btree (end_date);


--
-- Name: ix_benefit_periods_is_current; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_is_current ON public.benefit_periods USING btree (is_current);


--
-- Name: ix_benefit_periods_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_patient_id ON public.benefit_periods USING btree (patient_id);


--
-- Name: ix_benefit_periods_period_number; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_period_number ON public.benefit_periods USING btree (period_number);


--
-- Name: ix_benefit_periods_start_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_start_date ON public.benefit_periods USING btree (start_date);


--
-- Name: ix_benefit_periods_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_benefit_periods_tenant_id ON public.benefit_periods USING btree (tenant_id);


--
-- Name: ix_bereavement_cases_end_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_cases_end_date ON public.bereavement_cases USING btree (end_date);


--
-- Name: ix_bereavement_cases_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_cases_patient_id ON public.bereavement_cases USING btree (patient_id);


--
-- Name: ix_bereavement_cases_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_cases_status ON public.bereavement_cases USING btree (status);


--
-- Name: ix_bereavement_declines_role; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_declines_role ON public.bereavement_declines USING btree (declined_role);


--
-- Name: ix_bereavement_declines_task_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_declines_task_id ON public.bereavement_declines USING btree (bereavement_task_id);


--
-- Name: ix_bereavement_tasks_case_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_tasks_case_id ON public.bereavement_tasks USING btree (bereavement_case_id);


--
-- Name: ix_bereavement_tasks_due_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_tasks_due_date ON public.bereavement_tasks USING btree (due_date);


--
-- Name: ix_bereavement_tasks_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_tasks_status ON public.bereavement_tasks USING btree (status);


--
-- Name: ix_bereavement_tasks_subtype; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_bereavement_tasks_subtype ON public.bereavement_tasks USING btree (task_subtype);


--
-- Name: ix_billing_cycle_tenant_dates; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_cycle_tenant_dates ON public.billing_cycles USING btree (tenant_id, start_date, end_date);


--
-- Name: ix_billing_cycles_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_cycles_tenant_id ON public.billing_cycles USING btree (tenant_id);


--
-- Name: ix_billing_snapshot_patient_created; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_snapshot_patient_created ON public.billing_snapshots USING btree (patient_id, created_at);


--
-- Name: ix_billing_snapshot_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_snapshot_patient_id ON public.billing_snapshot USING btree (patient_id);


--
-- Name: ix_billing_snapshot_tenant_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_snapshot_tenant_type ON public.billing_snapshots USING btree (tenant_id, snapshot_type);


--
-- Name: ix_billing_summary_billing_cycle_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_summary_billing_cycle_id ON public.billing_summary USING btree (billing_cycle_id);


--
-- Name: ix_billing_summary_cycle; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_summary_cycle ON public.billing_summaries USING btree (billing_cycle_id);


--
-- Name: ix_billing_summary_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_summary_patient_id ON public.billing_summary USING btree (patient_id);


--
-- Name: ix_billing_summary_patient_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_billing_summary_patient_status ON public.billing_summaries USING btree (patient_id, status);


--
-- Name: ix_certifications_benefit_period_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_certifications_benefit_period_id ON public.certifications USING btree (benefit_period_id);


--
-- Name: ix_certifications_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_certifications_patient_id ON public.certifications USING btree (patient_id);


--
-- Name: ix_chha_pocs_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_pocs_patient_id ON public.chha_pocs USING btree (patient_id);


--
-- Name: ix_chha_pocs_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_pocs_status ON public.chha_pocs USING btree (status);


--
-- Name: ix_chha_visit_outcomes_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_visit_outcomes_patient_id ON public.chha_visit_outcomes USING btree (patient_id);


--
-- Name: ix_chha_visit_outcomes_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_visit_outcomes_tenant_id ON public.chha_visit_outcomes USING btree (tenant_id);


--
-- Name: ix_chha_visit_outcomes_visit_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_visit_outcomes_visit_id ON public.chha_visit_outcomes USING btree (visit_id);


--
-- Name: ix_chha_visit_task_results_outcome_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_visit_task_results_outcome_id ON public.chha_visit_task_results USING btree (outcome_id);


--
-- Name: ix_chha_visit_task_results_section_code; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_visit_task_results_section_code ON public.chha_visit_task_results USING btree (section_code);


--
-- Name: ix_chha_visit_task_results_task_code; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_chha_visit_task_results_task_code ON public.chha_visit_task_results USING btree (task_code);


--
-- Name: ix_claim_export_patient_cycle; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_claim_export_patient_cycle ON public.claim_export_logs USING btree (patient_id, billing_cycle_id);


--
-- Name: ix_claim_export_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_claim_export_status ON public.claim_export_logs USING btree (status);


--
-- Name: ix_clinical_note_versions_clinical_note_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_clinical_note_versions_clinical_note_id ON public.clinical_note_versions USING btree (clinical_note_id);


--
-- Name: ix_clinical_note_versions_note_active; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_clinical_note_versions_note_active ON public.clinical_note_versions USING btree (clinical_note_id, is_active);


--
-- Name: ix_clinical_notes_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_clinical_notes_created_by ON public.clinical_notes USING btree (created_by);


--
-- Name: ix_continuous_care_events_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_continuous_care_events_patient_id ON public.continuous_care_events USING btree (patient_id);


--
-- Name: ix_continuous_care_patient_service_dates; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_continuous_care_patient_service_dates ON public.continuous_care_events USING btree (patient_id, service_level, start_date, end_date);


--
-- Name: ix_contract_payer; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_contract_payer ON public.payer_contracts USING btree (payer_id);


--
-- Name: ix_discharges_effective_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_discharges_effective_at ON public.discharges USING btree (effective_at);


--
-- Name: ix_discharges_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_discharges_patient_id ON public.discharges USING btree (patient_id);


--
-- Name: ix_discharges_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_discharges_status ON public.discharges USING btree (status);


--
-- Name: ix_document_idg_resolution_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_document_idg_resolution_created_by ON public.document_idg_resolution USING btree (created_by);


--
-- Name: ix_document_idg_resolution_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_document_idg_resolution_tenant_id ON public.document_idg_resolution USING btree (tenant_id);


--
-- Name: ix_document_records_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_document_records_created_by ON public.document_records USING btree (created_by);


--
-- Name: ix_document_records_flagged; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_document_records_flagged ON public.document_records USING btree (is_flagged);


--
-- Name: ix_document_records_tenant_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_document_records_tenant_patient ON public.document_records USING btree (tenant_id, patient_id);


--
-- Name: ix_document_records_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_document_records_type ON public.document_records USING btree (document_type);


--
-- Name: ix_drug_aliases_canonical_text; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_drug_aliases_canonical_text ON public.drug_aliases USING btree (canonical_text);


--
-- Name: ix_drug_aliases_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_drug_aliases_created_by ON public.drug_aliases USING btree (created_by);


--
-- Name: ix_dx_disc_patient_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_dx_disc_patient_status ON public.diagnosis_discrepancies USING btree (patient_id, status);


--
-- Name: ix_dx_patient_active; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_dx_patient_active ON public.diagnosis_sources USING btree (patient_id, is_active);


--
-- Name: ix_dx_patient_source_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_dx_patient_source_type ON public.diagnosis_sources USING btree (patient_id, source, dx_type);


--
-- Name: ix_dx_primary_policies_code; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ix_dx_primary_policies_code ON public.dx_primary_policies USING btree (diagnosis_code);


--
-- Name: ix_dx_primary_policies_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_dx_primary_policies_created_by ON public.dx_primary_policies USING btree (created_by);


--
-- Name: ix_dx_primary_policy_pattern; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_dx_primary_policy_pattern ON public.dx_primary_policy USING btree (code_pattern);


--
-- Name: ix_dx_primary_policy_tenant; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_dx_primary_policy_tenant ON public.dx_primary_policy USING btree (tenant_id);


--
-- Name: ix_dx_recon_discrepancy; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_dx_recon_discrepancy ON public.diagnosis_reconciliations USING btree (discrepancy_id);


--
-- Name: ix_eligibility_assessments_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_eligibility_assessments_created_by ON public.eligibility_assessments USING btree (created_by);


--
-- Name: ix_eligibility_decisions_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_eligibility_decisions_created_by ON public.eligibility_decisions USING btree (created_by);


--
-- Name: ix_eligibility_rulesets_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_eligibility_rulesets_created_by ON public.eligibility_rulesets USING btree (created_by);


--
-- Name: ix_f2f_encounters_benefit_period_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_f2f_encounters_benefit_period_id ON public.f2f_encounters USING btree (benefit_period_id);


--
-- Name: ix_f2f_encounters_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_f2f_encounters_patient_id ON public.f2f_encounters USING btree (patient_id);


--
-- Name: ix_form_modules_module_key; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_modules_module_key ON public.form_modules USING btree (module_key);


--
-- Name: ix_form_package_modules_form_registry_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_package_modules_form_registry_id ON public.form_package_modules USING btree (form_registry_id);


--
-- Name: ix_form_package_modules_module_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_package_modules_module_id ON public.form_package_modules USING btree (module_id);


--
-- Name: ix_form_registry_discipline; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_registry_discipline ON public.form_registry USING btree (discipline);


--
-- Name: ix_form_registry_form_family; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_registry_form_family ON public.form_registry USING btree (form_family);


--
-- Name: ix_form_registry_form_key; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_registry_form_key ON public.form_registry USING btree (form_key);


--
-- Name: ix_form_registry_form_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_registry_form_type ON public.form_registry USING btree (form_type);


--
-- Name: ix_form_registry_level_of_care; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_registry_level_of_care ON public.form_registry USING btree (level_of_care);


--
-- Name: ix_form_registry_resolution; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_form_registry_resolution ON public.form_registry USING btree (discipline, form_type, level_of_care);


--
-- Name: ix_forms_form_registry_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_forms_form_registry_id ON public.forms USING btree (form_registry_id);


--
-- Name: ix_forms_visit_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_forms_visit_id ON public.forms USING btree (visit_id);


--
-- Name: ix_gip_period_patient_service_dates; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_gip_period_patient_service_dates ON public.gip_periods USING btree (patient_id, service_level, start_date, end_date);


--
-- Name: ix_gip_periods_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_gip_periods_patient_id ON public.gip_periods USING btree (patient_id);


--
-- Name: ix_guardrail_policies_is_active; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_guardrail_policies_is_active ON public.guardrail_policies USING btree (is_active);


--
-- Name: ix_guardrail_policies_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_guardrail_policies_tenant_id ON public.guardrail_policies USING btree (tenant_id);


--
-- Name: ix_idg_attendance_session_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_attendance_session_id ON public.idg_attendance USING btree (idg_session_id);


--
-- Name: ix_idg_md_attestations_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_md_attestations_created_by ON public.idg_md_attestations USING btree (created_by);


--
-- Name: ix_idg_md_attestations_idg_review_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_md_attestations_idg_review_id ON public.idg_md_attestations USING btree (idg_review_id);


--
-- Name: ix_idg_notes_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_notes_created_by ON public.idg_notes USING btree (created_by);


--
-- Name: ix_idg_notes_idg_review_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_notes_idg_review_id ON public.idg_notes USING btree (idg_review_id);


--
-- Name: ix_idg_reviews_benefit_period_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_reviews_benefit_period_id ON public.idg_reviews USING btree (benefit_period_id);


--
-- Name: ix_idg_reviews_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_reviews_created_by ON public.idg_reviews USING btree (created_by);


--
-- Name: ix_idg_session_plan_of_care_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_session_plan_of_care_id ON public.idg_session USING btree (plan_of_care_id);


--
-- Name: ix_idg_session_started_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_session_started_at ON public.idg_session USING btree (started_at);


--
-- Name: ix_idg_signatures_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_signatures_created_by ON public.idg_signatures USING btree (created_by);


--
-- Name: ix_idg_signatures_idg_review_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_signatures_idg_review_id ON public.idg_signatures USING btree (idg_review_id);


--
-- Name: ix_idg_signatures_session_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_idg_signatures_session_id ON public.idg_signatures USING btree (idg_session_id);


--
-- Name: ix_incident_reports_clinical_note_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_incident_reports_clinical_note_id ON public.incident_reports USING btree (clinical_note_id);


--
-- Name: ix_incident_reports_incident_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_incident_reports_incident_date ON public.incident_reports USING btree (incident_date);


--
-- Name: ix_incident_reports_incident_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_incident_reports_incident_type ON public.incident_reports USING btree (incident_type);


--
-- Name: ix_incident_reports_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_incident_reports_patient_id ON public.incident_reports USING btree (patient_id);


--
-- Name: ix_incident_reports_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_incident_reports_tenant_id ON public.incident_reports USING btree (tenant_id);


--
-- Name: ix_interfaces_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_interfaces_created_by ON public.interfaces USING btree (created_by);


--
-- Name: ix_interfaces_name; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ix_interfaces_name ON public.interfaces USING btree (name);


--
-- Name: ix_md_attestations_idg_review_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_md_attestations_idg_review_id ON public.idg_md_attestations USING btree (idg_review_id);


--
-- Name: ix_med_recon_audit_logs_import_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_recon_audit_logs_import_id ON public.med_reconciliation_audit_logs USING btree (import_id);


--
-- Name: ix_med_recon_audit_logs_item_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_recon_audit_logs_item_id ON public.med_reconciliation_audit_logs USING btree (item_id);


--
-- Name: ix_med_recon_audit_logs_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_recon_audit_logs_patient_id ON public.med_reconciliation_audit_logs USING btree (patient_id);


--
-- Name: ix_med_recon_audit_logs_signature_hash; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_recon_audit_logs_signature_hash ON public.med_reconciliation_audit_logs USING btree (signature_hash);


--
-- Name: ix_med_recon_audit_logs_stage_event; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_recon_audit_logs_stage_event ON public.med_reconciliation_audit_logs USING btree (stage, event_type);


--
-- Name: ix_med_reconciliation_imports_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_imports_patient_id ON public.med_reconciliation_imports USING btree (patient_id);


--
-- Name: ix_med_reconciliation_imports_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_imports_status ON public.med_reconciliation_imports USING btree (status);


--
-- Name: ix_med_reconciliation_imports_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_imports_tenant_id ON public.med_reconciliation_imports USING btree (tenant_id);


--
-- Name: ix_med_reconciliation_imports_uploaded_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_imports_uploaded_at ON public.med_reconciliation_imports USING btree (uploaded_at);


--
-- Name: ix_med_reconciliation_items_comparison_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_comparison_status ON public.med_reconciliation_items USING btree (comparison_status);


--
-- Name: ix_med_reconciliation_items_import_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_import_id ON public.med_reconciliation_items USING btree (import_id);


--
-- Name: ix_med_reconciliation_items_import_list_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_import_list_type ON public.med_reconciliation_items USING btree (import_id, list_type);


--
-- Name: ix_med_reconciliation_items_is_critical_reaction; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_is_critical_reaction ON public.med_reconciliation_items USING btree (is_critical_reaction);


--
-- Name: ix_med_reconciliation_items_matched_med; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_matched_med ON public.med_reconciliation_items USING btree (matched_medication_id);


--
-- Name: ix_med_reconciliation_items_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_patient_id ON public.med_reconciliation_items USING btree (patient_id);


--
-- Name: ix_med_reconciliation_items_patient_pending_signature; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_patient_pending_signature ON public.med_reconciliation_items USING btree (patient_id, review_status, signature_hash);


--
-- Name: ix_med_reconciliation_items_review_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_review_status ON public.med_reconciliation_items USING btree (review_status);


--
-- Name: ix_med_reconciliation_items_signature_hash; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_signature_hash ON public.med_reconciliation_items USING btree (signature_hash);


--
-- Name: ix_med_reconciliation_items_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_med_reconciliation_items_tenant_id ON public.med_reconciliation_items USING btree (tenant_id);


--
-- Name: ix_medications_canonical_name; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_medications_canonical_name ON public.medications USING btree (canonical_name);


--
-- Name: ix_medications_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_medications_created_by ON public.medications USING btree (created_by);


--
-- Name: ix_orders_diagnosis_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_diagnosis_id ON public.orders USING btree (diagnosis_id);


--
-- Name: ix_orders_discontinued_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_discontinued_at ON public.orders USING btree (discontinued_at);


--
-- Name: ix_orders_medication_class; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_medication_class ON public.orders USING btree (medication_class);


--
-- Name: ix_orders_order_category; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_order_category ON public.orders USING btree (order_category);


--
-- Name: ix_orders_snapshot_patient_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_snapshot_patient_date ON public.orders_snapshots USING btree (patient_id, effective_date);


--
-- Name: ix_orders_snapshot_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_snapshot_patient_id ON public.orders_snapshot USING btree (patient_id);


--
-- Name: ix_orders_snapshot_tenant; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_snapshot_tenant ON public.orders_snapshots USING btree (tenant_id);


--
-- Name: ix_orders_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_orders_status ON public.orders USING btree (status);


--
-- Name: ix_patient_allergies_patient_active; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patient_allergies_patient_active ON public.patient_allergies USING btree (patient_id, is_active);


--
-- Name: ix_patient_assignments_active_unique; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ix_patient_assignments_active_unique ON public.patient_assignments USING btree (tenant_id, patient_id, discipline, status);


--
-- Name: ix_patient_assignments_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patient_assignments_patient ON public.patient_assignments USING btree (patient_id);


--
-- Name: ix_patient_payers_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patient_payers_patient_id ON public.patient_payers USING btree (patient_id);


--
-- Name: ix_patient_pos_patient_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patient_pos_patient_date ON public.patient_pos USING btree (patient_id, effective_date);


--
-- Name: ix_patient_pos_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patient_pos_patient_id ON public.patient_pos USING btree (patient_id);


--
-- Name: ix_patient_pos_tenant; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patient_pos_tenant ON public.patient_pos USING btree (tenant_id);


--
-- Name: ix_patients_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patients_created_by ON public.patients USING btree (created_by);


--
-- Name: ix_patients_mrn; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patients_mrn ON public.patients USING btree (mrn);


--
-- Name: ix_patients_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_patients_tenant_id ON public.patients USING btree (tenant_id);


--
-- Name: ix_payer_contracts_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_payer_contracts_tenant_id ON public.payer_contracts USING btree (tenant_id);


--
-- Name: ix_payers_code; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_payers_code ON public.payers USING btree (code);


--
-- Name: ix_payers_name; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_payers_name ON public.payers USING btree (name);


--
-- Name: ix_payers_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_payers_tenant_id ON public.payers USING btree (tenant_id);


--
-- Name: ix_plan_of_care_approvals_plan_of_care_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_approvals_plan_of_care_id ON public.plan_of_care_approvals USING btree (plan_of_care_id);


--
-- Name: ix_plan_of_care_approvals_version_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_approvals_version_id ON public.plan_of_care_approvals USING btree (version_id);


--
-- Name: ix_plan_of_care_goals_plan_of_care_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_goals_plan_of_care_id ON public.plan_of_care_goals USING btree (plan_of_care_id);


--
-- Name: ix_plan_of_care_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_patient_id ON public.plan_of_care USING btree (patient_id);


--
-- Name: ix_plan_of_care_review_due_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_review_due_at ON public.plan_of_care USING btree (review_due_at);


--
-- Name: ix_plan_of_care_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_status ON public.plan_of_care USING btree (status);


--
-- Name: ix_plan_of_care_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_tenant_id ON public.plan_of_care USING btree (tenant_id);


--
-- Name: ix_plan_of_care_versions_plan_of_care_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_plan_of_care_versions_plan_of_care_id ON public.plan_of_care_versions USING btree (plan_of_care_id);


--
-- Name: ix_respite_period_patient_service_dates; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_respite_period_patient_service_dates ON public.respite_periods USING btree (patient_id, service_level, start_date, end_date);


--
-- Name: ix_respite_periods_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_respite_periods_patient_id ON public.respite_periods USING btree (patient_id);


--
-- Name: ix_rn_recert_assessments_benefit_period_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_rn_recert_assessments_benefit_period_id ON public.rn_recert_assessments USING btree (benefit_period_id);


--
-- Name: ix_rn_recert_assessments_created_by_user_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_rn_recert_assessments_created_by_user_id ON public.rn_recert_assessments USING btree (created_by_user_id);


--
-- Name: ix_rn_recert_assessments_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_rn_recert_assessments_patient_id ON public.rn_recert_assessments USING btree (patient_id);


--
-- Name: ix_rn_recert_assessments_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_rn_recert_assessments_status ON public.rn_recert_assessments USING btree (status);


--
-- Name: ix_roles_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_roles_created_by ON public.roles USING btree (created_by);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_runbooks_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_runbooks_tenant_id ON public.runbooks USING btree (tenant_id);


--
-- Name: ix_safety_assessments_patient_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_safety_assessments_patient_id ON public.safety_assessments USING btree (patient_id);


--
-- Name: ix_security_activity_events_user_time; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_security_activity_events_user_time ON public.security_activity_events USING btree (user_id, event_at);


--
-- Name: ix_sfv_requirements_open_due; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_sfv_requirements_open_due ON public.sfv_requirements USING btree (patient_id, status, due_at);


--
-- Name: ix_sfv_requirements_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_sfv_requirements_patient ON public.sfv_requirements USING btree (patient_id);


--
-- Name: ix_survey_access_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_survey_access_created_by ON public.survey_access USING btree (created_by);


--
-- Name: ix_survey_access_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_survey_access_tenant_id ON public.survey_access USING btree (tenant_id);


--
-- Name: ix_tasks_assigned_user_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_assigned_user_id ON public.tasks USING btree (assigned_user_id);


--
-- Name: ix_tasks_benefit_period_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_benefit_period_id ON public.tasks USING btree (benefit_period_id);


--
-- Name: ix_tasks_completion_reference; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_completion_reference ON public.tasks USING btree (completion_reference_type, completion_reference_id);


--
-- Name: ix_tasks_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_created_by ON public.tasks USING btree (created_by);


--
-- Name: ix_tasks_discipline; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_discipline ON public.tasks USING btree (discipline);


--
-- Name: ix_tasks_regulatory_basis; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_regulatory_basis ON public.tasks USING btree (regulatory_basis);


--
-- Name: ix_tasks_schedule_status; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_schedule_status ON public.tasks USING btree (schedule_status);


--
-- Name: ix_tasks_scheduled_start_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_scheduled_start_at ON public.tasks USING btree (scheduled_start_at);


--
-- Name: ix_tasks_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_tenant_id ON public.tasks USING btree (tenant_id);


--
-- Name: ix_tasks_tenant_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_tenant_patient ON public.tasks USING btree (tenant_id, patient_id);


--
-- Name: ix_tasks_tenant_status_due; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tasks_tenant_status_due ON public.tasks USING btree (tenant_id, status, due_date);


--
-- Name: ix_tenant_rule_toggles_rule_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tenant_rule_toggles_rule_id ON public.tenant_rule_toggles USING btree (rule_id);


--
-- Name: ix_tenant_rule_toggles_tenant; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tenant_rule_toggles_tenant ON public.tenant_rule_toggles USING btree (tenant_id);


--
-- Name: ix_tenant_rule_toggles_workflow; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tenant_rule_toggles_workflow ON public.tenant_rule_toggles USING btree (workflow);


--
-- Name: ix_tenants_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_tenants_created_by ON public.tenants USING btree (created_by);


--
-- Name: ix_users_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_users_created_by ON public.users USING btree (created_by);


--
-- Name: ix_users_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_users_tenant_id ON public.users USING btree (tenant_id);


--
-- Name: ix_visit_minutes_tenant; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visit_minutes_tenant ON public.visit_minutes USING btree (tenant_id);


--
-- Name: ix_visit_minutes_visit_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visit_minutes_visit_date ON public.visit_minutes USING btree (visit_id, service_date);


--
-- Name: ix_visit_minutes_visit_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visit_minutes_visit_id ON public.visit_minutes USING btree (visit_id);


--
-- Name: ix_visits_acuity_state_at_visit; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visits_acuity_state_at_visit ON public.visits USING btree (acuity_state_at_visit);


--
-- Name: ix_visits_chha_poc_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visits_chha_poc_id ON public.visits USING btree (chha_poc_id);


--
-- Name: ix_visits_created_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visits_created_by ON public.visits USING btree (created_by);


--
-- Name: ix_visits_deleted_at; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visits_deleted_at ON public.visits USING btree (deleted_at);


--
-- Name: ix_visits_deleted_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visits_deleted_by ON public.visits USING btree (deleted_by);


--
-- Name: ix_visits_tenant_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visits_tenant_id ON public.visits USING btree (tenant_id);


--
-- Name: ix_visits_updated_by; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_visits_updated_by ON public.visits USING btree (updated_by);


--
-- Name: ix_volunteer_hours_activity_type; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_volunteer_hours_activity_type ON public.volunteer_hours USING btree (activity_type);


--
-- Name: ix_volunteer_hours_date; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_volunteer_hours_date ON public.volunteer_hours USING btree (date);


--
-- Name: ix_volunteer_hours_volunteer_user_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE INDEX ix_volunteer_hours_volunteer_user_id ON public.volunteer_hours USING btree (volunteer_user_id);


--
-- Name: uq_clinical_note_one_active_version; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_clinical_note_one_active_version ON public.clinical_note_versions USING btree (clinical_note_id) WHERE (is_active = true);


--
-- Name: uq_dx_active_primary_per_source; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_dx_active_primary_per_source ON public.diagnosis_sources USING btree (patient_id, source) WHERE ((is_active = true) AND (dx_type = 'PRIMARY'::text));


--
-- Name: uq_guardrail_policies_tenant_key; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_guardrail_policies_tenant_key ON public.guardrail_policies USING btree (tenant_id, policy_key);


--
-- Name: uq_med_recon_active_patient_signature; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_med_recon_active_patient_signature ON public.med_reconciliation_items USING btree (patient_id, lower((med_name_normalized)::text), lower((COALESCE(dose_normalized, ''::character varying))::text), lower((COALESCE(route_normalized, ''::character varying))::text), lower((COALESCE(frequency_normalized, ''::character varying))::text)) WHERE (((review_status)::text = 'PENDING'::text) AND (med_name_normalized IS NOT NULL));


--
-- Name: uq_one_current_bp_per_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_one_current_bp_per_patient ON public.benefit_periods USING btree (patient_id) WHERE (is_current = true);


--
-- Name: uq_patients_tenant_mrn; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_patients_tenant_mrn ON public.patients USING btree (tenant_id, mrn);


--
-- Name: uq_plan_of_care_one_live_per_patient; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_plan_of_care_one_live_per_patient ON public.plan_of_care USING btree (patient_id) WHERE ((status)::text = ANY ((ARRAY['DRAFT'::character varying, 'ACTIVE'::character varying])::text[]));


--
-- Name: uq_sfv_requirements_trigger_once; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX uq_sfv_requirements_trigger_once ON public.sfv_requirements USING btree (patient_id, trigger_source_type, trigger_reference_id);


--
-- Name: ux_document_idg_resolution_tenant_document; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ux_document_idg_resolution_tenant_document ON public.document_idg_resolution USING btree (tenant_id, document_id);


--
-- Name: ux_drug_aliases_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ux_drug_aliases_id ON public.drug_aliases USING btree (id) WHERE (id IS NOT NULL);


--
-- Name: ux_idg_md_attestations_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ux_idg_md_attestations_id ON public.idg_md_attestations USING btree (id) WHERE (id IS NOT NULL);


--
-- Name: ux_idg_meetings_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ux_idg_meetings_id ON public.idg_meetings USING btree (id) WHERE (id IS NOT NULL);


--
-- Name: ux_idg_notes_id; Type: INDEX; Schema: public; Owner: sns
--

CREATE UNIQUE INDEX ux_idg_notes_id ON public.idg_notes USING btree (id) WHERE (id IS NOT NULL);


--
-- Name: tenants trg_no_tenant_delete; Type: TRIGGER; Schema: core; Owner: sns
--

CREATE TRIGGER trg_no_tenant_delete BEFORE DELETE ON core.tenants FOR EACH ROW EXECUTE FUNCTION core.prevent_tenant_delete();


--
-- Name: patients patients_status_transition_guard; Type: TRIGGER; Schema: public; Owner: sns
--

CREATE TRIGGER patients_status_transition_guard BEFORE UPDATE OF status ON public.patients FOR EACH ROW EXECUTE FUNCTION public.enforce_patient_status_transition();


--
-- Name: regulatory_report_artifacts trg_block_artifacts_on_locked_report; Type: TRIGGER; Schema: public; Owner: sns
--

CREATE TRIGGER trg_block_artifacts_on_locked_report BEFORE INSERT OR DELETE OR UPDATE ON public.regulatory_report_artifacts FOR EACH ROW EXECUTE FUNCTION public.prevent_child_modification_when_report_locked();


--
-- Name: regulatory_report_metrics trg_block_metrics_on_locked_report; Type: TRIGGER; Schema: public; Owner: sns
--

CREATE TRIGGER trg_block_metrics_on_locked_report BEFORE INSERT OR DELETE OR UPDATE ON public.regulatory_report_metrics FOR EACH ROW EXECUTE FUNCTION public.prevent_child_modification_when_report_locked();


--
-- Name: regulatory_reports trg_block_report_update_when_locked; Type: TRIGGER; Schema: public; Owner: sns
--

CREATE TRIGGER trg_block_report_update_when_locked BEFORE DELETE OR UPDATE ON public.regulatory_reports FOR EACH ROW EXECUTE FUNCTION public.prevent_report_update_when_locked();


--
-- Name: regulatory_report_sections trg_block_sections_on_locked_report; Type: TRIGGER; Schema: public; Owner: sns
--

CREATE TRIGGER trg_block_sections_on_locked_report BEFORE INSERT OR DELETE OR UPDATE ON public.regulatory_report_sections FOR EACH ROW EXECUTE FUNCTION public.prevent_child_modification_when_report_locked();


--
-- Name: guardrail_policies trg_guardrail_policies_updated_at; Type: TRIGGER; Schema: public; Owner: sns
--

CREATE TRIGGER trg_guardrail_policies_updated_at BEFORE UPDATE ON public.guardrail_policies FOR EACH ROW EXECUTE FUNCTION public.update_guardrail_policies_updated_at();


--
-- Name: bereavement_declines trg_set_bereavement_task_decline_flag; Type: TRIGGER; Schema: public; Owner: sns
--

CREATE TRIGGER trg_set_bereavement_task_decline_flag AFTER INSERT ON public.bereavement_declines FOR EACH ROW EXECUTE FUNCTION public.set_bereavement_task_decline_flag();


--
-- Name: tenant_events fk_tenant_events_tenant_id_tenants; Type: FK CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.tenant_events
    ADD CONSTRAINT fk_tenant_events_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES core.tenants(id) ON DELETE RESTRICT;


--
-- Name: tenants fk_tenants_billing_organization; Type: FK CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.tenants
    ADD CONSTRAINT fk_tenants_billing_organization FOREIGN KEY (billing_organization_id) REFERENCES core.billing_organizations(id) ON DELETE SET NULL;


--
-- Name: user_tenants fk_user_tenants_tenant_id_tenants; Type: FK CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.user_tenants
    ADD CONSTRAINT fk_user_tenants_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES core.tenants(id) ON DELETE RESTRICT;


--
-- Name: user_tenants fk_user_tenants_user_id_users; Type: FK CONSTRAINT; Schema: core; Owner: sns
--

ALTER TABLE ONLY core.user_tenants
    ADD CONSTRAINT fk_user_tenants_user_id_users FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE RESTRICT;


--
-- Name: amendments fk_amendments_author_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.amendments
    ADD CONSTRAINT fk_amendments_author_id_users FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: amendments fk_amendments_clinical_note_id_clinical_notes; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.amendments
    ADD CONSTRAINT fk_amendments_clinical_note_id_clinical_notes FOREIGN KEY (clinical_note_id) REFERENCES public.clinical_notes(id);


--
-- Name: amendments fk_amendments_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.amendments
    ADD CONSTRAINT fk_amendments_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: assessment_discrepancies fk_assessment_discrepancies_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_discrepancies
    ADD CONSTRAINT fk_assessment_discrepancies_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: assessment_discrepancies fk_assessment_discrepancies_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_discrepancies
    ADD CONSTRAINT fk_assessment_discrepancies_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: assessment_references fk_assessment_references_assessment; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_references
    ADD CONSTRAINT fk_assessment_references_assessment FOREIGN KEY (assessment_id) REFERENCES public.assessments(id) ON DELETE CASCADE;


--
-- Name: assessment_references fk_assessment_references_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_references
    ADD CONSTRAINT fk_assessment_references_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: assessment_references fk_assessment_references_referenced; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_references
    ADD CONSTRAINT fk_assessment_references_referenced FOREIGN KEY (referenced_assessment_id) REFERENCES public.assessments(id) ON DELETE CASCADE;


--
-- Name: assessments fk_assessments_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT fk_assessments_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: assessments fk_assessments_patient; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT fk_assessments_patient FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE RESTRICT;


--
-- Name: assessments fk_assessments_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT fk_assessments_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: audit_logs fk_audit_logs_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT fk_audit_logs_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: authorization_records fk_authorization_records_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.authorization_records
    ADD CONSTRAINT fk_authorization_records_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: benefit_periods fk_benefit_periods_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.benefit_periods
    ADD CONSTRAINT fk_benefit_periods_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: benefit_periods fk_benefit_periods_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.benefit_periods
    ADD CONSTRAINT fk_benefit_periods_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: benefit_periods fk_benefit_periods_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.benefit_periods
    ADD CONSTRAINT fk_benefit_periods_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: benefit_periods fk_benefit_periods_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.benefit_periods
    ADD CONSTRAINT fk_benefit_periods_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: bereavement_cases fk_bereavement_cases_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_cases
    ADD CONSTRAINT fk_bereavement_cases_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: bereavement_declines fk_bereavement_declines_bereavement_task_id_bereavement_tasks; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_declines
    ADD CONSTRAINT fk_bereavement_declines_bereavement_task_id_bereavement_tasks FOREIGN KEY (bereavement_task_id) REFERENCES public.bereavement_tasks(id) ON DELETE CASCADE;


--
-- Name: bereavement_declines fk_bereavement_declines_recorded_by_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_declines
    ADD CONSTRAINT fk_bereavement_declines_recorded_by_user_id_users FOREIGN KEY (recorded_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: bereavement_tasks fk_bereavement_tasks_bereavement_case_id_bereavement_cases; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_tasks
    ADD CONSTRAINT fk_bereavement_tasks_bereavement_case_id_bereavement_cases FOREIGN KEY (bereavement_case_id) REFERENCES public.bereavement_cases(id) ON DELETE CASCADE;


--
-- Name: bereavement_tasks fk_bereavement_tasks_completed_by_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.bereavement_tasks
    ADD CONSTRAINT fk_bereavement_tasks_completed_by_user_id_users FOREIGN KEY (completed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: billing_snapshots fk_billing_snapshots_billing_cycle_id_billing_cycles; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_snapshots
    ADD CONSTRAINT fk_billing_snapshots_billing_cycle_id_billing_cycles FOREIGN KEY (billing_cycle_id) REFERENCES public.billing_cycles(id) ON DELETE SET NULL;


--
-- Name: billing_snapshots fk_billing_snapshots_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_snapshots
    ADD CONSTRAINT fk_billing_snapshots_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: billing_snapshots fk_billing_snapshots_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_snapshots
    ADD CONSTRAINT fk_billing_snapshots_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: billing_summaries fk_billing_summaries_billing_cycle_id_billing_cycles; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_summaries
    ADD CONSTRAINT fk_billing_summaries_billing_cycle_id_billing_cycles FOREIGN KEY (billing_cycle_id) REFERENCES public.billing_cycles(id) ON DELETE CASCADE;


--
-- Name: billing_summaries fk_billing_summaries_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_summaries
    ADD CONSTRAINT fk_billing_summaries_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: billing_summaries fk_billing_summaries_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.billing_summaries
    ADD CONSTRAINT fk_billing_summaries_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: certifications fk_certifications_benefit_period_id_benefit_periods; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.certifications
    ADD CONSTRAINT fk_certifications_benefit_period_id_benefit_periods FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id);


--
-- Name: certifications fk_certifications_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.certifications
    ADD CONSTRAINT fk_certifications_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: chha_pocs fk_chha_pocs_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_pocs
    ADD CONSTRAINT fk_chha_pocs_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: chha_pocs fk_chha_pocs_finalized_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_pocs
    ADD CONSTRAINT fk_chha_pocs_finalized_by_users FOREIGN KEY (finalized_by) REFERENCES public.users(id);


--
-- Name: chha_pocs fk_chha_pocs_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_pocs
    ADD CONSTRAINT fk_chha_pocs_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: chha_visit_outcomes fk_chha_visit_outcomes_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_visit_outcomes
    ADD CONSTRAINT fk_chha_visit_outcomes_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: chha_visit_outcomes fk_chha_visit_outcomes_visit_id_visits; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_visit_outcomes
    ADD CONSTRAINT fk_chha_visit_outcomes_visit_id_visits FOREIGN KEY (visit_id) REFERENCES public.visits(id);


--
-- Name: chha_visit_task_results fk_chha_visit_task_results_outcome_id_chha_visit_outcomes; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.chha_visit_task_results
    ADD CONSTRAINT fk_chha_visit_task_results_outcome_id_chha_visit_outcomes FOREIGN KEY (outcome_id) REFERENCES public.chha_visit_outcomes(id) ON DELETE CASCADE;


--
-- Name: claim_export_logs fk_claim_export_logs_billing_cycle_id_billing_cycles; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.claim_export_logs
    ADD CONSTRAINT fk_claim_export_logs_billing_cycle_id_billing_cycles FOREIGN KEY (billing_cycle_id) REFERENCES public.billing_cycles(id) ON DELETE CASCADE;


--
-- Name: claim_export_logs fk_claim_export_logs_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.claim_export_logs
    ADD CONSTRAINT fk_claim_export_logs_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: claim_export_logs fk_claim_export_logs_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.claim_export_logs
    ADD CONSTRAINT fk_claim_export_logs_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: clinical_note_versions fk_clinical_note_versions_clinical_note_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_note_versions
    ADD CONSTRAINT fk_clinical_note_versions_clinical_note_id FOREIGN KEY (clinical_note_id) REFERENCES public.clinical_notes(id) ON DELETE RESTRICT;


--
-- Name: clinical_notes fk_clinical_notes_author_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_clinical_notes_author_id_users FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: clinical_notes fk_clinical_notes_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_clinical_notes_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: clinical_notes fk_clinical_notes_current_version_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_clinical_notes_current_version_id FOREIGN KEY (current_version_id) REFERENCES public.clinical_note_versions(id) ON DELETE RESTRICT;


--
-- Name: clinical_notes fk_clinical_notes_parent_form; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_clinical_notes_parent_form FOREIGN KEY (parent_form_id) REFERENCES public.clinical_notes(id) ON DELETE CASCADE;


--
-- Name: clinical_notes fk_clinical_notes_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_clinical_notes_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: clinical_notes fk_clinical_notes_visit_id_visits; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_clinical_notes_visit_id_visits FOREIGN KEY (visit_id) REFERENCES public.visits(id);


--
-- Name: diagnosis_discrepancies fk_diagnosis_discrepancies_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_discrepancies
    ADD CONSTRAINT fk_diagnosis_discrepancies_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: diagnosis_reconciliations fk_diagnosis_reconciliations_attested_by_account_id_accounts; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_reconciliations
    ADD CONSTRAINT fk_diagnosis_reconciliations_attested_by_account_id_accounts FOREIGN KEY (attested_by_account_id) REFERENCES public.accounts(id);


--
-- Name: diagnosis_reconciliations fk_diagnosis_reconciliations_discrepancy_id_diagnosis_d_71ea; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_reconciliations
    ADD CONSTRAINT fk_diagnosis_reconciliations_discrepancy_id_diagnosis_d_71ea FOREIGN KEY (discrepancy_id) REFERENCES public.diagnosis_discrepancies(id) ON DELETE CASCADE;


--
-- Name: diagnosis_sources fk_diagnosis_sources_documented_by_account_id_accounts; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_sources
    ADD CONSTRAINT fk_diagnosis_sources_documented_by_account_id_accounts FOREIGN KEY (documented_by_account_id) REFERENCES public.accounts(id);


--
-- Name: diagnosis_sources fk_diagnosis_sources_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.diagnosis_sources
    ADD CONSTRAINT fk_diagnosis_sources_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: discharges fk_discharges_discharge_reason_code_discharge_reasons; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.discharges
    ADD CONSTRAINT fk_discharges_discharge_reason_code_discharge_reasons FOREIGN KEY (discharge_reason_code) REFERENCES public.discharge_reasons(code);


--
-- Name: discharges fk_discharges_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.discharges
    ADD CONSTRAINT fk_discharges_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: discharges fk_discharges_recorded_by_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.discharges
    ADD CONSTRAINT fk_discharges_recorded_by_user_id_users FOREIGN KEY (recorded_by_user_id) REFERENCES public.users(id);


--
-- Name: assessment_discrepancies fk_discrepancies_baseline_assessment; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_discrepancies
    ADD CONSTRAINT fk_discrepancies_baseline_assessment FOREIGN KEY (baseline_assessment_id) REFERENCES public.assessments(id) ON DELETE SET NULL;


--
-- Name: assessment_discrepancies fk_discrepancies_comparing_assessment; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_discrepancies
    ADD CONSTRAINT fk_discrepancies_comparing_assessment FOREIGN KEY (comparing_assessment_id) REFERENCES public.assessments(id) ON DELETE SET NULL;


--
-- Name: assessment_discrepancies fk_discrepancies_patient; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_discrepancies
    ADD CONSTRAINT fk_discrepancies_patient FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE RESTRICT;


--
-- Name: assessment_discrepancies fk_discrepancies_resolved_in_idg_meeting; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.assessment_discrepancies
    ADD CONSTRAINT fk_discrepancies_resolved_in_idg_meeting FOREIGN KEY (resolved_in_idg_meeting_id) REFERENCES public.idg_meetings(idg_id) ON DELETE SET NULL;


--
-- Name: document_idg_resolution fk_document_idg_resolution_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_idg_resolution
    ADD CONSTRAINT fk_document_idg_resolution_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: document_idg_resolution fk_document_idg_resolution_document_id_document_records; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_idg_resolution
    ADD CONSTRAINT fk_document_idg_resolution_document_id_document_records FOREIGN KEY (document_id) REFERENCES public.document_records(id) ON DELETE CASCADE;


--
-- Name: document_idg_resolution fk_document_idg_resolution_resolved_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_idg_resolution
    ADD CONSTRAINT fk_document_idg_resolution_resolved_by_users FOREIGN KEY (resolved_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: document_idg_resolution fk_document_idg_resolution_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_idg_resolution
    ADD CONSTRAINT fk_document_idg_resolution_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: document_idg_resolution fk_document_idg_resolution_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_idg_resolution
    ADD CONSTRAINT fk_document_idg_resolution_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: document_idg_resolution fk_document_idg_resolution_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_idg_resolution
    ADD CONSTRAINT fk_document_idg_resolution_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: document_records fk_document_records_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_records
    ADD CONSTRAINT fk_document_records_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: document_records fk_document_records_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.document_records
    ADD CONSTRAINT fk_document_records_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: drug_aliases fk_drug_aliases_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.drug_aliases
    ADD CONSTRAINT fk_drug_aliases_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: dx_primary_policies fk_dx_primary_policies_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.dx_primary_policies
    ADD CONSTRAINT fk_dx_primary_policies_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: eligibility_assessments fk_eligibility_assessments_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.eligibility_assessments
    ADD CONSTRAINT fk_eligibility_assessments_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: eligibility_decisions fk_eligibility_decisions_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.eligibility_decisions
    ADD CONSTRAINT fk_eligibility_decisions_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: eligibility_rulesets fk_eligibility_rulesets_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.eligibility_rulesets
    ADD CONSTRAINT fk_eligibility_rulesets_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: f2f_encounters fk_f2f_encounters_benefit_period_id_benefit_periods; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.f2f_encounters
    ADD CONSTRAINT fk_f2f_encounters_benefit_period_id_benefit_periods FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id);


--
-- Name: f2f_encounters fk_f2f_encounters_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.f2f_encounters
    ADD CONSTRAINT fk_f2f_encounters_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: form_package_modules fk_form_package_modules_form_registry_id_form_registry; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_package_modules
    ADD CONSTRAINT fk_form_package_modules_form_registry_id_form_registry FOREIGN KEY (form_registry_id) REFERENCES public.form_registry(id) ON DELETE CASCADE;


--
-- Name: form_package_modules fk_form_package_modules_module_id_form_modules; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.form_package_modules
    ADD CONSTRAINT fk_form_package_modules_module_id_form_modules FOREIGN KEY (module_id) REFERENCES public.form_modules(id) ON DELETE CASCADE;


--
-- Name: forms fk_forms_form_registry_id_form_registry; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.forms
    ADD CONSTRAINT fk_forms_form_registry_id_form_registry FOREIGN KEY (form_registry_id) REFERENCES public.form_registry(id) ON DELETE RESTRICT;


--
-- Name: forms fk_forms_visit_id_visits; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.forms
    ADD CONSTRAINT fk_forms_visit_id_visits FOREIGN KEY (visit_id) REFERENCES public.visits(id) ON DELETE CASCADE;


--
-- Name: guardrail_policies fk_guardrail_policies_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.guardrail_policies
    ADD CONSTRAINT fk_guardrail_policies_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: hope_symptom_assessments fk_hope_symptom_assessments_hope_record_id_hope_records; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_symptom_assessments
    ADD CONSTRAINT fk_hope_symptom_assessments_hope_record_id_hope_records FOREIGN KEY (hope_record_id) REFERENCES public.hope_records(id);


--
-- Name: hope_symptom_followups fk_hope_symptom_followups_hope_record_id_hope_records; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_symptom_followups
    ADD CONSTRAINT fk_hope_symptom_followups_hope_record_id_hope_records FOREIGN KEY (hope_record_id) REFERENCES public.hope_records(id);


--
-- Name: hope_symptom_visits fk_hope_symptom_visits_hope_symptom_followup_id_hope_sy_d7ad; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_symptom_visits
    ADD CONSTRAINT fk_hope_symptom_visits_hope_symptom_followup_id_hope_sy_d7ad FOREIGN KEY (hope_symptom_followup_id) REFERENCES public.hope_symptom_followups(id);


--
-- Name: hope_symptom_visits fk_hope_symptom_visits_visit_id_visits; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_symptom_visits
    ADD CONSTRAINT fk_hope_symptom_visits_visit_id_visits FOREIGN KEY (visit_id) REFERENCES public.visits(id);


--
-- Name: idg_attendance fk_idg_attendance_session; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_attendance
    ADD CONSTRAINT fk_idg_attendance_session FOREIGN KEY (idg_session_id) REFERENCES public.idg_session(id) ON DELETE CASCADE;


--
-- Name: idg_md_attestations fk_idg_md_attestations_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_md_attestations
    ADD CONSTRAINT fk_idg_md_attestations_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: idg_md_attestations fk_idg_md_attestations_idg_review_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_md_attestations
    ADD CONSTRAINT fk_idg_md_attestations_idg_review_id FOREIGN KEY (idg_review_id) REFERENCES public.idg_reviews(id) ON DELETE RESTRICT;


--
-- Name: idg_md_attestations fk_idg_md_attestations_md_user_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_md_attestations
    ADD CONSTRAINT fk_idg_md_attestations_md_user_id FOREIGN KEY (md_user_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: idg_meetings fk_idg_meetings_benefit_period_id_benefit_periods; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_meetings
    ADD CONSTRAINT fk_idg_meetings_benefit_period_id_benefit_periods FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id);


--
-- Name: idg_meetings fk_idg_meetings_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_meetings
    ADD CONSTRAINT fk_idg_meetings_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: idg_notes fk_idg_notes_author_user_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_notes
    ADD CONSTRAINT fk_idg_notes_author_user_id FOREIGN KEY (author_user_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: idg_notes fk_idg_notes_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_notes
    ADD CONSTRAINT fk_idg_notes_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: idg_notes fk_idg_notes_idg_review_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_notes
    ADD CONSTRAINT fk_idg_notes_idg_review_id FOREIGN KEY (idg_review_id) REFERENCES public.idg_reviews(id) ON DELETE RESTRICT;


--
-- Name: idg_reviews fk_idg_reviews_benefit_period_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_reviews
    ADD CONSTRAINT fk_idg_reviews_benefit_period_id FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id) ON DELETE SET NULL;


--
-- Name: idg_reviews fk_idg_reviews_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_reviews
    ADD CONSTRAINT fk_idg_reviews_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: idg_reviews fk_idg_reviews_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_reviews
    ADD CONSTRAINT fk_idg_reviews_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: idg_reviews fk_idg_reviews_patient_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_reviews
    ADD CONSTRAINT fk_idg_reviews_patient_id FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE RESTRICT;


--
-- Name: idg_reviews fk_idg_reviews_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_reviews
    ADD CONSTRAINT fk_idg_reviews_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: idg_session fk_idg_session_plan_of_care; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_session
    ADD CONSTRAINT fk_idg_session_plan_of_care FOREIGN KEY (plan_of_care_id) REFERENCES public.plan_of_care(id) ON DELETE CASCADE;


--
-- Name: idg_signatures fk_idg_signatures_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_signatures
    ADD CONSTRAINT fk_idg_signatures_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: idg_signatures fk_idg_signatures_idg_review_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_signatures
    ADD CONSTRAINT fk_idg_signatures_idg_review_id FOREIGN KEY (idg_review_id) REFERENCES public.idg_reviews(id) ON DELETE RESTRICT;


--
-- Name: idg_signatures fk_idg_signatures_user_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_signatures
    ADD CONSTRAINT fk_idg_signatures_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: interfaces fk_interfaces_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.interfaces
    ADD CONSTRAINT fk_interfaces_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: idg_md_attestations fk_md_attestations_idg_review; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_md_attestations
    ADD CONSTRAINT fk_md_attestations_idg_review FOREIGN KEY (idg_review_id) REFERENCES public.idg_reviews(id);


--
-- Name: med_reconciliation_imports fk_med_reconciliation_imports_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_imports
    ADD CONSTRAINT fk_med_reconciliation_imports_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: med_reconciliation_imports fk_med_reconciliation_imports_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_imports
    ADD CONSTRAINT fk_med_reconciliation_imports_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: med_reconciliation_items fk_med_reconciliation_items_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_items
    ADD CONSTRAINT fk_med_reconciliation_items_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: med_reconciliation_items fk_med_reconciliation_items_import_id_imports; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_items
    ADD CONSTRAINT fk_med_reconciliation_items_import_id_imports FOREIGN KEY (import_id) REFERENCES public.med_reconciliation_imports(id) ON DELETE CASCADE;


--
-- Name: med_reconciliation_items fk_med_reconciliation_items_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.med_reconciliation_items
    ADD CONSTRAINT fk_med_reconciliation_items_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: medications fk_medications_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT fk_medications_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: medications fk_medications_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT fk_medications_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: medications fk_medications_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT fk_medications_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: clinical_notes fk_notes_finalized_interface; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_notes_finalized_interface FOREIGN KEY (finalized_interface_id) REFERENCES public.interfaces(id);


--
-- Name: clinical_notes fk_notes_finalized_role; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.clinical_notes
    ADD CONSTRAINT fk_notes_finalized_role FOREIGN KEY (finalized_role_id) REFERENCES public.roles(id);


--
-- Name: orders_snapshots fk_orders_snapshots_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.orders_snapshots
    ADD CONSTRAINT fk_orders_snapshots_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: orders_snapshots fk_orders_snapshots_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.orders_snapshots
    ADD CONSTRAINT fk_orders_snapshots_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: patient_allergies fk_patient_allergies_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT fk_patient_allergies_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: patient_allergies fk_patient_allergies_recorded_by_account_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT fk_patient_allergies_recorded_by_account_id_users FOREIGN KEY (recorded_by_account_id) REFERENCES public.users(id);


--
-- Name: patient_allergy_profiles fk_patient_allergy_profiles_last_updated_by_account_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_allergy_profiles
    ADD CONSTRAINT fk_patient_allergy_profiles_last_updated_by_account_id_users FOREIGN KEY (last_updated_by_account_id) REFERENCES public.users(id);


--
-- Name: patient_allergy_profiles fk_patient_allergy_profiles_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_allergy_profiles
    ADD CONSTRAINT fk_patient_allergy_profiles_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: patient_assignments fk_patient_assignments_assigned_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_assignments
    ADD CONSTRAINT fk_patient_assignments_assigned_by_users FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: patient_assignments fk_patient_assignments_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_assignments
    ADD CONSTRAINT fk_patient_assignments_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: patient_assignments fk_patient_assignments_staff_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_assignments
    ADD CONSTRAINT fk_patient_assignments_staff_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: patient_insurances fk_patient_insurances_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_insurances
    ADD CONSTRAINT fk_patient_insurances_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: patient_insurances fk_patient_insurances_verified_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patient_insurances
    ADD CONSTRAINT fk_patient_insurances_verified_by_users FOREIGN KEY (verified_by) REFERENCES public.users(id);


--
-- Name: patients fk_patients_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT fk_patients_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: patients fk_patients_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT fk_patients_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: patients fk_patients_current_discharge; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT fk_patients_current_discharge FOREIGN KEY (current_discharge_id) REFERENCES public.discharges(id) ON DELETE SET NULL;


--
-- Name: patients fk_patients_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT fk_patients_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: patients fk_patients_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT fk_patients_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: payers fk_payers_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.payers
    ADD CONSTRAINT fk_payers_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: plan_of_care_approvals fk_plan_of_care_approvals_plan_of_care_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_approvals
    ADD CONSTRAINT fk_plan_of_care_approvals_plan_of_care_id FOREIGN KEY (plan_of_care_id) REFERENCES public.plan_of_care(id) ON DELETE CASCADE;


--
-- Name: plan_of_care_approvals fk_plan_of_care_approvals_version_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_approvals
    ADD CONSTRAINT fk_plan_of_care_approvals_version_id FOREIGN KEY (version_id) REFERENCES public.plan_of_care_versions(id) ON DELETE CASCADE;


--
-- Name: plan_of_care fk_plan_of_care_current_version_id_versions; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care
    ADD CONSTRAINT fk_plan_of_care_current_version_id_versions FOREIGN KEY (current_version_id) REFERENCES public.plan_of_care_versions(id);


--
-- Name: plan_of_care_goals fk_plan_of_care_goals_plan_of_care_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_goals
    ADD CONSTRAINT fk_plan_of_care_goals_plan_of_care_id FOREIGN KEY (plan_of_care_id) REFERENCES public.plan_of_care(id) ON DELETE CASCADE;


--
-- Name: plan_of_care fk_plan_of_care_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care
    ADD CONSTRAINT fk_plan_of_care_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: plan_of_care fk_plan_of_care_supersedes_self; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care
    ADD CONSTRAINT fk_plan_of_care_supersedes_self FOREIGN KEY (supersedes_plan_of_care_id) REFERENCES public.plan_of_care(id);


--
-- Name: plan_of_care_versions fk_plan_of_care_versions_based_on_version; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_versions
    ADD CONSTRAINT fk_plan_of_care_versions_based_on_version FOREIGN KEY (based_on_version_id) REFERENCES public.plan_of_care_versions(id);


--
-- Name: plan_of_care_versions fk_plan_of_care_versions_plan_of_care_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.plan_of_care_versions
    ADD CONSTRAINT fk_plan_of_care_versions_plan_of_care_id FOREIGN KEY (plan_of_care_id) REFERENCES public.plan_of_care(id) ON DELETE CASCADE;


--
-- Name: regulatory_report_artifacts fk_regulatory_report_artifacts_report_id_regulatory_reports; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_artifacts
    ADD CONSTRAINT fk_regulatory_report_artifacts_report_id_regulatory_reports FOREIGN KEY (report_id) REFERENCES public.regulatory_reports(id);


--
-- Name: regulatory_report_metrics fk_regulatory_report_metrics_report_id_regulatory_reports; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_metrics
    ADD CONSTRAINT fk_regulatory_report_metrics_report_id_regulatory_reports FOREIGN KEY (report_id) REFERENCES public.regulatory_reports(id);


--
-- Name: regulatory_report_metrics fk_regulatory_report_metrics_section_id_regulatory_repo_60e0; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_metrics
    ADD CONSTRAINT fk_regulatory_report_metrics_section_id_regulatory_repo_60e0 FOREIGN KEY (section_id) REFERENCES public.regulatory_report_sections(id);


--
-- Name: regulatory_report_sections fk_regulatory_report_sections_report_id_regulatory_reports; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.regulatory_report_sections
    ADD CONSTRAINT fk_regulatory_report_sections_report_id_regulatory_reports FOREIGN KEY (report_id) REFERENCES public.regulatory_reports(id);


--
-- Name: rn_recert_assessments fk_rn_recert_assessments_attesting_provider_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.rn_recert_assessments
    ADD CONSTRAINT fk_rn_recert_assessments_attesting_provider_user_id_users FOREIGN KEY (attesting_provider_user_id) REFERENCES public.users(id);


--
-- Name: rn_recert_assessments fk_rn_recert_assessments_benefit_period_id_benefit_periods; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.rn_recert_assessments
    ADD CONSTRAINT fk_rn_recert_assessments_benefit_period_id_benefit_periods FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id);


--
-- Name: rn_recert_assessments fk_rn_recert_assessments_created_by_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.rn_recert_assessments
    ADD CONSTRAINT fk_rn_recert_assessments_created_by_user_id_users FOREIGN KEY (created_by_user_id) REFERENCES public.users(id);


--
-- Name: rn_recert_assessments fk_rn_recert_assessments_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.rn_recert_assessments
    ADD CONSTRAINT fk_rn_recert_assessments_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: rn_recert_assessments fk_rn_recert_assessments_translation_reviewed_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.rn_recert_assessments
    ADD CONSTRAINT fk_rn_recert_assessments_translation_reviewed_by_users FOREIGN KEY (translation_reviewed_by) REFERENCES public.users(id);


--
-- Name: roles fk_roles_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT fk_roles_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: roles fk_roles_interface; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT fk_roles_interface FOREIGN KEY (interface_id) REFERENCES public.interfaces(id);


--
-- Name: sfv_requirements fk_sfv_requirements_completed_visit_id_visits; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.sfv_requirements
    ADD CONSTRAINT fk_sfv_requirements_completed_visit_id_visits FOREIGN KEY (completed_visit_id) REFERENCES public.visits(id) ON DELETE SET NULL;


--
-- Name: sfv_requirements fk_sfv_requirements_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.sfv_requirements
    ADD CONSTRAINT fk_sfv_requirements_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: sfv_requirements fk_sfv_requirements_tenant_id_tenants; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.sfv_requirements
    ADD CONSTRAINT fk_sfv_requirements_tenant_id_tenants FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: survey_access fk_survey_access_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT fk_survey_access_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: survey_access fk_survey_access_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT fk_survey_access_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: survey_access fk_survey_access_issued_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT fk_survey_access_issued_by_users FOREIGN KEY (issued_by) REFERENCES public.users(id);


--
-- Name: survey_access fk_survey_access_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT fk_survey_access_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: survey_access fk_survey_access_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT fk_survey_access_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: survey_access fk_survey_access_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.survey_access
    ADD CONSTRAINT fk_survey_access_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: tasks fk_tasks_assigned_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_assigned_user_id_users FOREIGN KEY (assigned_user_id) REFERENCES public.users(id);


--
-- Name: tasks fk_tasks_benefit_period_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_benefit_period_id FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id) ON DELETE SET NULL;


--
-- Name: tasks fk_tasks_benefit_period_id_benefit_periods; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_benefit_period_id_benefit_periods FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id);


--
-- Name: tasks fk_tasks_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: tasks fk_tasks_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: tasks fk_tasks_patient_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_patient_id FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE RESTRICT;


--
-- Name: tasks fk_tasks_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: tasks fk_tasks_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: tasks fk_tasks_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT fk_tasks_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: user_interface_roles fk_uir_interface; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.user_interface_roles
    ADD CONSTRAINT fk_uir_interface FOREIGN KEY (interface_id) REFERENCES public.interfaces(id);


--
-- Name: user_interface_roles fk_uir_role; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.user_interface_roles
    ADD CONSTRAINT fk_uir_role FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: user_interface_roles fk_uir_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.user_interface_roles
    ADD CONSTRAINT fk_uir_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: user_interface_roles fk_uir_user; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.user_interface_roles
    ADD CONSTRAINT fk_uir_user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users fk_users_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: users fk_users_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: users fk_users_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: users fk_users_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: visits fk_visits_chha_poc_id_chha_pocs; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_chha_poc_id_chha_pocs FOREIGN KEY (chha_poc_id) REFERENCES public.chha_pocs(id);


--
-- Name: visits fk_visits_created_by; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: visits fk_visits_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: visits fk_visits_deleted_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_deleted_by_users FOREIGN KEY (deleted_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: visits fk_visits_finalized_interface; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_finalized_interface FOREIGN KEY (finalized_interface_id) REFERENCES public.interfaces(id);


--
-- Name: visits fk_visits_finalized_role; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_finalized_role FOREIGN KEY (finalized_role_id) REFERENCES public.roles(id);


--
-- Name: visits fk_visits_patient_id_patients; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_patient_id_patients FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: visits fk_visits_provider_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_provider_id_users FOREIGN KEY (provider_id) REFERENCES public.users(id);


--
-- Name: visits fk_visits_tenant; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: visits fk_visits_tenant_id; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE RESTRICT;


--
-- Name: visits fk_visits_updated_by_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT fk_visits_updated_by_users FOREIGN KEY (updated_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: volunteer_hours fk_volunteer_hours_supervised_by_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.volunteer_hours
    ADD CONSTRAINT fk_volunteer_hours_supervised_by_user_id_users FOREIGN KEY (supervised_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: volunteer_hours fk_volunteer_hours_volunteer_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.volunteer_hours
    ADD CONSTRAINT fk_volunteer_hours_volunteer_user_id_users FOREIGN KEY (volunteer_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: hope_records hope_records_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_records
    ADD CONSTRAINT hope_records_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: hope_records hope_records_previous_hope_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.hope_records
    ADD CONSTRAINT hope_records_previous_hope_record_id_fkey FOREIGN KEY (previous_hope_record_id) REFERENCES public.hope_records(id);


--
-- Name: idg_signatures idg_signatures_idg_review_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.idg_signatures
    ADD CONSTRAINT idg_signatures_idg_review_id_fkey FOREIGN KEY (idg_review_id) REFERENCES public.idg_reviews(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_benefit_period_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sns
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_benefit_period_id_fkey FOREIGN KEY (benefit_period_id) REFERENCES public.benefit_periods(id);


--
-- Name: tasks; Type: ROW SECURITY; Schema: public; Owner: sns
--

ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

--
-- Name: tasks tenant_isolation_tasks; Type: POLICY; Schema: public; Owner: sns
--

CREATE POLICY tenant_isolation_tasks ON public.tasks USING (((tenant_id)::text = current_setting('app.tenant_id'::text, true))) WITH CHECK (((tenant_id)::text = current_setting('app.tenant_id'::text, true)));


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO sns_user;
GRANT USAGE ON SCHEMA public TO sns_owner;
GRANT ALL ON SCHEMA public TO sns;


--
-- Name: TABLE patient_face_sheet_view; Type: ACL; Schema: public; Owner: sns
--

GRANT SELECT ON TABLE public.patient_face_sheet_view TO sns_user;


--
-- Name: TABLE refusals; Type: ACL; Schema: public; Owner: sns
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.refusals TO sns_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: sns_owner
--

ALTER DEFAULT PRIVILEGES FOR ROLE sns_owner IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO sns;
ALTER DEFAULT PRIVILEGES FOR ROLE sns_owner IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO sns_user;


--
-- PostgreSQL database dump complete
--

\unrestrict legXScc9SU8MzGemLrSZVGnee0IUOB43fYrGhbCAVIoEZlb8IVnXbBjMoCEdqfL

