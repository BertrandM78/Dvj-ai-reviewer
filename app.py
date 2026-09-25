import hmac
import tempfile
from pathlib import Path

import streamlit as st

from src.document_normalizer import normalize_document
from src.document_parser import extract_pdf_text
from src.reviewer_v2 import review_v2
from src.rules.loader import load_rules


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DVJ Proposal Reviewer",
    page_icon="📄",
    layout="wide",
)


# ============================================================
# CONSTANTS
# ============================================================

STATUS_CONFIG = {
    "COMPLIANT": {
        "label": "Conforme",
        "icon": "🟢",
    },
    "NON_COMPLIANT": {
        "label": "À corriger",
        "icon": "🔴",
    },
    "NOT_EVALUATED": {
        "label": "À vérifier",
        "icon": "🟠",
    },
    "NOT_APPLICABLE": {
        "label": "Non applicable",
        "icon": "⚪",
    },
    "SUGGESTED": {
        "label": "Suggestion",
        "icon": "💡",
    },
    "NOT_SUGGESTED": {
        "label": "Non suggéré",
        "icon": "⚪",
    },
}


# ============================================================
# AUTHENTICATION
# ============================================================

def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("DVJ Proposal Reviewer")

    st.caption(
        "Assistant de relecture des propositions commerciales "
        "de DeVinci Junior"
    )

    password = st.text_input(
        "Mot de passe",
        type="password",
    )

    if st.button(
        "Se connecter",
        type="primary",
    ):
        if hmac.compare_digest(
            password,
            st.secrets["APP_PASSWORD"],
        ):
            st.session_state["authenticated"] = True
            st.rerun()

        else:
            st.error("Mot de passe incorrect.")

    return False


if not check_password():
    st.stop()


# ============================================================
# RULE METADATA
# ============================================================

rules = load_rules()

rules_by_id = {
    rule["id"]: rule
    for rule in rules
}


# ============================================================
# HELPERS
# ============================================================

def get_metadata(result: dict) -> dict:
    return rules_by_id.get(
        result.get("rule_id"),
        {},
    )


def get_status_config(status: str) -> dict:
    return STATUS_CONFIG.get(
        status,
        {
            "label": status,
            "icon": "⚪",
        },
    )


SEVERITY_ORDER = {
    "CRITICAL": 0,
    "MAJOR": 1,
    "MINOR": 2,
    "INFO": 3,
}


def sort_by_priority(results: list[dict]) -> list[dict]:
    """
    Sort results by business severity while preserving
    the original rule order within the same severity.
    """
    return sorted(
        results,
        key=lambda result: SEVERITY_ORDER.get(
            get_metadata(result).get("severity", "INFO"),
            99,
        ),
    )


def render_result(
    result: dict,
    *,
    expanded: bool = False,
) -> None:
    rule_id = result.get("rule_id", "UNKNOWN")
    status = result.get("status", "UNKNOWN")

    metadata = get_metadata(result)
    status_config = get_status_config(status)

    title = metadata.get("title", rule_id)
    section = metadata.get("section", "—")
    dimension = metadata.get("dimension", "—")

    reason = (
        result.get("reason")
        or result.get("reasoning")
        or "Aucune explication disponible."
    )

    evidence = result.get("evidence")
    recommendation = result.get("recommendation")

    expander_title = (
        f"{status_config['icon']} "
        f"{title}"
    )

    with st.expander(
        expander_title,
        expanded=expanded,
    ):
        # Essential information first
        st.caption(
            f"{status_config['label']} · {section}"
        )

        st.write(reason)

        if recommendation:
            st.markdown("**Action recommandée**")
            st.info(recommendation)

        # Evidence is useful, but secondary.
        if evidence:
            with st.expander("Voir la preuve"):
                if isinstance(
                    evidence,
                    (dict, list),
                ):
                    st.json(
                        evidence,
                        expanded=False,
                    )
                else:
                    st.write(evidence)

        # Technical metadata: deliberately discreet.
        st.caption(
            f"{rule_id} · {dimension}"
        )


# ============================================================
# HEADER
# ============================================================

st.title("DVJ Proposal Reviewer")

st.caption(
    "Vérifiez votre proposition commerciale avant validation."
)

st.divider()


# ============================================================
# UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Proposition commerciale",
    type=["pdf"],
    help="Format accepté : PDF",
)


