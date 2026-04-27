"""
Unit Tests — CCTS Compliance Calculator
========================================
Run with: python -m pytest test_calculator.py -v
"""

import pytest
from calculator import (
    calculate_ccts_compliance,
    calculate_whatif_reduction,
    list_sectors,
    SECTOR_DATA,
    ComplianceStatus,
    PRICE_FLOOR_INR,
    PRICE_EXPECTED_INR,
    PRICE_CEILING_INR,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cement_target():
    s = SECTOR_DATA["cement"]
    return s["baseline_intensity"] * (1 - s["reduction_target_pct"])


@pytest.fixture
def steel_target():
    s = SECTOR_DATA["iron_steel"]
    return s["baseline_intensity"] * (1 - s["reduction_target_pct"])


# ---------------------------------------------------------------------------
# Input Validation
# ---------------------------------------------------------------------------

class TestInputValidation:

    def test_invalid_sector_raises(self):
        with pytest.raises(ValueError, match="not found"):
            calculate_ccts_compliance("rubber", 100_000)

    def test_zero_production_raises(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_ccts_compliance("cement", 0)

    def test_negative_production_raises(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_ccts_compliance("cement", -500_000)

    def test_negative_intensity_raises(self):
        with pytest.raises(ValueError, match="negative"):
            calculate_ccts_compliance("cement", 1_000_000, actual_intensity=-0.1)

    def test_all_valid_sectors_accepted(self):
        for key in SECTOR_DATA:
            result = calculate_ccts_compliance(key, 100_000)
            assert result.sector_key == key


# ---------------------------------------------------------------------------
# Sector Average Fallback
# ---------------------------------------------------------------------------

class TestIntensityFallback:

    def test_no_intensity_uses_sector_average(self):
        s = SECTOR_DATA["cement"]
        result = calculate_ccts_compliance("cement", 1_000_000)
        assert result.actual_intensity == pytest.approx(s["baseline_intensity"], rel=1e-4)
        assert result.intensity_was_estimated is True

    def test_provided_intensity_used(self):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.65)
        assert result.actual_intensity == pytest.approx(0.65, rel=1e-4)
        assert result.intensity_was_estimated is False

    def test_co2e_from_energy_derives_intensity(self):
        production = 500_000
        total_co2e = 325_000   # => intensity = 0.65
        result = calculate_ccts_compliance(
            "cement", production, co2e_from_energy=total_co2e
        )
        assert result.actual_intensity == pytest.approx(0.65, rel=1e-4)
        assert result.intensity_was_estimated is False


# ---------------------------------------------------------------------------
# Compliance Status
# ---------------------------------------------------------------------------

class TestComplianceStatus:

    def test_under_complier_above_target(self, cement_target):
        intensity = cement_target * 1.10   # 10% above target
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=intensity)
        assert result.compliance_status == ComplianceStatus.UNDER_COMPLIER

    def test_over_complier_below_target(self, cement_target):
        intensity = cement_target * 0.88   # 12% below target
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=intensity)
        assert result.compliance_status == ComplianceStatus.OVER_COMPLIER

    def test_at_threshold_within_2pct(self, cement_target):
        intensity = cement_target * 1.01   # 1% above target — within 2% band
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=intensity)
        assert result.compliance_status == ComplianceStatus.AT_THRESHOLD

    def test_at_threshold_below_within_2pct(self, cement_target):
        intensity = cement_target * 0.99   # 1% below target — within 2% band
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=intensity)
        assert result.compliance_status == ComplianceStatus.AT_THRESHOLD


# ---------------------------------------------------------------------------
# CCC Delta Calculation
# ---------------------------------------------------------------------------

