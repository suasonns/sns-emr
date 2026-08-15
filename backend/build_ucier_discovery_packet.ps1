# SNS UCIER Discovery Packet Builder
# Run from: C:\dev\sns emr\backend
# Output: SNS_UCIER_DISCOVERY_PACKET.md

$ErrorActionPreference = "Continue"

$Root = Get-Location
$Out = Join-Path $Root "SNS_UCIER_DISCOVERY_PACKET.md"
$DbName = "sns_emr_dev_clean"

" # SNS UCIER Discovery Packet" | Out-File $Out -Encoding UTF8
"" | Out-File $Out -Append -Encoding UTF8
"Generated from local repository and PostgreSQL schema." | Out-File $Out -Append -Encoding UTF8
"Root: $Root" | Out-File $Out -Append -Encoding UTF8
"Database: $DbName" | Out-File $Out -Append -Encoding UTF8
"" | Out-File $Out -Append -Encoding UTF8

function Add-Section {
    param([string]$Title)
    "" | Out-File $Out -Append -Encoding UTF8
    "## $Title" | Out-File $Out -Append -Encoding UTF8
    "" | Out-File $Out -Append -Encoding UTF8
}

function Add-AppSearch {
    param(
        [string]$Title,
        [string]$Pattern
    )

    Add-Section $Title

    Get-ChildItem .\app -Recurse -Filter *.py |
    Select-String -Pattern $Pattern |
    Select-Object Path, LineNumber, Line |
    Format-Table -AutoSize |
    Out-String -Width 300 |
    Out-File $Out -Append -Encoding UTF8
}

function Add-AppSearchContext {
    param(
        [string]$Title,
        [string]$Path,
        [string]$Pattern
    )

    Add-Section $Title

    if (Test-Path $Path) {
        Select-String -Path $Path -Pattern $Pattern -Context 5,5 |
        Out-String -Width 300 |
        Out-File $Out -Append -Encoding UTF8
    }
    else {
        "NOT FOUND: $Path" | Out-File $Out -Append -Encoding UTF8
    }
}

function Add-PsqlQuery {
    param(
        [string]$Title,
        [string]$Sql
    )

    Add-Section $Title

    $psqlExists = Get-Command psql -ErrorAction SilentlyContinue

    if ($null -eq $psqlExists) {
        "PSQL NOT FOUND ON PATH. Run this SQL manually:" | Out-File $Out -Append -Encoding UTF8
        $Sql | Out-File $Out -Append -Encoding UTF8
        return
    }

    psql -d $DbName -P pager=off -c $Sql 2>&1 |
    Out-String -Width 300 |
    Out-File $Out -Append -Encoding UTF8
}

Add-Section "1. Repository Summary"

"Current directory:" | Out-File $Out -Append -Encoding UTF8
Get-Location | Out-File $Out -Append -Encoding UTF8

"" | Out-File $Out -Append -Encoding UTF8
"Python file count under app:" | Out-File $Out -Append -Encoding UTF8
(Get-ChildItem .\app -Recurse -Filter *.py | Measure-Object).Count |
Out-File $Out -Append -Encoding UTF8

"" | Out-File $Out -Append -Encoding UTF8
"Top-level app folders:" | Out-File $Out -Append -Encoding UTF8
Get-ChildItem .\app -Directory |
Select-Object FullName |
Format-Table -AutoSize |
Out-String -Width 300 |
Out-File $Out -Append -Encoding UTF8

Add-Section "2. Python Files Under app"

Get-ChildItem .\app -Recurse -Filter *.py |
Select-Object FullName |
Sort-Object FullName |
Format-Table -AutoSize |
Out-String -Width 300 |
Out-File $Out -Append -Encoding UTF8

Add-AppSearch "3. Episode Evidence Writers and References" "episode_evidence|EpisodeEvidence|INSERT INTO episode_evidence|source_excerpt|evidence_summary|evidence_source_type|idg_reviewed|medical_director_reviewed"

