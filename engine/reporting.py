import pandas as pd
import matplotlib.pyplot as plt


def create_comparison_report(
    baseline_metrics: dict,
    optimized_metrics: dict,
    output_file: str = "results/performance_report.csv"
):
    """
    Create a CSV comparison between the baseline
    and ZYVARENTH PowerOS.
    """

    report = pd.DataFrame({
        "Metric": [
            "Electricity Cost (₹)",
            "Peak Power (kW)",
            "GPU Utilization (%)",
            "Completed Jobs",
            "Missed Deadlines",
            "Power Limit Violations"
        ],

        "Baseline": [
            baseline_metrics["total_cost"],
            baseline_metrics["peak_power_kw"],
            baseline_metrics["gpu_utilization_percent"],
            baseline_metrics["completed_jobs"],
            baseline_metrics["missed_deadlines"],
            baseline_metrics["power_limit_violations"]
        ],

        "ZYVARENTH": [
            optimized_metrics["total_cost"],
            optimized_metrics["peak_power_kw"],
            optimized_metrics["gpu_utilization_percent"],
            optimized_metrics["completed_jobs"],
            optimized_metrics["missed_deadlines"],
            optimized_metrics["power_limit_violations"]
        ]
    })

    report.to_csv(output_file, index=False)

    print(f"\nPerformance report saved to: {output_file}")

    return report


def create_cost_chart(
    baseline_cost: float,
    optimized_cost: float,
    output_file: str = "results/cost_comparison.png"
):
    """
    Create a simple baseline vs ZYVARENTH
    electricity-cost comparison chart.
    """

    labels = ["Baseline", "ZYVARENTH"]
    values = [baseline_cost, optimized_cost]

    plt.figure(figsize=(8, 5))

    plt.bar(labels, values)

    plt.title("Electricity Cost Comparison")
    plt.ylabel("Electricity Cost (₹)")

    plt.tight_layout()

    plt.savefig(output_file)

    plt.close()

    print(f"Cost chart saved to: {output_file}")