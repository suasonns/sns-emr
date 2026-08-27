import React, { useEffect, useRef, useState } from "react";
import { searchIcd10Diagnoses } from "../api/icd10";

/**
 * Generic ICD-10 typeahead input. As the user types a diagnosis description
 * or partial ICD-10 code, it suggests matching official ICD-10-CM entries
 * from the icd10_master table (search_icd10_diagnoses). Selecting a
 * suggestion calls onSelectSuggestion with the full match ({icd10_code,
 * diagnosis_description, display_name, ...}) and fills the input with
 * "<description> (<code>)" so it stays consistent with how coded diagnoses
 * are already displayed elsewhere on the Facesheet (Active Primary/Secondary
 * panels).
 *
 * Renders using the same `colors` theme object the rest of PatientFacesheet
 * uses, rather than hardcoded colors, so it fits either light/dark themes.
 */
export default function Icd10DiagnosisInput({
  value,
  onChange,
  onSelectSuggestion,
  colors,
  inputStyle,
  placeholder = "Start typing a diagnosis or ICD-10 code…",
  onKeyDown,
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (!value || value.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setLoading(true);
      searchIcd10Diagnoses(value)
        .then((results) => setSuggestions(results))
        .catch((err) => console.error("ICD-10 search failed:", err))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [value]);

  const pick = (suggestion) => {
    const label = suggestion.display_name
      || `${suggestion.diagnosis_description} (${suggestion.icd10_code})`;
    onChange(label);
    onSelectSuggestion && onSelectSuggestion(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div style={{ position: "relative" }}>
      <input
        value={value ?? ""}
        placeholder={placeholder}
        onChange={(event) => {
          onChange(event.target.value);
          setShowSuggestions(true);
        }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        onKeyDown={onKeyDown}
        style={inputStyle}
      />
      {showSuggestions && (loading || suggestions.length > 0) && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            zIndex: 30,
            background: colors?.cardBg || "#0b1522",
            border: `1px solid ${colors?.border || "#223449"}`,
            borderRadius: 8,
            marginTop: 4,
            maxHeight: 220,
            overflowY: "auto",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          }}
        >
          {loading && (
            <div style={{ padding: "8px 12px", fontSize: 12, color: colors?.label || "#8fa3b8" }}>
              Searching…
            </div>
          )}
          {!loading && suggestions.map((s) => (
            <div
              key={s.icd10_code}
              onMouseDown={() => pick(s)}
              style={{ padding: "8px 12px", fontSize: 12.5, color: colors?.white || "#e6edf3", cursor: "pointer" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(99,231,211,0.12)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <div>{s.diagnosis_description}</div>
              <div style={{ fontSize: 10.5, color: colors?.label || "#8fa3b8", marginTop: 2 }}>
                {s.icd10_code}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
