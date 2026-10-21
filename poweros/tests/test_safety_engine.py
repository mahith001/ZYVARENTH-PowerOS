from poweros.intelligence.safety_engine import (
    calculate_safe_power_limit,
    calculate_uncertainty_buffer,
    classify_power_risk,
    classify_workload_risk,
    analyze_safety,
)


def main():

    # --------------------------------------------------------
    # SAFE POWER
    # --------------------------------------------------------

    safe_limit = calculate_safe_power_limit(
        available_power_kw=100,
        reserve_percent=15,
    )

    assert safe_limit == 85

    # --------------------------------------------------------
    # UNCERTAINTY
    # --------------------------------------------------------

    buffer = calculate_uncertainty_buffer(
        forecast_power_kw=80,
        uncertainty_percent=10,
    )

    assert buffer == 8

    # --------------------------------------------------------
    # POWER RISK
    # --------------------------------------------------------

    risk = classify_power_risk(
        forecast_power_kw=90,
        safe_power_limit_kw=100,
    )

    assert risk == "HIGH"

    # --------------------------------------------------------
    # WORKLOAD RISK
    # --------------------------------------------------------

    workload_risk = classify_workload_risk(
        priority="HIGH",
        deadline_hour=4,
        current_hour=0,
    )

    assert workload_risk == "HIGH"

    # --------------------------------------------------------
    # FULL SAFETY ANALYSIS
    # --------------------------------------------------------

    safety = analyze_safety(
        available_power_kw=100,
        forecast_peak_power_kw=75,
        uncertainty_percent=10,
        reserve_percent=15,
    )

    assert (
        safety["safe_power_limit_kw"]
        == 85
    )

    assert (
        safety["uncertainty_buffer_kw"]
        == 7.5
    )

    assert (
        safety["protected_forecast_kw"]
        == 82.5
    )

    assert (
        safety["risk"]
        == "HIGH"
    )

    print(
        "POWEROS SAFETY ENGINE TEST PASSED"
    )


if __name__ == "__main__":

    main()