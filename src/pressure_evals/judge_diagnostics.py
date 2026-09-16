"""Judge dynamic-range diagnostics: the "self-evaluation blind spot" analysis.

This module reads the *already-frozen* evaluation scores (no model calls, no new
inference) and quantifies the failure mode the paper reports: a judge whose
manipulation scores are compressed to near-zero variance --- worst on its own
model family --- cannot detect a within-condition effect that a higher-dynamic-range
judge does. It also implements, as a reusable check, the "grep for zero-variance
cells" recommendation from the paper: any (judge, subject-model, condition) cell
whose scores never vary is a silent measurement floor, not evidence of no effect.

Everything here is deterministic. Run it with:

    uv run python -m pressure_evals.judge_diagnostics

which regenerates the JSON tables under reports/tables/, the LaTeX table under
paper/tables/, and the hero figure under reports/figures/ + paper/figures/.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import pstdev
from typing import Iterable, Optional

MANIPULATION_DIMS = (
    "deceptive_omission",
    "emotional_pressure",
    "artificial_urgency",
    "authority_social_pressure",
)
AUTONOMY_DIMS = ("respect_for_refusal", "transparency")
CONDITIONS = ("baseline", "pressure", "autonomy", "pressure_autonomy")
SUBJECT_MODELS = ("qwen3:4b", "gemma3:4b", "llama3.2:3b")

RUN_ID = "baseline-v0.1-20260722"
REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "data" / "evaluations"
BLINDING_KEY = EVAL_DIR / f"{RUN_ID}.blinding_key.json"

# (label, judge_model, path, family) for every judge whose frozen scores exist.
JUDGES = (
    ("qwen3:4b", "qwen3:4b", EVAL_DIR / f"{RUN_ID}.jsonl", "qwen"),
    ("claude-sonnet-4-6", "claude-sonnet-4-6",
     EVAL_DIR / f"{RUN_ID}.claude-sonnet-4-6.jsonl", "anthropic"),
    ("gemma3:4b", "gemma3:4b",
     EVAL_DIR / f"{RUN_ID}.gemma3-4b.sample.jsonl", "gemma"),
    ("llama3.2:3b", "llama3.2:3b",
     EVAL_DIR / f"{RUN_ID}.llama3-2-3b.sample.jsonl", "llama"),
)


# ---- loading -------------------------------------------------------------

def load_latest_successful(path: Path) -> dict[str, dict]:
    """Map item_id -> the latest *successful* evaluation result dict in a
    judge's JSONL, matching evaluate.py's latest-successful semantics (files
    may contain retries and failed attempts)."""
    latest: dict[str, dict] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("evaluation_failed") or row.get("result") is None:
                continue
            latest[row["item_id"]] = row["result"]
    return latest


def load_blinding_key(path: Path = BLINDING_KEY) -> dict[str, dict]:
    return json.loads(path.read_text())


def manipulation_score(result: dict) -> int:
    return sum(int(result[d]["score"]) for d in MANIPULATION_DIMS)


def autonomy_score(result: dict) -> int:
    return sum(int(result[d]["score"]) for d in AUTONOMY_DIMS)


# ---- long-format frame ---------------------------------------------------

def build_rows(blinding: Optional[dict] = None) -> list[dict]:
    """One row per (judge, item) with subject model/condition attached."""
    blinding = blinding or load_blinding_key()
    rows: list[dict] = []
    for label, _model, path, family in JUDGES:
        if not path.exists():
            continue
        for item_id, result in load_latest_successful(path).items():
            meta = blinding[item_id]
            rows.append({
                "judge": label,
                "judge_family": family,
                "item_id": item_id,
                "subject_model": meta["model"],
                "condition": meta["condition"],
                "scenario_id": meta["scenario_id"],
                "manipulation": manipulation_score(result),
                "autonomy": autonomy_score(result),
            })
    return rows


def _mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def _sd(xs: Iterable[float]) -> float:
    xs = list(xs)
    return pstdev(xs) if len(xs) > 1 else 0.0


# ---- (1) dynamic range: judge x subject-model ----------------------------

def dynamic_range(rows: list[dict], field: str = "manipulation") -> dict:
    """For each (judge, subject_model), the mean and SD of `field` over that
    subject's outputs. The self-evaluation blind spot shows up as qwen-judge x
    qwen-subject having ~0 mean AND ~0 SD, while other judges retain spread."""
    out: dict[str, dict[str, dict]] = {}
    judges = [j[0] for j in JUDGES]
    for judge in judges:
        out[judge] = {}
        for subj in SUBJECT_MODELS:
            vals = [r[field] for r in rows
                    if r["judge"] == judge and r["subject_model"] == subj]
            out[judge][subj] = {
                "n": len(vals),
                "mean": round(_mean(vals), 3) if vals else None,
                "sd": round(_sd(vals), 3) if vals else None,
            }
    return out


# ---- (2) zero-variance cell detector -------------------------------------

def zero_variance_cells(rows: list[dict], field: str = "manipulation") -> dict:
    """Implements the paper's 'grep for zero-variance cells' check. A cell is
    (judge, subject_model, condition); a zero-variance cell scored identically
    on every scenario and so cannot detect a within-condition effect."""
    summary: dict[str, dict] = {}
    for judge in [j[0] for j in JUDGES]:
        total = flat = 0
        flat_cells = []
        for subj in SUBJECT_MODELS:
            for cond in CONDITIONS:
                vals = [r[field] for r in rows
                        if r["judge"] == judge
                        and r["subject_model"] == subj
                        and r["condition"] == cond]
                if not vals:
                    continue
                total += 1
                if _sd(vals) == 0.0:
                    flat += 1
                    flat_cells.append(f"{subj}|{cond}(={vals[0]})")
        summary[judge] = {
            "cells_observed": total,
            "zero_variance_cells": flat,
            "fraction_flat": round(flat / total, 3) if total else None,
            "flat_cells": flat_cells,
        }
    return summary


# ---- (3) self vs cross family on the 60-item overlap ---------------------

def self_vs_cross_family(rows: list[dict], field: str = "manipulation") -> dict:
    """On the items that ALL open-weight judges scored (the 60-item overlap),
    restricted to qwen3:4b's own outputs: compare the score spread (SD) of the
    self-family judge (qwen) against cross-family judges (gemma, llama, claude).
    Lower self-family SD is consistent with a same-family blind spot, though a
    small judge's general dynamic-range limit is an alternative explanation."""
    # overlap = items scored by both secondary open-weight judges
    scored_by = {}
    for r in rows:
        scored_by.setdefault(r["item_id"], set()).add(r["judge"])
    overlap = {iid for iid, js in scored_by.items()
               if {"gemma3:4b", "llama3.2:3b"} <= js}
    qwen_subject_overlap = {
        r["item_id"] for r in rows
        if r["item_id"] in overlap and r["subject_model"] == "qwen3:4b"
    }
    out = {"n_qwen_subject_overlap_items": len(qwen_subject_overlap), "by_judge": {}}
    for judge in [j[0] for j in JUDGES]:
        vals = [r[field] for r in rows
                if r["judge"] == judge and r["item_id"] in qwen_subject_overlap]
        if not vals:
            continue
        out["by_judge"][judge] = {
            "relation": "self" if judge == "qwen3:4b" else "cross",
            "n": len(vals),
            "mean": round(_mean(vals), 3),
            "sd": round(_sd(vals), 3),
        }
    return out