Add-AppSearch "4. Findings Writers and Significant Change References" "INSERT INTO findings|save_findings|FindingCandidate|is_significant_change|significant_change_events|finding_type|observed_at"

Add-AppSearch "5. Communication Log Bridge Search" "CommunicationsLog|communications_logs|handle_commlog|commlog|episode_evidence|findings|clinical_reasoning|requires_idg_review|evidence_ref"

Add-AppSearch "6. CHHA Bridge Search" "chha_visit_outcomes|chha_visit_task_results|CHHAVisitOutcome|CHHAVisitTaskResult|CHHA|HHA|AIDE|episode_evidence|findings|clinical_reasoning|requires_idg_review"

Add-AppSearch "7. IDG Evidence Bridge Search" "episode_evidence|findings|clinical_reasoning_results|requires_idg_review|idg_reviewed|IDGReview|IDGNote|idg_review|idg_meeting"

Add-AppSearch "8. Task Evidence Linkage Search" "evidence_ref_type|evidence_ref_id|complete_task_with_evidence|task_completion_evidence|reference_type|reference_id|clinical_followup|CLINICAL_FOLLOWUP"

Add-AppSearch "9. POC Evidence and Review Search" "plan_of_care_updates|poc|POC|requires_poc_update|poc_review|hospice_poc_problem|poc_generation|poc_engine"

Add-AppSearch "10. RN Review and MD Review Search" "requires_rn_review|requires_md_review|accepted_by|accepted_at|rejected_by|rejected_at|rejection_reason|medical_director_reviewed"

Add-AppSearchContext "11. chha_outcome_service.py Focused Context" ".\app\services\chha_outcome_service.py" "episode_evidence|findings|clinical_reasoning|CHHAVisitOutcome|CHHAVisitTaskResult|db.add|INSERT|audit|task|CLINICAL_FOLLOWUP|CHHA_OUTCOME_ALERT"

Add-AppSearchContext "12. communications_log_service.py Focused Context" ".\app\services\communications_log_service.py" "create_commlog_alerts|handle_commlog_for_tasks|episode_evidence|findings|clinical_reasoning|db.add|commit|refresh"

Add-AppSearchContext "13. commlog_to_task_bridge.py Focused Context" ".\app\services\commlog_to_task_bridge.py" "episode_evidence|findings|clinical_reasoning|Task|task|CommunicationsLog|commlog|evidence_ref|source|reference"

Add-AppSearchContext "14. clinical_reasoning_engine.py Focused Context" ".\app\services\clinical_reasoning_engine.py" "def save_findings|INSERT INTO findings|significant_change|requires_idg_review|episode_evidence|source|FindingCandidate"

Add-AppSearchContext "15. visits.py Clinical Reasoning Entry Points" ".\app\api\visits.py" "_run_clinical_reasoning|_get_or_create_clinical_reasoning|clinical_reasoning_engine|CHHAOutcome|upsert_chha|episode_evidence|findings"

Add-PsqlQuery "16. DB Tables Matching UCIER Terms" "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND (
    table_name ILIKE '%evidence%'
    OR table_name ILIKE '%finding%'
    OR table_name ILIKE '%reason%'
    OR table_name ILIKE '%interpret%'
    OR table_name ILIKE '%problem%'
    OR table_name ILIKE '%note%'
    OR table_name ILIKE '%visit%'
    OR table_name ILIKE '%comm%'
    OR table_name ILIKE '%chha%'
    OR table_name ILIKE '%idg%'
)
ORDER BY table_name;
"

Add-PsqlQuery "17. clinical_notes Constraints" "
SELECT
    conname,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'clinical_notes'::regclass
ORDER BY conname;
"

Add-PsqlQuery "18. communications_logs Columns" "
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'communications_logs'
ORDER BY ordinal_position;
"

Add-PsqlQuery "19. episode_evidence Columns" "
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'episode_evidence'
ORDER BY ordinal_position;
"