if uploaded_file is not None:

    file_size_mb = (
        len(uploaded_file.getvalue())
        / (1024 * 1024)
    )

    st.caption(
        f"{uploaded_file.name} — "
        f"{file_size_mb:.1f} Mo"
    )

    analyze = st.button(
        "Analyser la proposition",
        type="primary",
        use_container_width=True,
    )

    if analyze:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temporary_file:

            temporary_file.write(
                uploaded_file.getvalue()
            )

            temporary_path = Path(
                temporary_file.name
            )

        try:

            with st.spinner(
                "Lecture et structuration de la proposition..."
            ):
                proposal_text = extract_pdf_text(
                    temporary_path
                )

                normalized_document = normalize_document(
                    proposal_text
                )

            with st.spinner(
                "Vérification des règles qualité..."
            ):
                results = review_v2(
                    normalized_document
                )

            st.session_state["review_results"] = results
            st.session_state[
                "normalized_document"
            ] = normalized_document

            st.session_state[
                "reviewed_filename"
            ] = uploaded_file.name

        except Exception:
            st.error(
                "L'analyse n'a pas pu être terminée."
            )

            # À retirer / masquer avant pilote large.
            st.exception(
                st.session_state.get(
                    "_last_exception",
                    Exception(
                        "Consultez les logs pour plus de détails."
                    ),
                )
            )

        finally:
            temporary_path.unlink(
                missing_ok=True
            )


# ============================================================
# RESULTS
# ============================================================

results = st.session_state.get(
    "review_results"
)

if results:

    st.divider()

    reviewed_filename = st.session_state.get(
        "reviewed_filename"
    )

    # ========================================================
    # COUNTS
    # ========================================================

    non_compliant = sum(
        result.get("status") == "NON_COMPLIANT"
        for result in results
    )

    not_evaluated = sum(
        result.get("status") == "NOT_EVALUATED"
        for result in results
    )

    suggested = sum(
        result.get("status") == "SUGGESTED"
        for result in results
    )

    # ========================================================
    # HEADER
    # ========================================================

    st.header("Résultat de l'analyse")

    if reviewed_filename:
        st.caption(reviewed_filename)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "À corriger",
        non_compliant,
    )

    col2.metric(
        "À vérifier",
        not_evaluated,
    )

    col3.metric(
        "Suggestions",
        suggested,
    )

    # ========================================================
    # ITEMS TO HANDLE
    # ========================================================

    st.divider()

    st.subheader("Points à traiter")

    actionable_results = [
        result
        for result in results
        if result.get("status")
        in {
            "NON_COMPLIANT",
            "NOT_EVALUATED",
        }
    ]

    # ========================================================
    # MINIMAL CONTROLS
    # ========================================================

    control_col1, control_col2 = st.columns(
        [3, 1],
        vertical_alignment="bottom"
    )

    with control_col1:
        sort_mode = st.selectbox(
            "Trier par",
            options=[
                "Priorité",
                "Ordre du document",
            ],
        )

    with control_col2:
        with st.popover(
            "Filtrer",
            use_container_width=True,
        ):

            available_sections = sorted({
                get_metadata(result).get("section")
                for result in actionable_results
                if get_metadata(result).get("section")
            })

            selected_sections = st.multiselect(
                "Section",
                available_sections,
                placeholder="Toutes",
            )

            dimension = st.radio(
                "Dimension",
                options=[
                    "Toutes",
                    "Fond",
                    "Forme",
                ],
                horizontal=True,
            )

    # ========================================================
    # FILTER
    # ========================================================

    filtered_results = []

    for result in actionable_results:

        metadata = get_metadata(result)

        if (
            selected_sections
            and metadata.get("section")
            not in selected_sections
        ):
            continue

        if (
            dimension != "Toutes"
            and metadata.get("dimension", "").upper()
            != dimension.upper()
        ):
            continue

        filtered_results.append(result)

    # ========================================================
    # SORT
    # ========================================================

    if sort_mode == "Priorité":
        filtered_results = sort_by_priority(
            filtered_results
        )

    # "Ordre du document" intentionally keeps
    # the original reviewer/rule order.

    # ========================================================
    # DISPLAY ACTIONABLE RESULTS
    # ========================================================

    if not actionable_results:

        st.success(
            "Aucun point à corriger ou à vérifier."
        )

    elif not filtered_results:

        st.info(
            "Aucun point ne correspond aux filtres sélectionnés."
        )

    else:

        for index, result in enumerate(
            filtered_results
        ):
            render_result(
                result,
                expanded=(index == 0),
            )

    # ========================================================
    # SUGGESTIONS
    # ========================================================

    suggestions = [
        result
        for result in results
        if result.get("status") == "SUGGESTED"
    ]

    if suggestions:

        st.divider()

        st.subheader(
            f"💡 Suggestion"
            f"{'s' if len(suggestions) > 1 else ''}"
        )

        st.caption(
            "Améliorations facultatives identifiées "
            "dans la proposition."
        )

        for result in suggestions:
            render_result(result)

    # ========================================================
    # FULL AUDIT
    # ========================================================

    st.divider()

    with st.expander(
        f"Voir les {len(results)} contrôles"
    ):

        st.caption(
            "Vue exhaustive de l'ensemble des règles évaluées."
        )

        for result in results:
            render_result(result)