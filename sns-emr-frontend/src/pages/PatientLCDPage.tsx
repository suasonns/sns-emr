import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Divider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { evaluateLCD, type LCDEvaluationResponse } from "../api/eligibility";

const initialPatient = {
  id: "pt-123",
  tenant_id: "tenant-1",
  primary_diagnosis_description: "CHF with edema and dyspnea",
  primary_diagnosis_code: "I50.9",
  kps: "30",
  pps: "30",
  weight_loss_percent_6_months: "12",
  dependent_count: "2",
};

export default function PatientLCDPage() {
  const [patient, setPatient] = useState(initialPatient);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LCDEvaluationResponse | null>(null);

  const updateField = (field: string, value: string) => {
    setPatient((current) => ({ ...current, [field]: value }));
  };

  const handleEvaluate = async () => {
    try {
      setLoading(true);
      setError(null);

      const payload: Record<string, unknown> = { ...patient };
      Object.keys(payload).forEach((key) => {
        if (key === "kps" || key === "pps" || key === "weight_loss_percent_6_months" || key === "dependent_count") {
          const num = Number(payload[key]);
          payload[key] = Number.isFinite(num) ? num : payload[key];
        }
      });

      const response = await evaluateLCD(payload, {}, new Date().toISOString().slice(0, 10));
      setResult(response);
    } catch (err) {
      console.error("LCD evaluation failed", err);
      setError("Unable to evaluate the LCD guideline for this patient.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Patient LCD Evaluation</Typography>
          <Typography variant="body1" color="text.secondary">
            Evaluate the real hospice LCD registry against the patient diagnosis and clinical findings.
          </Typography>
        </Box>

        <Card>
          <CardContent>
            <Stack spacing={2}>
              <TextField
                label="Patient ID"
                value={patient.id}
                onChange={(e) => updateField("id", e.target.value)}
              />
              <TextField
                label="Diagnosis description"
                value={patient.primary_diagnosis_description}
                onChange={(e) => updateField("primary_diagnosis_description", e.target.value)}
              />
              <TextField
                label="Diagnosis code"
                value={patient.primary_diagnosis_code}
                onChange={(e) => updateField("primary_diagnosis_code", e.target.value)}
              />
              <TextField
                label="KPS"
                type="number"
                value={patient.kps}
                onChange={(e) => updateField("kps", e.target.value)}
              />
              <TextField
                label="PPS"
                type="number"
                value={patient.pps}
                onChange={(e) => updateField("pps", e.target.value)}
              />
              <TextField
                label="Weight loss % (6 months)"
                type="number"
                value={patient.weight_loss_percent_6_months}
                onChange={(e) => updateField("weight_loss_percent_6_months", e.target.value)}
              />
              <TextField
                label="ADL dependency count"
                type="number"
                value={patient.dependent_count}
                onChange={(e) => updateField("dependent_count", e.target.value)}
              />
              <Button variant="contained" size="large" onClick={handleEvaluate} disabled={loading}>
                {loading ? "Evaluating..." : "Evaluate LCD"}
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {error && <Alert severity="error">{error}</Alert>}

        {result && (
          <Card>
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>LCD Result</Typography>
                <Typography><strong>Selected guideline:</strong> {result.selected_guideline || "-"}</Typography>
                <Typography><strong>Eligible:</strong> {String(result.eligible ?? "-")}</Typography>
                <Typography><strong>LCD ID:</strong> {result.lcd_id || "-"}</Typography>
                <Typography><strong>LCD title:</strong> {result.lcd_title || "-"}</Typography>
                <Typography><strong>Source document:</strong> {result.source_document || "-"}</Typography>
                <Typography><strong>Reference:</strong> {result.lcd_reference || "-"}</Typography>

                <Divider />

                {result.criteria_summary?.group_results?.map((group) => (
                  <Box key={`${group.group_id ?? "group"}-${group.group_name ?? "name"}`}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                      {group.group_name || "Group"} ({group.passed ? "PASS" : "FAIL"})
                    </Typography>
                    {group.criteria?.map((criterion) => (
                      <Typography key={criterion.criterion_id ?? criterion.description ?? "criterion"} variant="body2">
                        - {criterion.description}: {String(criterion.matched ?? false)}
                      </Typography>
                    ))}
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        )}
      </Stack>
    </Container>
  );
}
