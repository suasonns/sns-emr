import React from "react";
import "./ClinicalCommandWorkspace.css";

export function ClinicalCommandWorkspace({ density, ariaLabel, className = "", children }) {
  const disciplineDensityClass = className ? `${className}--${density}` : "";
  return (
    <div className="clinical-command-container">
      <main className={`clinical-command clinical-command--${density} ${className} ${disciplineDensityClass}`} aria-label={ariaLabel}>
        {children}
      </main>
    </div>
  );
}

export function ClinicalCommandHeader({ className = "", children }) {
  return <header className={`clinical-command-header ${className}`}>{children}</header>;
}

export function ClinicalCommandContextBar({ className = "", ariaLabel, children }) {
  return <section className={`clinical-command-context ${className}`} aria-label={ariaLabel}>{children}</section>;
}

export function ClinicalCommandLayout({ className = "", children }) {
  return <div className={`clinical-command-layout ${className}`}>{children}</div>;
}