Add-PsqlQuery "20. episode_evidence Current Source Types" "
SELECT
    evidence_source_type,
    discipline,
    COUNT(*) AS count
FROM episode_evidence
GROUP BY evidence_source_type, discipline
ORDER BY count DESC;
"

Add-PsqlQuery "21. episode_evidence Foreign Keys" "
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name = 'episode_evidence'
ORDER BY tc.table_name, kcu.column_name;
"

Add-PsqlQuery "22. findings Columns" "
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'findings'
ORDER BY ordinal_position;
"

Add-PsqlQuery "23. significant_change_events Columns" "
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'significant_change_events'
ORDER BY ordinal_position;
"

Add-PsqlQuery "24. clinical_reasoning_results Columns" "
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'clinical_reasoning_results'
ORDER BY ordinal_position;
"

Add-PsqlQuery "25. CHHA Table Columns" "
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN (
    'chha_visit_outcomes',
    'chha_visit_task_results',
    'chha_pocs'
)
ORDER BY table_name, ordinal_position;
"

Add-PsqlQuery "26. CHHA Row Counts" "
SELECT
    'chha_visit_outcomes' AS table_name,
    COUNT(*) AS row_count
FROM chha_visit_outcomes
UNION ALL
SELECT
    'chha_visit_task_results' AS table_name,
    COUNT(*) AS row_count
FROM chha_visit_task_results
UNION ALL
SELECT
    'chha_pocs' AS table_name,
    COUNT(*) AS row_count
FROM chha_pocs;
"

Add-PsqlQuery "27. Communication Log Row Counts by Status and Type" "
SELECT
    status,
    event_type,
    focus_area,
    COUNT(*) AS row_count
FROM communications_logs
GROUP BY status, event_type, focus_area
ORDER BY row_count DESC;
"

Add-PsqlQuery "28. IDG Tables" "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name ILIKE '%idg%'
ORDER BY table_name;
"

Add-PsqlQuery "29. Task Columns Related to Evidence and References" "
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'tasks'
AND (
    column_name ILIKE '%evidence%'
    OR column_name ILIKE '%reference%'
    OR column_name ILIKE '%reason%'
    OR column_name ILIKE '%status%'
    OR column_name ILIKE '%task%'
    OR column_name ILIKE '%discipline%'
    OR column_name ILIKE '%alert%'
)
ORDER BY ordinal_position;
"

Add-Section "30. Discovery Interpretation Checklist"

@"
Use this checklist to classify the implementation path:

[ ] communications_logs -> episode_evidence exists
[ ] communications_logs -> findings exists
[ ] communications_logs -> clinical_reasoning exists
[ ] chha_visit_outcomes -> episode_evidence exists
[ ] chha_visit_outcomes -> findings exists
[ ] chha_visit_outcomes -> RN task exists
[ ] clinical_reasoning_results.requires_idg_review triggers IDG workflow
[ ] episode_evidence appears in IDG dashboard/review
[ ] findings appear in IDG dashboard/review
[ ] tasks support evidence_ref_type and evidence_ref_id
[ ] CHHA remains observational only, no direct diagnostic interpretation
[ ] communication log can become observation evidence for RN/IDG discussion
"@ | Out-File $Out -Append -Encoding UTF8

Add-Section "31. Recommended Classification Rules"

@"
DO NOT create new tables until reuse is ruled out:

Do not create patient_evidence_registry until episode_evidence is confirmed insufficient.
Do not create patient_signal_registry until findings is confirmed insufficient.
Do not create a new IDG queue until existing IDG review/task/dashboard paths are confirmed insufficient.
Do not make CHHA create clinical findings directly.
Do allow CHHA and communication-log content to create observation evidence candidates.
Do require RN/LVN/IDG review before clinical interpretation.
"@ | Out-File $Out -Append -Encoding UTF8

Add-Section "32. End of Packet"

"Discovery packet complete." | Out-File $Out -Append -Encoding UTF8
"Output file: $Out" | Out-File $Out -Append -Encoding UTF8

Write-Host "Created: $Out"