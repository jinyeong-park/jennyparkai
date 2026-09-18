import re
import unittest
from pathlib import Path


DASHBOARD_DIR = Path(__file__).resolve().parents[1]
PY_FILES = [
    DASHBOARD_DIR / "Summary.py",
    *(DASHBOARD_DIR / "pages").glob("*.py"),
    DASHBOARD_DIR / "utils" / "theme.py",
]


class ProfessionalToneTest(unittest.TestCase):
    def test_dashboard_navigation_stays_focused_on_four_screens(self):
        page_files = sorted(p.name for p in (DASHBOARD_DIR / "pages").glob("*.py"))

        self.assertEqual(
            [
                "1_Lead_Funnel.py",
                "2_Campaign_Performance.py",
                "3_Partner_Reconciliation.py",
            ],
            page_files,
        )

        campaign_text = (DASHBOARD_DIR / "pages" / "2_Campaign_Performance.py").read_text(encoding="utf-8")
        partner_text = (DASHBOARD_DIR / "pages" / "3_Partner_Reconciliation.py").read_text(encoding="utf-8")
        self.assertIn("mart_attribution", campaign_text)
        self.assertIn("mart_reconciliation", partner_text)

    def test_python_files_avoid_consumer_style_emoji(self):
        emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
        offenders = []
        for path in PY_FILES:
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if emoji_pattern.search(line):
                    offenders.append(f"{path.relative_to(DASHBOARD_DIR)}:{line_no}: {line.strip()}")

        self.assertEqual([], offenders)

    def test_captions_read_like_business_notes(self):
        banned_fragments = [
            "↳",
            "burning cash",
            "red = above",
            "red = below",
            "red = highest",
            "green =",
            "amber =",
            "Navigate using",
        ]
        offenders = []
        for path in PY_FILES:
            text = path.read_text(encoding="utf-8")
            for fragment in banned_fragments:
                if fragment in text:
                    offenders.append(f"{path.relative_to(DASHBOARD_DIR)} contains {fragment!r}")

        self.assertEqual([], offenders)

    def test_funnel_uses_shared_muted_palette(self):
        summary = (DASHBOARD_DIR / "Summary.py").read_text(encoding="utf-8")
        lead_funnel = (DASHBOARD_DIR / "pages" / "1_Lead_Funnel.py").read_text(encoding="utf-8")

        self.assertIn("FUNNEL_COLORS", summary)
        self.assertIn("FUNNEL_COLORS", lead_funnel)
        self.assertNotIn("stages_colors =", summary)
        self.assertNotIn("stages_c =", lead_funnel)

    def test_routing_outcome_categories_use_distinct_colors(self):
        partner_text = (DASHBOARD_DIR / "pages" / "3_Partner_Reconciliation.py").read_text(encoding="utf-8")

        self.assertIn('name="Capacity Exceeded"', partner_text)
        self.assertIn('name="No Response"', partner_text)
        self.assertIn('marker_color=C_AMBER', partner_text)
        self.assertIn('("Capacity Exceeded",C_AMBER)', partner_text)
        self.assertIn('("No Response",      C_SUBTLE)', partner_text)

    def test_executive_palette_reduces_alarm_colors(self):
        theme = (DASHBOARD_DIR / "utils" / "theme.py").read_text(encoding="utf-8")
        lead_funnel = (DASHBOARD_DIR / "pages" / "1_Lead_Funnel.py").read_text(encoding="utf-8")
        campaign = (DASHBOARD_DIR / "pages" / "2_Campaign_Performance.py").read_text(encoding="utf-8")
        partner = (DASHBOARD_DIR / "pages" / "3_Partner_Reconciliation.py").read_text(encoding="utf-8")

        self.assertIn("[data-baseweb=\"tag\"]", theme)
        self.assertIn("[data-baseweb=\"select\"] > div", theme)
        self.assertIn("[data-baseweb=\"slider\"]", theme)
        self.assertIn("background-color: #EAF1FB", theme)
        self.assertIn("norm_colors = [C_NAVY, C_MUTED, C_MUTED, C_MUTED]", lead_funnel)
        self.assertIn("C_NAVY if r >= 1.0 else C_AMBER", campaign)
        self.assertNotIn("C_GREEN if r >= 1.0", campaign)
        self.assertIn("C_RED if r < 0.70 else C_AMBER if r < 0.80 else C_NAVY", partner)


if __name__ == "__main__":
    unittest.main()
