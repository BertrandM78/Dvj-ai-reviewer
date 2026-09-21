import tempfile
from pathlib import Path

import streamlit as st

from src.reviewer import review_file

import hmac

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DVJ AI Proposal Reviewer",
    page_icon="📄",
    layout="wide",
)

# ============================================================
# AUTHENTICATION
# ============================================================

def check_password() -> bool:
    """
    Display a password field and validate access.
    """

    if st.session_state.get("authenticated"):
        return True

    st.title("DVJ AI Proposal Reviewer")

    password = st.text_input(
        "Mot de passe",
        type="password",
    )

    if st.button("Se connecter", type="primary"):

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
# HEADER
# ============================================================

st.title("DVJ AI Proposal Reviewer")

st.caption(
    "Assistant de relecture des propositions commerciales "
    "de DeVinci Junior"
)

st.write(
    "Déposez une proposition commerciale pour vérifier automatiquement "
    "sa conformité aux 31 règles qualité."
)

st.divider()


# ============================================================
# UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Proposition commerciale",
    type=["pdf", "txt"],
    help="Formats acceptés : PDF et TXT",
)


if uploaded_file is not None:

    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

    st.caption(
        f"{uploaded_file.name} — {file_size_mb:.1f} Mo"
    )

    analyze = st.button(
        "Analyser la proposition",
        type="primary",
        use_container_width=True,
    )

    if analyze:

        suffix = Path(uploaded_file.name).suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temporary_file:

            temporary_file.write(
                uploaded_file.getvalue()
            )

            temporary_path = Path(
                temporary_file.name
            )

        try:

            # ====================================================
            # ANALYSIS
            # ====================================================

            with st.spinner(
                "Analyse des 31 règles qualité en cours..."
            ):
                result = review_file(
                    temporary_path
                )

            review = result["review"]

            commercial_context = result.get(
                "commercial_context",
                {},
            )

            historical_summary = result.get(
                "historical_summary"
            )

            results = review.get(
                "results",
                [],
            )


            # ====================================================
            # COUNTS
            # ====================================================

            compliant = sum(
                r.get("status") == "COMPLIANT"
                for r in results
            )

            violations = [
                r
                for r in results
                if r.get("status") == "NON_COMPLIANT"
            ]

            non_compliant = len(violations)

            not_applicable = sum(
                r.get("status") == "NOT_APPLICABLE"
                for r in results
            )


            # ====================================================
            # RESULT HEADER
            # ====================================================

            st.divider()

            st.header("Résultat de l'analyse")

            if non_compliant == 0:

                st.success(
                    "Aucun point de non-conformité détecté "
                    "sur les 31 contrôles."
                )

            else:

                st.warning(
                    f"{non_compliant} point"
                    f"{'s' if non_compliant > 1 else ''} "
                    f"à corriger sur {len(results)} contrôles."
                )


            # ====================================================
            # METRICS
            # ====================================================

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Conformes",
                compliant,
            )

            col2.metric(
                "À corriger",
                non_compliant,
            )

            col3.metric(
                "Non applicables",
                not_applicable,
            )


            # ====================================================
            # COMMERCIAL CONTEXT
            # ====================================================

            st.subheader("Contexte identifié")

            context_col1, context_col2 = st.columns(2)

            context_col1.metric(
                "Secteur",
                commercial_context.get("sector")
                or "Non identifié",
            )

            context_col2.metric(
                "Type de mission",
                commercial_context.get("mission_type")
                or "Non identifié",
            )


            # ====================================================
            # VIOLATIONS
            # ====================================================

            st.divider()

            st.header("Points à corriger")

            if not violations:

                st.success(
                    "Aucune non-conformité détectée."
                )

            else:

                for index, violation in enumerate(
                    violations,
                    start=1,
                ):

                    rule_id = violation.get(
                        "rule_id",
                        "Règle",
                    )

                    reasoning = (
                        violation.get("reason")
                        or violation.get("reasoning")
                        or "Aucune explication disponible."
                    )

                    evidence = violation.get(
                        "evidence"
                    )

                    recommendation = violation.get(
                        "recommendation"
                    )

                    with st.expander(
                        f"{index}. {rule_id}",
                        expanded=(index <= 3),
                    ):

                        st.markdown(
                            "**Pourquoi ce point est signalé**"
                        )

                        st.write(
                            reasoning
                        )

                        if evidence:

                            st.markdown(
                                "**Élément détecté**"
                            )

                            if isinstance(
                                evidence,
                                (dict, list),
                            ):
                                st.json(
                                    evidence,
                                    expanded=False,
                                )
                            else:
                                st.write(
                                    evidence
                                )

                        if recommendation:

                            st.markdown(
                                "**Action recommandée**"
                            )

                            st.info(
                                recommendation
                            )


            # ====================================================
            # HISTORICAL REFERENCES
            # ====================================================

            st.divider()

            st.header(
                "Références commerciales"
            )

            sector = commercial_context.get(
                "sector"
            )

            mission_type = commercial_context.get(
                "mission_type"
            )

            if sector and mission_type:

                st.caption(
                    f"Recherche effectuée pour : "
                    f"{sector} × {mission_type}"
                )

            if historical_summary:

                st.write(
                    historical_summary
                )

            else:

                st.info(
                    "Aucune référence historique exploitable "
                    "n'a été identifiée."
                )


            # ====================================================
            # ALL RULES
            # ====================================================

            st.divider()

            with st.expander(
                "Voir le détail des 31 contrôles"
            ):

                for rule_result in results:

                    rule_id = rule_result.get(
                        "rule_id",
                        "Règle",
                    )

                    status = rule_result.get(
                        "status",
                        "UNKNOWN",
                    )

                    status_labels = {
                        "COMPLIANT": "Conforme",
                        "NON_COMPLIANT": "À corriger",
                        "NOT_APPLICABLE": "Non applicable",
                    }

                    status_label = status_labels.get(
                        status,
                        status,
                    )

                    st.markdown(
                        f"**{rule_id} — {status_label}**"
                    )

                    reasoning = (
                        rule_result.get("reason")
                        or rule_result.get("reasoning")
                    )

                    if reasoning:
                        st.caption(
                            reasoning
                        )

                    st.divider()


        # ========================================================
        # ERROR HANDLING
        # ========================================================

        except Exception as error:

            st.error(
                "L'analyse n'a pas pu être terminée."
            )

            # Keep during local development.
            st.exception(
                error
            )


        finally:

            temporary_path.unlink(
                missing_ok=True
            )