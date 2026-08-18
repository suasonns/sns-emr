import React from "react";

const OPTIONS = [
  { value: "update", label: "Update Assessment" },
  { value: "recert", label: "Recertification Assessment" },
];

const styles = {
  shell: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: 6,
    background: "#0F172A",
    border: "1px solid #1E293B",
    borderRadius: 999,
    boxShadow: "0 10px 24px rgba(15, 23, 42, 0.18)",
    flexWrap: "wrap",
  },
  button: {
    border: "none",
    borderRadius: 999,
    padding: "10px 16px",
    fontSize: 12,
    fontWeight: 700,
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
};

export default function AssessmentTypeToggle({ value = "update", onChange }) {
  return (
    <div style={styles.shell}>
      {OPTIONS.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange?.(option.value)}
            style={{
              ...styles.button,
              background: active ? "linear-gradient(135deg, #0D9488 0%, #10B7A2 100%)" : "transparent",
              color: active ? "#FFFFFF" : "#CBD5E1",
              boxShadow: active ? "0 8px 20px rgba(13, 148, 136, 0.28)" : "none",
            }}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
