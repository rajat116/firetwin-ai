"""Data availability audit and reporting.

This module provides tools to audit data source coverage, quality,
and limitations for fire case selection and model development.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


@dataclass
class DataSourceAudit:
    """Audit results for a single data source."""

    source_name: str
    total_records: int
    date_range: tuple[date, date]
    spatial_extent: tuple[float, float, float, float]  # bbox
    missing_data_pct: float
    quality_issues: list[str]
    coverage_gaps: list[str]
    recommendations: list[str]


class DataAuditor:
    """Data availability auditor for all FireTwin data sources."""

    def __init__(self) -> None:
        """Initialize data auditor."""
        self.audits: dict[str, DataSourceAudit] = {}

    def audit_all_sources(self) -> dict[str, DataSourceAudit]:
        """Run comprehensive audit on all data sources.

        Returns:
            Dictionary mapping source names to audit results
        """
        # This would be implemented with actual data queries
        # For now, provide structure and placeholder

        self.audits = {
            "FIRMS": DataSourceAudit(
                source_name="NASA FIRMS",
                total_records=0,  # Would query actual API
                date_range=(date(2020, 1, 1), date.today()),
                spatial_extent=(-180, -90, 180, 90),
                missing_data_pct=5.0,  # Estimated from cloud/orbit gaps
                quality_issues=[
                    "Cloud cover creates detection gaps",
                    "False positives from industrial sites",
                    "Variable spatial resolution by sensor",
                ],
                coverage_gaps=[
                    "Polar regions: limited coverage",
                    "Tropical regions: frequent cloud cover",
                    "Small fires (<100m²): below detection threshold",
                ],
                recommendations=[
                    "Use confidence >80% for high-quality detections",
                    "Cross-reference with perimeter data",
                    "Account for 1-2 day temporal gaps",
                ],
            ),
            "NIFC": DataSourceAudit(
                source_name="NIFC/WFIGS",
                total_records=0,
                date_range=(date(2000, 1, 1), date.today()),
                spatial_extent=(-180, 18, -65, 72),  # US extent
                missing_data_pct=15.0,
                quality_issues=[
                    "Update frequency varies by incident",
                    "Hand-digitized: variable precision",
                    "Small fires may not be mapped",
                ],
                coverage_gaps=[
                    "US only (federal and state lands)",
                    "Fires <300 acres may be incomplete",
                    "Historical data: final perimeters only",
                ],
                recommendations=[
                    "Use for large, high-profile fires",
                    "Check perimeter timestamp carefully",
                    "Supplement with FIRMS for progression",
                ],
            ),
            "MTBS": DataSourceAudit(
                source_name="MTBS",
                total_records=0,
                date_range=(date(1984, 1, 1), date(2024, 12, 31)),
                spatial_extent=(-180, 18, -65, 72),
                missing_data_pct=10.0,
                quality_issues=[
                    "1-2 year lag in data availability",
                    "Landsat cloud cover affects accuracy",
                    "Minimum fire size thresholds",
                ],
                coverage_gaps=[
                    "US only",
                    "West: >1000 acres; East: >500 acres",
                    "Final perimeters only (no progression)",
                ],
                recommendations=[
                    "Use for historical analysis only",
                    "Excellent for burn severity mapping",
                    "Combine with FIRMS/NIFC for near-real-time",
                ],
            ),
            "ERA5": DataSourceAudit(
                source_name="ERA5-Land",
                total_records=0,
                date_range=(date(1950, 1, 1), date.today()),
                spatial_extent=(-180, -90, 180, 90),
                missing_data_pct=0.1,  # Very complete
                quality_issues=[
                    "9km resolution: coarse for local effects",
                    "Reanalysis: model + obs blend",
                    "Complex terrain: higher uncertainty",
                ],
                coverage_gaps=[
                    "5-day lag for near-real-time",
                    "No sub-grid-scale wind variability",
                    "Limited vertical profile data",
                ],
                recommendations=[
                    "Use for synoptic-scale weather forcing",
                    "Downscale for local terrain effects",
                    "Validate against local weather stations",
                ],
            ),
            "LANDFIRE": DataSourceAudit(
                source_name="LANDFIRE",
                total_records=0,
                date_range=(date(2001, 1, 1), date(2022, 12, 31)),
                spatial_extent=(-180, 18, -65, 72),
                missing_data_pct=5.0,
                quality_issues=[
                    "Temporal lag: 2-3 year update cycle",
                    "Static snapshots: no daily moisture",
                    "Derived from satellite: not ground truth",
                ],
                coverage_gaps=[
                    "US only",
                    "Version changes: discontinuities",
                    "No dynamic vegetation moisture",
                ],
                recommendations=[
                    "Use most recent version available",
                    "Document version in metadata",
                    "Adjust for fuel moisture separately",
                ],
            ),
            "USGS_3DEP": DataSourceAudit(
                source_name="USGS 3DEP",
                total_records=0,
                date_range=(date(2000, 1, 1), date.today()),
                spatial_extent=(-180, 18, -165, 72),
                missing_data_pct=2.0,
                quality_issues=[
                    "Variable resolution by region",
                    "5-10 year update cycles",
                    "Seam lines in some areas",
                ],
                coverage_gaps=[
                    "US and territories only",
                    "1m lidar: limited coverage",
                    "Steep terrain: data voids",
                ],
                recommendations=[
                    "Use 10m or 30m for consistent coverage",
                    "Check vertical accuracy metadata",
                    "Fill voids with interpolation if needed",
                ],
            ),
        }

        return self.audits

    def generate_report(self, output_path: Path) -> None:
        """Generate comprehensive audit report.

        Args:
            output_path: Path to output markdown report
        """
        if not self.audits:
            self.audit_all_sources()

        report_lines = [
            "# FireTwin Data Availability Audit Report",
            "",
            f"**Generated**: {date.today().isoformat()}",
            "",
            "## Executive Summary",
            "",
            f"This report audits {len(self.audits)} data sources used in FireTwin.",
            "",
            "### Overall Coverage",
            "",
        ]

        # Summary table
        report_lines.append(
            "| Data Source | Records | Date Range | Missing Data % | Quality Issues |"
        )
        report_lines.append(
            "|------------|---------|------------|----------------|----------------|"
        )

        for audit in self.audits.values():
            start, end = audit.date_range
            report_lines.append(
                f"| {audit.source_name} | {audit.total_records:,} | "
                f"{start.year}-{end.year} | {audit.missing_data_pct:.1f}% | "
                f"{len(audit.quality_issues)} |"
            )

        report_lines.extend(
            [
                "",
                "## Detailed Source Audits",
                "",
            ]
        )

        # Detailed sections for each source
        for audit in self.audits.values():
            report_lines.extend(
                [
                    f"### {audit.source_name}",
                    "",
                    f"**Total Records**: {audit.total_records:,}",
                    f"**Date Range**: {audit.date_range[0].isoformat()} to {audit.date_range[1].isoformat()}",
                    f"**Missing Data**: {audit.missing_data_pct:.1f}%",
                    "",
                    "**Quality Issues**:",
                    "",
                ]
            )

            for issue in audit.quality_issues:
                report_lines.append(f"- {issue}")

            report_lines.extend(
                [
                    "",
                    "**Coverage Gaps**:",
                    "",
                ]
            )

            for gap in audit.coverage_gaps:
                report_lines.append(f"- {gap}")

            report_lines.extend(
                [
                    "",
                    "**Recommendations**:",
                    "",
                ]
            )

            for rec in audit.recommendations:
                report_lines.append(f"- {rec}")

            report_lines.extend(
                [
                    "",
                    "---",
                    "",
                ]
            )

        # Cross-source analysis
        report_lines.extend(
            [
                "## Cross-Source Analysis",
                "",
                "### Data Source Complementarity",
                "",
                "**Optimal Fire Case Requirements**:",
                "",
                "1. **Active Fire Detection**: FIRMS detections (confidence >80%)",
                "2. **Fire Perimeter**: NIFC perimeters (multiple timestamps) OR MTBS final perimeter",
                "3. **Weather**: ERA5-Land hourly data (full fire duration)",
                "4. **Fuels**: LANDFIRE (version matched to fire year)",
                "5. **Terrain**: USGS 3DEP (10m or 30m resolution)",
                "",
                "### Data Quality Tiers",
                "",
                "**Tier 1 (Highest Quality)**:",
                "- All 6 data sources available",
                "- NIFC: 5+ perimeter updates",
                "- FIRMS: 50+ high-confidence detections",
                "- Fire duration: 7+ days",
                "",
                "**Tier 2 (Good Quality)**:",
                "- 4-5 data sources available",
                "- At least one perimeter source (NIFC or MTBS)",
                "- FIRMS: 20+ detections",
                "- Fire duration: 3+ days",
                "",
                "**Tier 3 (Acceptable Quality)**:",
                "- 3-4 data sources available",
                "- At least FIRMS + one other source",
                "- Fire duration: 1+ days",
                "",
                "### Known Limitations",
                "",
                "1. **Temporal Mismatch**: ERA5 (hourly) vs NIFC (daily) vs MTBS (final)",
                "2. **Spatial Resolution**: ERA5 (9km) vs LANDFIRE/3DEP (30m) vs FIRMS (375m-1km)",
                "3. **Geographic Coverage**: All sources US-only except FIRMS and ERA5",
                "4. **Temporal Lag**: LANDFIRE (2-3 years), MTBS (1-2 years)",
                "",
                "### Recommendations for Model Development",
                "",
                "1. **Focus on Tier 1 & 2 fires** for initial model training",
                "2. **Use synthetic data** to augment real fire cases",
                "3. **Validate predictions** against MTBS burn severity",
                "4. **Account for uncertainty** in fire spread model",
                "5. **Document data provenance** for all fire cases",
                "",
                "## Next Steps",
                "",
                "1. Build fire case inventory from data sources",
                "2. Implement quality filtering and ranking",
                "3. Select initial dataset for model development",
                "4. Create validation splits (spatial + temporal)",
                "5. Document any data preprocessing decisions",
                "",
            ]
        )

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(report_lines))

    def to_dataframe(self) -> pd.DataFrame:
        """Convert audit results to DataFrame.

        Returns:
            DataFrame with audit summary
        """
        data = []
        for audit in self.audits.values():
            data.append(
                {
                    "source_name": audit.source_name,
                    "total_records": audit.total_records,
                    "start_date": audit.date_range[0],
                    "end_date": audit.date_range[1],
                    "missing_data_pct": audit.missing_data_pct,
                    "num_quality_issues": len(audit.quality_issues),
                    "num_coverage_gaps": len(audit.coverage_gaps),
                    "num_recommendations": len(audit.recommendations),
                }
            )

        return pd.DataFrame(data)
