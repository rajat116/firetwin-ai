"""Pilot fire definitions used by Phase 4 real-data workflows."""

from dataclasses import dataclass
from datetime import date

from firetwin.data.progression_audit import PilotFireSpec


@dataclass(frozen=True)
class PilotLabelSpec:
    """Pilot fire configuration for label artifact generation."""

    case_id: str
    fire: PilotFireSpec


PILOT_LABEL_SPECS = [
    PilotLabelSpec(
        case_id="carlton_complex_2014",
        fire=PilotFireSpec(
            name="Carlton Complex",
            year=2014,
            bbox=(-120.5, 47.5, -119.5, 48.5),
            start_date=date(2014, 7, 14),
            end_date=date(2014, 8, 25),
        ),
    ),
    PilotLabelSpec(
        case_id="king_2014",
        fire=PilotFireSpec(
            name="KING",
            year=2014,
            bbox=(-121.5, 38.5, -120.0, 39.5),
            start_date=date(2014, 9, 13),
            end_date=date(2014, 10, 9),
        ),
    ),
    PilotLabelSpec(
        case_id="big_cougar_2014",
        fire=PilotFireSpec(
            name="Big Cougar",
            year=2014,
            bbox=(-117.5, 45.4, -116.2, 46.6),
            start_date=date(2014, 8, 2),
            end_date=date(2014, 9, 15),
        ),
    ),
]