class TestCCCDelta:

    def test_deficit_is_positive(self, cement_target):
        intensity = cement_target * 1.10
        production = 1_000_000
        result = calculate_ccts_compliance("cement", production, actual_intensity=intensity)
        assert result.ccc_delta_tonnes > 0

    def test_surplus_is_negative(self, cement_target):
        intensity = cement_target * 0.88
        production = 1_000_000
        result = calculate_ccts_compliance("cement", production, actual_intensity=intensity)
        assert result.ccc_delta_tonnes < 0

    def test_delta_magnitude_correct(self, cement_target):
        intensity = cement_target + 0.05   # 0.05 tCO2e/tonne above target
        production = 2_000_000
        result = calculate_ccts_compliance("cement", production, actual_intensity=intensity)
        expected_delta = 0.05 * 2_000_000
        assert result.ccc_delta_tonnes == pytest.approx(expected_delta, rel=1e-3)

    def test_zero_gap_near_zero_delta(self, cement_target):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=cement_target)
        assert abs(result.ccc_delta_tonnes) < 1.0   # effectively zero


# ---------------------------------------------------------------------------
# Price Scenarios
# ---------------------------------------------------------------------------

class TestPriceScenarios:

    def test_three_scenarios_always_returned(self):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        assert len(result.price_scenarios) == 3

    def test_scenario_prices_match_constants(self):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        prices = [s.price_inr for s in result.price_scenarios]
        assert PRICE_FLOOR_INR in prices
        assert PRICE_EXPECTED_INR in prices
        assert PRICE_CEILING_INR in prices

    def test_financial_exposure_proportional_to_delta(self):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        delta = result.ccc_delta_tonnes
        for sc in result.price_scenarios:
            expected_inr = delta * sc.price_inr
            assert sc.total_exposure_inr == pytest.approx(expected_inr, rel=1e-3)

    def test_over_complier_exposure_is_negative(self):
        s = SECTOR_DATA["cement"]
        target = s["baseline_intensity"] * (1 - s["reduction_target_pct"])
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=target * 0.85)
        for sc in result.price_scenarios:
            assert sc.total_exposure_inr < 0   # revenue, not cost

    def test_per_unit_exposure_consistent(self):
        result = calculate_ccts_compliance("cement", 2_000_000, actual_intensity=0.74)
        for sc in result.price_scenarios:
            expected_per_unit = sc.total_exposure_inr / 2_000_000
            assert sc.per_unit_exposure_inr == pytest.approx(expected_per_unit, rel=1e-3)


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------

class TestBenchmarks:

    def test_benchmark_sector_name_matches(self):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        assert result.benchmark.sector_name == "Cement"

    def test_relative_position_in_range(self):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        assert 0.0 <= result.benchmark.relative_position_pct <= 100.0

    def test_worst_performer_near_zero_position(self):
        worst_intensity = SECTOR_DATA["cement"]["baseline_intensity"] * 1.45
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=worst_intensity)
        assert result.benchmark.relative_position_pct <= 5.0

    def test_best_performer_near_100_position(self):
        best_intensity = SECTOR_DATA["cement"]["top_quartile_intensity"] * 0.75
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=best_intensity)
        assert result.benchmark.relative_position_pct >= 95.0

    def test_gap_to_target_positive_for_under_complier(self):
        s = SECTOR_DATA["cement"]
        target = s["baseline_intensity"] * (1 - s["reduction_target_pct"])
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=target * 1.10)
        assert result.benchmark.gap_to_target_pct > 0

    def test_gap_to_target_negative_for_over_complier(self):
        s = SECTOR_DATA["cement"]
        target = s["baseline_intensity"] * (1 - s["reduction_target_pct"])
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=target * 0.88)
        assert result.benchmark.gap_to_target_pct < 0


# ---------------------------------------------------------------------------
# Deloitte Recommendations
# ---------------------------------------------------------------------------

