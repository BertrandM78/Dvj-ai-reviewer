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
    page_title="DVJ AI Proposal Reviewer",
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

    st.title("DVJ AI Proposal Reviewer")

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


def render_result(result: dict) -> None:
    rule_id = result.get("rule_id", "UNKNOWN")
    status = result.get("status", "UNKNOWN")

    metadata = get_metadata(result)
    status_config = get_status_config(status)

    title = metadata.get("title", rule_id)
    rule_type = metadata.get("type", "—")
    section = metadata.get("section", "—")
    dimension = metadata.get("dimension", "—")
    severity = metadata.get("severity", "—")

    reason = (
        result.get("reason")
        or result.get("reasoning")
        or "Aucune explication disponible."
    )

    evidence = result.get("evidence")
    recommendation = result.get("recommendation")

    expander_title = (
        f"{status_config['icon']} "
        f"{title} · {status_config['label']}"
    )

    expanded = status in {
        "NON_COMPLIANT",
        "NOT_EVALUATED",
        "SUGGESTED",
    }

    with st.expander(
        expander_title,
        expanded=expanded,
    ):
        st.caption(
            f"{rule_id} · "
            f"{rule_type} · "
            f"{section} · "
            f"{dimension} · "
            f"{severity}"
        )

        st.markdown("**Pourquoi ce point est signalé**")
        st.write(reason)

        if evidence:
            st.markdown("**Élément détecté**")

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

        if recommendation:
            st.markdown("**Action recommandée**")
            st.info(recommendation)


def apply_view(
    results: list[dict],
    view: str,
) -> list[dict]:

    if view == "À corriger":
        return [
            result
            for result in results
            if result.get("status")
            in {
                "NON_COMPLIANT",
                "NOT_EVALUATED",
            }
        ]

    if view == "Recommandations":
        return [
            result
            for result in results
            if result.get("status") == "SUGGESTED"
        ]

    return results


# ============================================================
# HEADER
# ============================================================

st.title("DVJ AI Proposal Reviewer")

st.caption(
    "Vérifiez votre proposition commerciale avant validation."
)

st.write(
    "Le reviewer contrôle automatiquement les obligations qualité "
    "et identifie les recommandations pertinentes."
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

    st.header("Résultat de l'analyse")

    reviewed_filename = st.session_state.get(
        "reviewed_filename"
    )

    if reviewed_filename:
        st.caption(reviewed_filename)

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

    compliant = sum(
        result.get("status") == "COMPLIANT"
        for result in results
    )

    not_applicable = sum(
        result.get("status") == "NOT_APPLICABLE"
        for result in results
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

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

    col4.metric(
        "Conformes",
        compliant,
    )

    if non_compliant:
        st.warning(
            f"{non_compliant} point"
            f"{'s' if non_compliant > 1 else ''} "
            "à corriger avant validation."
        )
    else:
        st.success(
            "Aucune non-conformité détectée."
        )

    st.caption(
        f"{not_applicable} contrôle"
        f"{'s' if not_applicable != 1 else ''} "
        "non applicable"
    )

    # ========================================================
    # VIEW
    # ========================================================

    st.subheader("Relecture")

    view = st.radio(
        "Vue",
        options=[
            "À corriger",
            "Recommandations",
            "Tout",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    visible_results = apply_view(
        results,
        view,
    )

    # ========================================================
    # FILTERS
    # ========================================================

    filter_col1, filter_col2, filter_col3 = (
        st.columns(3)
    )

    available_sections = sorted({
        get_metadata(result).get("section")
        for result in visible_results
        if get_metadata(result).get("section")
    })

    available_severities = sorted({
        get_metadata(result).get("severity")
        for result in visible_results
        if get_metadata(result).get("severity")
    })

    available_dimensions = sorted({
        get_metadata(result).get("dimension")
        for result in visible_results
        if get_metadata(result).get("dimension")
    })

    selected_sections = filter_col1.multiselect(
        "Section",
        available_sections,
    )

    selected_severities = filter_col2.multiselect(
        "Sévérité",
        available_severities,
    )

    selected_dimensions = filter_col3.multiselect(
        "Dimension",
        available_dimensions,
    )

    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_results = []

    for result in visible_results:

        metadata = get_metadata(result)

        if (
            selected_sections
            and metadata.get("section")
            not in selected_sections
        ):
            continue

        if (
            selected_severities
            and metadata.get("severity")
            not in selected_severities
        ):
            continue

        if (
            selected_dimensions
            and metadata.get("dimension")
            not in selected_dimensions
        ):
            continue

        filtered_results.append(result)

    # ========================================================
    # DISPLAY
    # ========================================================

    st.caption(
        f"{len(filtered_results)} résultat"
        f"{'s' if len(filtered_results) != 1 else ''}"
    )

    if not filtered_results:

        if view == "Recommandations":
            st.success(
                "Aucune recommandation particulière "
                "n'est suggérée."
            )

        else:
            st.info(
                "Aucun résultat ne correspond "
                "aux filtres sélectionnés."
            )

    else:

        for result in filtered_results:
            render_result(result)