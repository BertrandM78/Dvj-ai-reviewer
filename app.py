import tempfile
from pathlib import Path

import streamlit as st

from src.reviewer import review_file


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DVJ AI Proposal Reviewer",
    page_icon="📄",
    layout="wide",
)

st.title("DVJ AI Proposal Reviewer")

st.write(
    "Analysez une proposition commerciale selon les "
    "règles qualité de DeVinci Junior."
)


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Déposez une proposition commerciale",
    type=["pdf", "txt"],
)


# ============================================================
# ANALYSIS
# ============================================================

if uploaded_file is not None:

    st.write(f"**Fichier :** {uploaded_file.name}")

    if st.button(
        "Analyser la proposition",
        type="primary",
    ):

        suffix = Path(uploaded_file.name).suffix

        # Streamlit keeps the uploaded file in memory.
        # review_file() expects a file path, so we temporarily
        # save the uploaded document.
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

            with st.spinner(
                "Analyse de la proposition en cours..."
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
            # METRICS
            # ====================================================

            compliant = sum(
                result.get("status") == "COMPLIANT"
                for result in results
            )

            non_compliant = sum(
                result.get("status") == "NON_COMPLIANT"
                for result in results
            )

            not_applicable = sum(
                result.get("status") == "NOT_APPLICABLE"
                for result in results
            )

            st.success("Analyse terminée.")

            st.header("Synthèse")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Conformes",
                compliant,
            )

            col2.metric(
                "Anomalies",
                non_compliant,
            )

            col3.metric(
                "Non applicables",
                not_applicable,
            )


            # ====================================================
            # COMMERCIAL CONTEXT
            # ====================================================

            st.header("Contexte commercial")

            context_col1, context_col2 = st.columns(2)

            context_col1.write(
                "**Secteur**"
            )

            context_col1.write(
                commercial_context.get("sector")
                or "Non identifié"
            )

            context_col2.write(
                "**Type de mission**"
            )

            context_col2.write(
                commercial_context.get("mission_type")
                or "Non identifié"
            )


            # ====================================================
            # NON-COMPLIANT RULES
            # ====================================================

            st.header("Points à corriger")

            violations = [
                result
                for result in results
                if result.get("status")
                == "NON_COMPLIANT"
            ]

            if not violations:

                st.success(
                    "Aucune non-conformité détectée."
                )

            else:

                for violation in violations:

                    rule_id = violation.get(
                        "rule_id",
                        "Règle",
                    )

                    with st.expander(
                        rule_id,
                        expanded=True,
                    ):

                        reasoning = (
                            violation.get("reason")
                            or violation.get("reasoning")
                            or "Aucune explication disponible."
                        )

                        st.write(reasoning)

                        evidence = violation.get(
                            "evidence"
                        )

                        if evidence:

                            st.write(
                                "**Élément identifié :**"
                            )

                            st.write(evidence)

                        recommendation = violation.get(
                            "recommendation"
                        )

                        if recommendation:

                            st.write(
                                "**Recommandation :**"
                            )

                            st.write(
                                recommendation
                            )


            # ====================================================
            # HISTORICAL REFERENCES
            # ====================================================

            st.header("Références historiques")

            if historical_summary:

                st.info(
                    historical_summary
                )

            else:

                st.write(
                    "Aucune référence historique "
                    "pertinente n'a pu être générée."
                )


            # ====================================================
            # ALL RULES
            # ====================================================

            with st.expander(
                "Voir le détail des 31 règles"
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

                    st.write(
                        f"**{rule_id} — {status}**"
                    )

                    reasoning = (
                        rule_result.get("reason")
                        or rule_result.get("reasoning")
                    )

                    if reasoning:
                        st.write(reasoning)

                    st.divider()


        except Exception as error:

            st.error(
                "Une erreur est survenue pendant "
                "l'analyse."
            )

            # Useful for local V0 debugging.
            st.exception(error)


        finally:

            temporary_path.unlink(
                missing_ok=True
            )