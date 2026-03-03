"""
Calculator result exporter — TXT and HTML output.

Pure Python module (no Qt dependency). Generates:
- Structured TXT for script consumption
- Styled HTML for presentation-grade reports

Cross-platform compatible (Mac, Windows, Linux).
"""

import html
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# ────────────────────────────────────────────────────────────────
#  Data class
# ────────────────────────────────────────────────────────────────


@dataclass
class ExportData:
    """All data needed to export a calculator result."""

    calculator_name: str
    """Human-readable calculator name, e.g. 'Nominal Point Density (NPD)'."""

    calculator_slug: str
    """Short slug for filenames, e.g. 'npd'."""

    sensor_label: str
    """Display name of the selected sensor, or 'Manual Entry'."""

    sensor_slug: str
    """Slug for filenames, e.g. 'hesai_xt32_m2x' or 'manual_entry'."""

    inputs: list[tuple[str, str]]
    """Ordered list of (label, formatted_value) for input parameters."""

    results: list[tuple[str, str]]
    """Ordered list of (label, formatted_value) for computed results."""

    math_formula: str
    """The math model formula string."""

    assumptions: list[str]
    """List of assumption strings."""

    references: list[str] = field(default_factory=list)
    """List of reference strings (may be empty)."""

    configuration_label: str = ""
    """Optional config/lens label, e.g. 'Single Return @ 10 Hz'."""

    sensor_category: str = ""
    """Sensor category label, e.g. 'LiDAR', 'Camera', 'POS / INS'."""


def default_filename(data: ExportData, extension: str) -> str:
    """Generate the default filename: {calculator}-{sensor}-{date}.{ext}."""
    today = datetime.now().strftime("%Y-%m-%d")
    slug = data.sensor_slug or "manual_entry"
    # Sanitize slug for safe filenames
    slug = slug.replace(" ", "_").replace("/", "_").replace("\\", "_")
    return f"{data.calculator_slug}-{slug}-{today}.{extension}"


# ────────────────────────────────────────────────────────────────
#  TXT Export
# ────────────────────────────────────────────────────────────────


def export_txt(data: ExportData, path: Path) -> None:
    """Write a structured TXT report to *path*."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    w = 20  # label column width

    lines: list[str] = []
    sep = "=" * 50

    lines.append(sep)
    lines.append(f"2SP LiDAR Calculator — {data.calculator_name}")
    lines.append(f"Generated: {now}")
    lines.append(sep)
    lines.append("")

    # Sensor
    lines.append("[SENSOR]")
    if data.sensor_category:
        lines.append(f"{'Category':<{w}}: {data.sensor_category}")
    lines.append(f"{'Sensor':<{w}}: {data.sensor_label}")
    if data.configuration_label:
        lines.append(f"{'Configuration':<{w}}: {data.configuration_label}")
    lines.append("")

    # Inputs
    lines.append("[INPUTS]")
    for label, value in data.inputs:
        lines.append(f"{label:<{w}}: {value}")
    lines.append("")

    # Results
    lines.append("[RESULTS]")
    for label, value in data.results:
        lines.append(f"{label:<{w}}: {value}")
    lines.append("")

    # Model
    lines.append("[MODEL]")
    lines.append(f"{'Formula':<{w}}: {data.math_formula}")
    lines.append("")

    # Assumptions
    lines.append("[ASSUMPTIONS]")
    for a in data.assumptions:
        lines.append(f"- {a}")
    lines.append("")

    # References
    lines.append("[REFERENCES]")
    if data.references:
        for r in data.references:
            lines.append(f"- {r}")
    else:
        lines.append("(none)")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# ────────────────────────────────────────────────────────────────
#  HTML Export
# ────────────────────────────────────────────────────────────────


def export_html(data: ExportData, path: Path) -> None:
    """Write a styled standalone HTML report to *path*."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    e = html.escape  # shorthand

    # Build input rows
    input_rows = "\n".join(
        f'<tr><td class="key">{e(label)}</td>'
        f'<td class="val">{e(value)}</td></tr>'
        for label, value in data.inputs
    )

    # Build result cards
    result_cards = "\n".join(
        f"""<div class="result-card">
            <div class="result-label">{e(label)}</div>
            <div class="result-value">{e(value)}</div>
        </div>"""
        for label, value in data.results
    )

    # Build assumptions list
    assumptions_items = "\n".join(
        f"<li>{e(a)}</li>" for a in data.assumptions
    )

    # Build references
    if data.references:
        ref_items = "\n".join(f"<li>{e(r)}</li>" for r in data.references)
        references_html = f"""
        <div class="section">
            <h2 class="section-title">
                <span class="section-icon">📄</span> References
            </h2>
            <ul class="ref-list">{ref_items}</ul>
        </div>"""
    else:
        references_html = ""

    # Sensor line
    sensor_line = e(data.sensor_label)
    if data.configuration_label:
        sensor_line += f' <span class="config-badge">{e(data.configuration_label)}</span>'

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(data.calculator_name)} — 2SP Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-page: #FFFFFF;
    --bg-card: #F7F8FA;
    --bg-surface: #EEF1F5;
    --accent: #1B5E94;
    --accent-light: #2A7ABF;
    --accent-glow: rgba(27, 94, 148, 0.08);
    --accent-subtle: rgba(27, 94, 148, 0.04);
    --text-primary: #1A1D23;
    --text-secondary: #5A6170;
    --text-muted: #8B919E;
    --border: #DDE1E8;
    --border-light: #E8ECF0;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'DM Sans', -apple-system, sans-serif;
    background: var(--bg-page);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
}}

