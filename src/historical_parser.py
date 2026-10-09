from typing import Any


def _split_tabular_chunk(
    text: str,
) -> tuple[list[str], list[str]]:
    """
    Bedrock returns CSV rows as:
    header line
    data line
    """

    lines = [
        line
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) < 2:
        return [], []

    headers = lines[0].split("\t")
    values = lines[1].split("\t")

    # Pad short rows safely.
    if len(values) < len(headers):
        values += [""] * (
            len(headers) - len(values)
        )

    return headers, values


def _get_value(
    headers: list[str],
    values: list[str],
    column: str,
    occurrence: int = 0,
) -> str | None:
    """
    Get one column while supporting duplicate column names.
    """

    matches = [
        index
        for index, header in enumerate(headers)
        if header.strip() == column
    ]

    if occurrence >= len(matches):
        return None

    index = matches[occurrence]

    if index >= len(values):
        return None

    value = values[index].strip()

    if not value:
        return None

    return value


def _clean_list(
    values: list[str | None],
) -> list[str]:
    return [
        value
        for value in values
        if value
    ]


def parse_commercial_proposal(
    text: str,
) -> dict[str, Any] | None:
    headers, values = _split_tabular_chunk(
        text
    )

    if not headers:
        return None

    prestations = _clean_list(
        [
            _get_value(
                headers,
                values,
                f"Prestation {index}",
            )
            for index in range(1, 6)
        ]
    )

    return {
        "record_id": _get_value(
            headers,
            values,
            "ID lead",
        ),
        "title": _get_value(
            headers,
            values,
            "Titre",
        ),
        "company": _get_value(
            headers,
            values,
            "Entreprise",
        ),
        "client_type": _get_value(
            headers,
            values,
            "Type",
        ),
        "status": _get_value(
            headers,
            values,
            "Statut lead",
        ),
        "closure_reason": _get_value(
            headers,
            values,
            "Raison clôture",
        ),
        "source": _get_value(
            headers,
            values,
            "Provenance",
        ),
        "budget": _get_value(
            headers,
            values,
            "Budget",
        ),
        "services": prestations,
        "forecast_revenue_ht": _get_value(
            headers,
            values,
            "CA prévisionnel HT",
        ),
        "signed_revenue_ht": _get_value(
            headers,
            values,
            "CA signé HT",
        ),
        "mandate": _get_value(
            headers,
            values,
            "Mandat 25/26",
        ),
    }


def parse_signed_mission(
    text: str,
) -> dict[str, Any] | None:
    headers, values = _split_tabular_chunk(
        text
    )

    if not headers:
        return None

    services = _clean_list(
        [
            _get_value(
                headers,
                values,
                "Prestation 1",
            ),
            _get_value(
                headers,
                values,
                "Prestation 2",
            ),
        ]
    )

    return {
        "record_id": _get_value(
            headers,
            values,
            "Numéro de l'étude",
        ),
        "title": _get_value(
            headers,
            values,
            "Nom de l'étude",
        ),
        "company": _get_value(
            headers,
            values,
            "Client",
        ),
        "client_type": _get_value(
            headers,
            values,
            "Typologie Client",
        ),
        "status": _get_value(
            headers,
            values,
            "Statut",
        ),
        "source": _get_value(
            headers,
            values,
            "Provenance",
        ),
        "services": services,
        "amount_ht": _get_value(
            headers,
            values,
            "Prix HT. de l'étude (avec frais)",
            occurrence=0,
        ),
        "jeh_count": _get_value(
            headers,
            values,
            "Nb JEH",
            occurrence=0,
        ),
        "consultant_count": _get_value(
            headers,
            values,
            "Nb INT",
            occurrence=0,
        ),
        "duration_weeks": _get_value(
            headers,
            values,
            "Durée d'étude (semaines)",
            occurrence=0,
        ),
        "year": _get_value(
            headers,
            values,
            "Année de signature",
        ),
        "mandate": _get_value(
            headers,
            values,
            "Mandat",
        ),
        "reference_service": _get_value(
            headers,
            values,
            "Prestation de référence",
        ),
        "communication_authorized": _get_value(
            headers,
            values,
            "Autorisation com",
        ),
    }


def parse_historical_record(
    text: str,
    corpus_type: str,
) -> dict[str, Any] | None:
    if corpus_type == "COMMERCIAL_PROPOSAL":
        return parse_commercial_proposal(
            text
        )

    if corpus_type == "SIGNED_MISSION":
        return parse_signed_mission(
            text
        )

    raise ValueError(
        f"Unsupported corpus type: {corpus_type}"
    )