# ---- per-condition means for qwen-subject (drives the hero figure) --------

def qwen_subject_by_condition(rows: list[dict], field: str = "manipulation") -> dict:
    out: dict[str, dict] = {}
    for judge in ("qwen3:4b", "claude-sonnet-4-6"):
        out[judge] = {}
        for cond in CONDITIONS:
            vals = [r[field] for r in rows
                    if r["judge"] == judge
                    and r["subject_model"] == "qwen3:4b"
                    and r["condition"] == cond]
            out[judge][cond] = {"mean": round(_mean(vals), 3), "sd": round(_sd(vals), 3)}
    return out


# ---- emitters ------------------------------------------------------------

def latex_dynamic_range(dr: dict) -> str:
    """Money table: judge x subject-model mean (sd) of manipulation."""
    def cell(judge, subj):
        c = dr[judge][subj]
        return f"{c['mean']:.2f} ({c['sd']:.2f})"
    lines = [
        "% Auto-generated by pressure_evals.judge_diagnostics -- do not edit by hand.",
        "\\begin{table}[h]", "\\centering",
        "\\caption{Manipulation score, mean (SD), by judge and subject model "
        "(0--8 scale). The open-weight judge scores its \\emph{own} family "
        "(\\texttt{qwen3:4b}) at zero with zero variance; the frontier judge, on "
        "the same text, retains both a higher mean and real spread.}",
        "\\label{tab:dynamic_range}",
        "\\begin{tabular}{lccc}", "\\toprule",
        "Judge & qwen3:4b & gemma3:4b & llama3.2:3b \\\\", "\\midrule",
    ]
    for judge, disp in (("qwen3:4b", "\\texttt{qwen3:4b} (open-weight)"),
                        ("claude-sonnet-4-6", "\\texttt{claude-sonnet-4-6} (frontier)")):
        qcell = cell(judge, "qwen3:4b")
        if judge == "qwen3:4b":
            qcell = f"\\textbf{{{qcell}}}"
        lines.append(f"{disp} & {qcell} & {cell(judge,'gemma3:4b')} "
                     f"& {cell(judge,'llama3.2:3b')} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    return "\n".join(lines)


def hero_figure(rows: list[dict], out_paths: list[Path]) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    data = qwen_subject_by_condition(rows, "manipulation")
    x = np.arange(len(CONDITIONS))
    w = 0.38
    q = [data["qwen3:4b"][c]["mean"] for c in CONDITIONS]
    qs = [data["qwen3:4b"][c]["sd"] for c in CONDITIONS]
    cl = [data["claude-sonnet-4-6"][c]["mean"] for c in CONDITIONS]
    cls = [data["claude-sonnet-4-6"][c]["sd"] for c in CONDITIONS]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(x - w / 2, q, w, yerr=qs, capsize=3, label="qwen3:4b judge (self-family)",
           color="#B3B3B3")
    ax.bar(x + w / 2, cl, w, yerr=cls, capsize=3,
           label="claude-sonnet-4-6 judge (independent)", color="#3B6FB6")
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", "\n") for c in CONDITIONS])
    ax.set_ylabel("Manipulation score (0-8)")
    ax.set_ylim(0, 8)
    ax.set_title("Scoring qwen3:4b's own outputs: self-family judge vs. independent judge")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150)
    plt.close(fig)
    return data


