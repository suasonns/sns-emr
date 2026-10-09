import { Alert, AlertDescription, AlertTitle } from "../../../components/ui/alert";

/**
 * Fixed, always-visible notice that this workspace shell is a synthetic,
 * read-only demonstration — never a patient record. Required by the
 * governing task to be visible without any user interaction.
 */
export function SyntheticDataNotice() {
  return (
    <Alert variant="info" data-testid="synthetic-data-notice">
      <AlertTitle>Synthetic read-only UI preview</AlertTitle>
      <AlertDescription>
        No patient record is loaded. No clinical documentation is saved.
      </AlertDescription>
    </Alert>
  );
}