class TestRecommendations:

    def test_mrv_always_first_recommendation(self):
        for key in list(SECTOR_DATA.keys())[:3]:
            result = calculate_ccts_compliance(key, 500_000)
            assert "MRV" in result.recommendations[0].service or \
                   "Monitoring" in result.recommendations[0].service

    def test_under_complier_gets_procurement_rec(self):
        s = SECTOR_DATA["cement"]
        target = s["baseline_intensity"] * (1 - s["reduction_target_pct"])
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=target * 1.10)
        services = [r.service for r in result.recommendations]
        assert any("Procurement" in s or "Trading" in s for s in services)

    def test_over_complier_gets_monetisation_rec(self):
        s = SECTOR_DATA["cement"]
        target = s["baseline_intensity"] * (1 - s["reduction_target_pct"])
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=target * 0.85)
        services = [r.service for r in result.recommendations]
        assert any("Monetisation" in s or "Revenue" in s for s in services)

    def test_estimated_intensity_gets_baseline_rec(self):
        result = calculate_ccts_compliance("cement", 1_000_000)   # no intensity given
        services = [r.service for r in result.recommendations]
        assert any("Baseline" in s or "GHG" in s for s in services)

    def test_unofficial_target_gets_policy_watch_rec(self):
        # iron_steel target not officially notified
        result = calculate_ccts_compliance("iron_steel", 500_000)
        services = [r.service for r in result.recommendations]
        assert any("Policy" in s or "Regulatory" in s for s in services)

    def test_no_duplicate_services(self):
        result = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        services = [r.service for r in result.recommendations]
        assert len(services) == len(set(services))


# ---------------------------------------------------------------------------
# What-If Reduction
# ---------------------------------------------------------------------------

class TestWhatIfReduction:

    def test_invalid_reduction_zero_raises(self):
        base = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        with pytest.raises(ValueError):
            calculate_whatif_reduction(base, 0.0)

    def test_invalid_reduction_one_raises(self):
        base = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        with pytest.raises(ValueError):
            calculate_whatif_reduction(base, 1.0)

    def test_new_intensity_reduced_by_pct(self):
        base = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        w = calculate_whatif_reduction(base, 0.10)
        assert w["new_intensity"] == pytest.approx(0.74 * 0.90, rel=1e-4)

    def test_reduction_improves_ccc_delta(self):
        base = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        w = calculate_whatif_reduction(base, 0.10)
        assert w["new_ccc_delta"] < base.ccc_delta_tonnes

    def test_large_reduction_flips_to_over_complier(self):
        base = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        assert base.compliance_status == ComplianceStatus.UNDER_COMPLIER
        w = calculate_whatif_reduction(base, 0.15)
        assert w["new_status"] in (ComplianceStatus.OVER_COMPLIER, ComplianceStatus.AT_THRESHOLD)

    def test_three_price_scenarios_returned(self):
        base = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        w = calculate_whatif_reduction(base, 0.10)
        assert len(w["price_scenarios"]) == 3

    def test_delta_improvement_is_positive_for_under_complier(self):
        base = calculate_ccts_compliance("cement", 1_000_000, actual_intensity=0.74)
        w = calculate_whatif_reduction(base, 0.10)
        assert w["delta_improvement_tonnes"] > 0


# ---------------------------------------------------------------------------
# list_sectors helper
# ---------------------------------------------------------------------------

class TestListSectors:

    def test_returns_all_sectors(self):
        sectors = list_sectors()
        assert len(sectors) == len(SECTOR_DATA)

    def test_values_are_human_readable_names(self):
        sectors = list_sectors()
        for key, name in sectors.items():
            assert isinstance(name, str)
            assert len(name) > 2


# ---------------------------------------------------------------------------
# Cross-sector smoke test
# ---------------------------------------------------------------------------

class TestAllSectorsSmoke:

    @pytest.mark.parametrize("sector_key", list(SECTOR_DATA.keys()))
    def test_all_sectors_produce_valid_result(self, sector_key):
        result = calculate_ccts_compliance(sector_key, 1_000_000)
        assert result.sector_key == sector_key
        assert result.compliance_status in ComplianceStatus
        assert len(result.price_scenarios) == 3
        assert len(result.recommendations) >= 1
        assert result.methodology_note != ""
        assert result.data_source != ""