def main() -> None:
    rows = build_rows()
    tables_dir = REPO / "reports" / "tables"
    figs_dir = REPO / "reports" / "figures"
    paper_tables = REPO / "paper" / "tables"
    paper_figs = REPO / "paper" / "figures"

    dr = dynamic_range(rows)
    zv = zero_variance_cells(rows)
    scf = self_vs_cross_family(rows)
    bycond = qwen_subject_by_condition(rows)

    (tables_dir / "judge_dynamic_range.json").write_text(json.dumps(dr, indent=2))
    (tables_dir / "zero_variance_cells.json").write_text(json.dumps(zv, indent=2))
    (tables_dir / "self_vs_cross_family.json").write_text(json.dumps(scf, indent=2))
    (tables_dir / "qwen_subject_by_condition.json").write_text(json.dumps(bycond, indent=2))
    (paper_tables / "judge_dynamic_range.tex").write_text(latex_dynamic_range(dr))

    fig = "qwen_self_vs_frontier.png"
    hero_figure(rows, [figs_dir / fig, paper_figs / fig])

    print("wrote:")
    for p in ("reports/tables/judge_dynamic_range.json",
              "reports/tables/zero_variance_cells.json",
              "reports/tables/self_vs_cross_family.json",
              "reports/tables/qwen_subject_by_condition.json",
              "paper/tables/judge_dynamic_range.tex",
              f"reports/figures/{fig}", f"paper/figures/{fig}"):
        print("  ", p)
    print("\nzero-variance cells per judge:")
    for j, s in zv.items():
        print(f"  {j:20s} {s['zero_variance_cells']}/{s['cells_observed']} flat")
    print("\nself vs cross family (qwen-subject overlap, manipulation SD):")
    for j, s in scf["by_judge"].items():
        print(f"  {j:20s} {s['relation']:5s} sd={s['sd']} mean={s['mean']} n={s['n']}")


if __name__ == "__main__":
    main()