/* ── Page layout ─────────────────────────────── */
.page {{
    max-width: 820px;
    margin: 0 auto;
    padding: 48px 32px 64px;
}}

/* ── Header ──────────────────────────────────── */
.header {{
    margin-bottom: 40px;
    padding-bottom: 24px;
    border-bottom: 2px solid var(--border);
}}

.brand {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 16px;
}}

.title {{
    font-family: 'DM Sans', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}}

.meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    font-size: 13px;
    color: var(--text-secondary);
}}

.meta-item {{
    display: flex;
    align-items: center;
    gap: 6px;
}}

.meta-icon {{
    font-size: 14px;
}}

.config-badge {{
    display: inline-block;
    background: var(--accent-glow);
    color: var(--accent);
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 4px;
    letter-spacing: 0.3px;
}}

/* ── Sections ────────────────────────────────── */
.section {{
    margin-bottom: 32px;
}}

.section-title {{
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.section-icon {{
    font-size: 14px;
}}

/* ── Results grid ────────────────────────────── */
.results-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 8px;
}}

.result-card {{
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 10px;
    padding: 20px;
}}

.result-card:first-child {{
    border-color: var(--accent);
    background: linear-gradient(
        135deg,
        var(--accent-subtle) 0%,
        var(--bg-card) 100%
    );
}}

.result-label {{
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}}

.result-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    color: var(--accent-light);
    letter-spacing: -0.5px;
}}

.result-card:first-child .result-value {{
    font-size: 28px;
    color: var(--accent);
}}

/* ── Inputs table ────────────────────────────── */
.inputs-table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 8px;
    overflow: hidden;
}}

.inputs-table tr {{
    border-bottom: 1px solid var(--border-light);
}}

.inputs-table tr:last-child {{
    border-bottom: none;
}}

.inputs-table td {{
    padding: 10px 16px;
    font-size: 13px;
}}

.inputs-table td.key {{
    color: var(--text-secondary);
    font-weight: 500;
    width: 45%;
}}

.inputs-table td.val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    text-align: right;
}}

/* ── Model box ───────────────────────────────── */
.model-box {{
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 500;
    color: var(--accent);
    letter-spacing: 0.3px;
}}

/* ── Assumptions ─────────────────────────────── */
.assumptions-list, .ref-list {{
    list-style: none;
    padding: 0;
}}

.assumptions-list li, .ref-list li {{
    position: relative;
    padding: 6px 0 6px 20px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
}}

.assumptions-list li::before {{
    content: '—';
    position: absolute;
    left: 0;
    color: var(--text-muted);
}}

.ref-list li::before {{
    content: '›';
    position: absolute;
    left: 2px;
    color: var(--accent);
    font-weight: 700;
}}

/* ── Footer ──────────────────────────────────── */
.footer {{
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: var(--text-muted);
}}

.footer-brand {{
    font-weight: 700;
    letter-spacing: 1px;
    color: var(--accent);
}}

/* ── Print ────────────────────────────────────── */
@media print {{
    .page {{
        padding: 24px 0;
    }}

    .result-card {{
        border-color: #ccc;
    }}
}}
</style>
</head>
<body>
<div class="page">
    <header class="header">
        <div class="brand">2SP LiDAR Calculator</div>
        <h1 class="title">{e(data.calculator_name)}</h1>
        <div class="meta">
            <span class="meta-item">
                <span class="meta-icon">📅</span> {e(now)}
            </span>
            <span class="meta-item">
                <span class="meta-icon">📡</span> {sensor_line}
            </span>
        </div>
    </header>

    <div class="section">
        <h2 class="section-title">
            <span class="section-icon">📊</span> Results
        </h2>
        <div class="results-grid">
            {result_cards}
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">
            <span class="section-icon">⚙️</span> Input Parameters
        </h2>
        <table class="inputs-table">
            {input_rows}
        </table>
    </div>

    <div class="section">
        <h2 class="section-title">
            <span class="section-icon">🔢</span> Math Model
        </h2>
        <div class="model-box">{e(data.math_formula)}</div>
    </div>

    <div class="section">
        <h2 class="section-title">
            <span class="section-icon">📋</span> Assumptions
        </h2>
        <ul class="assumptions-list">{assumptions_items}</ul>
    </div>

    {references_html}

    <footer class="footer">
        <span class="footer-brand">2SP Professional Tools</span>
        <span>Generated by 2SP LiDAR Calculator v0.1.0</span>
    </footer>
</div>
</body>
</html>"""

    path.write_text(doc, encoding="utf-8")
