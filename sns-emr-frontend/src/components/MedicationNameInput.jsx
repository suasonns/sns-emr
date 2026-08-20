import React, { useEffect, useRef, useState } from "react";
import { searchDrugSuggestions, getDrugFamily } from "../api/medications";

/**
 * Medication name input with RxNorm typeahead suggestions.
 *
 * Includes a "Compounded / Off-Market Medication" toggle: compounded meds
 * (custom-mixed by a compounding pharmacy) will never appear in RxNorm or any
 * standard drug database, so when toggled on we skip the lookup entirely and
 * just accept free text — this is expected/normal, not an error state.
 *
 * Also shows a read-only "Same Therapeutic Family" box once a stock/curated
 * medication is recognized — listing other agency-stocked meds in the same
 * drug class, cheapest first, and flagging when the selected med (or an
 * alternative) isn't currently available in the pharmacy.
 */
export default function MedicationNameInput({
  value,
  onChange,
  onSelectSuggestion,
  inputStyle,
  labelStyle,
  placeholder = "Start typing a medication name…",
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isCompounded, setIsCompounded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [family, setFamily] = useState(null);
  const debounceRef = useRef(null);
  const familyDebounceRef = useRef(null);

  useEffect(() => {
    if (isCompounded || !value || value.trim().length < 3) {
      setSuggestions([]);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setLoading(true);
      searchDrugSuggestions(value)
        .then((results) => setSuggestions(results))
        .catch((err) => console.error("Drug search failed:", err))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [value, isCompounded]);

  useEffect(() => {
    if (isCompounded || !value || value.trim().length < 3) {
      setFamily(null);
      return;
    }
    if (familyDebounceRef.current) clearTimeout(familyDebounceRef.current);
    familyDebounceRef.current = setTimeout(() => {
      getDrugFamily(value)
        .then((result) => setFamily(result && result.alternatives.length > 0 ? result : null))
        .catch(() => setFamily(null));
    }, 350);
    return () => clearTimeout(familyDebounceRef.current);
  }, [value, isCompounded]);

  return (
    <div style={{ position: "relative" }}>
      <input
        style={inputStyle}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setShowSuggestions(true);
        }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        placeholder={isCompounded ? "Compounded medication (free text)" : placeholder}
      />
      {!isCompounded && showSuggestions && (loading || suggestions.length > 0) && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            zIndex: 20,
            background: "#0b1522",
            border: "1px solid #223449",
            borderRadius: 8,
            marginTop: 4,
            maxHeight: 220,
            overflowY: "auto",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          }}
        >
          {loading && <div style={{ padding: "8px 12px", fontSize: 12, color: "#8fa3b8" }}>Searching…</div>}
          {!loading &&
            suggestions.map((s) => (
              <div
                key={`${s.rxcui || s.name}`}
                onMouseDown={() => {
                  onChange(s.base_name || s.name);
                  onSelectSuggestion && onSelectSuggestion(s);
                  setShowSuggestions(false);
                }}
                style={{
                  padding: "8px 12px",
                  fontSize: 13,
                  color: "#e6edf3",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(99,231,211,0.12)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                {s.name}
                {s.is_stock && (
                  <span style={{ color: "#63e7d3", marginLeft: 6, fontWeight: 700, fontSize: 11 }}>★ Stock</span>
                )}
                {(s.strength || s.route) && (
                  <span style={{ color: "#8fa3b8", marginLeft: 6 }}>
                    {[s.strength, s.route].filter(Boolean).join(" · ")}
                  </span>
                )}
                {s.recommended_dosing && (
                  <div style={{ color: "#63e7d3", fontSize: 11, marginTop: 2 }}>
                    Recommended: {s.recommended_dosing}
                  </div>
                )}
              </div>
            ))}
        </div>
      )}
      <label
        style={{
          fontSize: 11,
          color: "#8fa3b8",
          ...labelStyle,
          display: (labelStyle && labelStyle.display) || "flex",
          alignItems: "center",
          gap: 6,
          marginTop: 6,
          textTransform: "none",
          fontWeight: 500,
        }}
      >
        <input
          type="checkbox"
          checked={isCompounded}
          onChange={(e) => {
            setIsCompounded(e.target.checked);
            setShowSuggestions(false);
          }}
        />
        Compounded / off-market medication (not in standard drug database — skip suggestions)
      </label>

      {family && (
        <div
          style={{
            marginTop: 8,
            padding: "8px 10px",
            borderRadius: 8,
            border: "1px solid #223449",
            background: "#0b1522",
          }}
        >
          <div style={{ fontSize: 11, color: "#8fa3b8", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.3 }}>
            {family.pharmacy_available === false
              ? "⚠ Not available in pharmacy — recommended alternatives (cheapest first)"
              : "Same therapeutic family (cheapest first)"}
          </div>
          {family.alternatives.map((alt) => (
            <div
              key={alt.name}
              style={{
                fontSize: 12,
                color: alt.pharmacy_available === false ? "#8fa3b8" : "#e6edf3",
                padding: "3px 0",
                display: "flex",
                justifyContent: "space-between",
                gap: 8,
              }}
            >
              <span>
                {alt.generic_name || alt.name}
                {alt.brand_name && ` (${alt.brand_name})`}
                {alt.strength ? ` — ${alt.strength}` : ""}
                {alt.pharmacy_available === false && (
                  <span style={{ color: "#f2a154", marginLeft: 6, fontWeight: 700 }}>Unavailable</span>
                )}
              </span>
              <span style={{ color: "#63e7d3", fontWeight: 700, whiteSpace: "nowrap" }}>
                {"$".repeat(alt.relative_cost_rank || 1)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

