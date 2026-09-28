import { useRef, useState } from "react";
import { X } from "lucide-react";
import { Popover, PopoverTrigger, PopoverContent } from "../../ui/popover";
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from "../../ui/command";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { Checkbox } from "../../ui/checkbox";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../../ui/select";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from "../../ui/alert-dialog";

// A1005/A1010 owner-approved exclusivity model (owner design decision
// 2026-09-25, superseding the earlier "family may respond for either
// marker" draft):
// - "None of the above" (race only) and "Patient declines to respond" are
//   both definitive, exclusive answers -- selecting either clears every
//   other selection (including each other), and while "Patient declines
//   to respond" is selected every other option is disabled (not merely
//   cleared), since CMS HOPE guidance says only the declined response is
//   coded and no other source is substituted for it.
// - "Patient unable to respond" is NOT exclusive: a caregiver,
//   responsible party, or medical record may still supply the real
//   category/categories, coded together with this marker per CMS HOPE
//   guidance. Selecting it requires a concise information-source
//   attribution (relationship/source picker, free text only for
//   "Other documented source").
export const NONE_OF_THE_ABOVE = "None of the above";
export const PATIENT_DECLINES = "Patient declines to respond";
export const PATIENT_UNABLE = "Patient unable to respond";
const EXCLUSIVE_OPTIONS = [PATIENT_DECLINES, NONE_OF_THE_ABOVE];

export const INFORMATION_SOURCE_OPTIONS = [
  "Daughter",
  "Son",
  "Spouse or partner",
  "Other family member",
  "Caregiver",
  "Authorized representative",
  "Responsible party",
  "Facility staff",
  "Medical record",
  "Other documented source",
];

// Owner threshold: 0-3 selections stay frictionless. A 4th (or later, in
// the same open editing session) triggers one concise confirmation --
// never a hard cap, never a repeat prompt once confirmed this session.
const FRICTIONLESS_LIMIT = 3;

export function toggleDemographicValue(current, item) {
  const list = current || [];
  if (list.includes(item)) return list.filter((v) => v !== item);
  if (EXCLUSIVE_OPTIONS.includes(item)) return [item];
  return [...list.filter((v) => !EXCLUSIVE_OPTIONS.includes(v)), item];
}

// Compact multi-select for HOPE A1005 Ethnicity / A1010 Race. Replaces the
// unbounded checkbox wall with a searchable popover + visible selection
// chips, per owner direction: fast/accurate/minimal-burden documentation,
// not maximum data capture. The full CMS response set is always present in
// the popover -- nothing is truncated, ranked by presumed likelihood, or
// pre-selected.
export default function DemographicMultiSelect({
  title,
  itemCode,
  options,
  value,
  onChange,
  disabled,
  informationSource,
  informationSourceOther,
  onInformationSourceChange,
  onInformationSourceOtherChange,
}) {
  const selected = value || [];
  const [search, setSearch] = useState("");
  const [pendingSelection, setPendingSelection] = useState(null);
  // Once the nurse confirms an extended (4+) selection, don't ask again
  // for this field while this screen instance stays mounted.
  const confirmedExtendedRef = useRef(false);

  const declinesSelected = selected.includes(PATIENT_DECLINES);
  const unableSelected = selected.includes(PATIENT_UNABLE);

  function handleToggle(item) {
    if (disabled) return;
    const isLockedOff = declinesSelected && item !== PATIENT_DECLINES;
    if (isLockedOff) return;
    const isAdding = !selected.includes(item);
    const next = toggleDemographicValue(selected, item);
    if (isAdding && next.length > FRICTIONLESS_LIMIT && !confirmedExtendedRef.current) {
      setPendingSelection(next);
      return;
    }
    onChange?.(next);
  }

  function confirmPending() {
    confirmedExtendedRef.current = true;
    if (pendingSelection) onChange?.(pendingSelection);
    setPendingSelection(null);
  }

  function cancelPending() {
    setPendingSelection(null);
  }

  function removeChip(item) {
    if (disabled) return;
    onChange?.(selected.filter((v) => v !== item));
  }

  return (
    <div className="rnica-demo-multiselect">
      <Popover>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={disabled}
            className="rnica-demo-multiselect__trigger"
            aria-label={`Select applicable ${title.toLowerCase()} categories (${itemCode})`}
          >
            <span>Select applicable categories</span>
            {selected.length > 0 && <Badge variant="teal">{selected.length}</Badge>}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="rnica-demo-multiselect__popover">
          <Command shouldFilter>
            <CommandInput
              placeholder={`Search ${title.toLowerCase()}\u2026`}
              value={search}
              onValueChange={setSearch}
              aria-label={`Search ${title.toLowerCase()} categories`}
            />
            <CommandList>
              <CommandEmpty>No matches.</CommandEmpty>
              <CommandGroup>
                {options.map((opt) => {
                  const isChecked = selected.includes(opt);
                  const isLockedOff = declinesSelected && opt !== PATIENT_DECLINES;
                  return (
                    <CommandItem
                      key={opt}
                      value={opt}
                      disabled={disabled || isLockedOff}
                      onSelect={() => handleToggle(opt)}
                    >
                      <Checkbox checked={isChecked} disabled={disabled || isLockedOff} className="pointer-events-none" />
                      <span>{opt}</span>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <div className="rnica-demo-multiselect__selected" aria-label={`Selected ${title.toLowerCase()} categories`}>
        {selected.length === 0 && <span className="rnica-demo-multiselect__empty">None selected</span>}
        {selected.map((opt) => (
          <Badge key={opt} variant="neutral" className="rnica-demo-multiselect__chip">
            <span>{opt}</span>
            {!disabled && (
              <button
                type="button"
                aria-label={`Remove ${opt}`}
                onClick={() => removeChip(opt)}
                className="rnica-demo-multiselect__chip-remove"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </Badge>
        ))}
      </div>

      {unableSelected && (
        <div className="rnica-demo-multiselect__source">
          <label className="rnica-demo-multiselect__source-label" htmlFor={`${itemCode}-info-source`}>
            Information source
          </label>
          <Select
            value={informationSource || undefined}
            disabled={disabled}
            onValueChange={onInformationSourceChange}
          >
            <SelectTrigger id={`${itemCode}-info-source`}>
              <SelectValue placeholder="Select source&hellip;" />
            </SelectTrigger>
            <SelectContent>
              {INFORMATION_SOURCE_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {informationSource === "Other documented source" && (
            <input
              type="text"
              className="rnica-demo-multiselect__source-other"
              placeholder="Describe source"
              value={informationSourceOther || ""}
              disabled={disabled}
              onChange={(e) => onInformationSourceOtherChange?.(e.target.value)}
            />
          )}
        </div>
      )}

      <AlertDialog
        open={pendingSelection !== null}
        onOpenChange={(open) => {
          if (!open) cancelPending();
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm additional {title.toLowerCase()} categories</AlertDialogTitle>
            <AlertDialogDescription>
              You selected more than three categories. Confirm that all selected categories were reported by the
              patient, caregiver, responsible party, or authorized source.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={cancelPending}>Review selections</AlertDialogCancel>
            <AlertDialogAction onClick={confirmPending}>Confirm selections</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
