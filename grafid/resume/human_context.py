"""Build human-facing dashboard summary text from deterministic sources."""

from __future__ import annotations

from grafid.resume.quality import normalize_note
from grafid.resume.summary_composition import CompositionInput, compose_workflow_summary
from grafid.resume.workflow_artifacts import WorkflowArtifact

WEAK_CONTEXT_MESSAGE = (
    "Not enough context found. Add an Exit Note or a short handoff note when you pause work."
)


def build_dashboard_summary(
    *,
    project_name: str = "",
    project_notes: str | None = None,
    last_session_label: str | None = None,
    session_started_at: str | None = None,
    last_refreshed_at: str | None = None,
    modified_files: tuple[str, ...] = (),
    exit_note: str | None,
    blocker: str | None,
    next_step: str | None,
    has_active_session: bool,
    artifacts: tuple[WorkflowArtifact, ...],
    open_task_count: int | None,
    has_scan: bool,
    git_label: str | None,
    task_markers: tuple[str, ...] = (),
    git_state: str | None = None,
    git_branch: str | None = None,
    git_is_repo: bool = False,
) -> dict[str, str | list[str] | list[dict[str, str]]]:
    """Return headline, summary_text, sources_used, and MVP sections for the UI."""
    composed = compose_workflow_summary(
        CompositionInput(
            project_name=project_name,
            exit_note=exit_note,
            next_step=next_step,
            blocker=blocker,
            has_active_session=has_active_session,
            session_started_at=session_started_at,
            last_refreshed_at=last_refreshed_at,
            project_notes=project_notes,
            artifacts=artifacts,
            task_markers=task_markers,
            open_task_count=open_task_count,
            has_scan=has_scan,
            modified_files=modified_files,
            git_label=git_label,
            git_state=git_state,
            git_branch=git_branch,
            git_is_repo=git_is_repo,
            last_session_label=last_session_label,
        )
    )

    summary_text = "\n".join(composed.primary_lines).strip()
    exit_clean = normalize_note(exit_note)
    if (
        composed.confidence == "weak"
        and not has_active_session
        and not exit_clean
    ):
        summary_text = WEAK_CONTEXT_MESSAGE

    mvp_sections = build_mvp_sections(
        project_name=project_name,
        last_session_label=last_session_label,
        where_left_off=list(composed.where_left_off),
        supporting_notes=list(composed.supporting_notes),
        technical_notes=list(composed.technical_notes),
        task_markers=task_markers,
        blocker=normalize_note(blocker),
        next_step=composed.suggested_next_step,
        modified_files=modified_files,
        confidence=composed.confidence,
    )

    return {
        "headline": composed.headline,
        "summary_text": summary_text,
        "sources_used": list(composed.sources_used),
        "confidence": composed.confidence,
        "mvp_sections": mvp_sections,
    }


def build_mvp_sections(
    *,
    project_name: str,
    last_session_label: str | None,
    where_left_off: list[str],
    supporting_notes: list[str],
    technical_notes: list[str],
    task_markers: tuple[str, ...],
    blocker: str | None,
    next_step: str | None,
    modified_files: tuple[str, ...],
    confidence: str,
) -> list[dict[str, str]]:
    """Structured sections: workflow first, diagnostics in expandable detail."""
    sections: list[dict[str, str]] = []

    if where_left_off:
        sections.append(
            {
                "title": "Where you left off",
                "body": "\n".join(where_left_off[:4]),
            }
        )

    if next_step:
        sections.append({"title": "Suggested next step", "body": next_step})

    if blocker:
        sections.append({"title": "Blocker", "body": blocker})

    if supporting_notes:
        sections.append(
            {
                "title": "Notes on file",
                "body": "\n".join(supporting_notes[:3]),
            }
        )

    if modified_files:
        sections.append(
            {
                "title": "Recent file changes",
                "body": "\n".join(modified_files[:5]),
            }
        )

    marker_title = (
        "Potential code markers"
        if confidence in ("low", "weak") and task_markers
        else "Code markers (detail)"
    )
    detail_lines = list(technical_notes)
    if task_markers:
        detail_lines.extend(task_markers[:5])
    if detail_lines:
        sections.append(
            {"title": marker_title, "body": "\n".join(detail_lines[:8])}
        )

    if last_session_label:
        sections.append({"title": "Session", "body": last_session_label})

    if confidence == "weak":
        sections.append({"title": "Context", "body": WEAK_CONTEXT_MESSAGE})
    elif confidence != "high":
        sections.append(
            {
                "title": "Context",
                "body": f"Confidence: {confidence} — add an Exit Note for a clearer resume next time.",
            }
        )

    if not sections:
        sections.append(
            {"title": "Project", "body": project_name or "Unknown project"},
        )

    return sections
