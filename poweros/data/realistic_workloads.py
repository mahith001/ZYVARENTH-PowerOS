from typing import List, Dict


# =========================================================
# REALISTIC POWEROS WORKLOAD DATASET
# =========================================================

REALISTIC_WORKLOADS: List[Dict] = [

    # -----------------------------------------------------
    # LLM TRAINING
    # -----------------------------------------------------

    {
        "workload_id": "LLM-TRAIN-001",
        "workload_type": "LLM_TRAINING",
        "gpu_required": 8,
        "duration_hours": 6,
        "deadline_hour": 12,
        "priority": "HIGH",
    },

    {
        "workload_id": "LLM-TRAIN-002",
        "workload_type": "LLM_TRAINING",
        "gpu_required": 16,
        "duration_hours": 8,
        "deadline_hour": 18,
        "priority": "HIGH",
    },

    # -----------------------------------------------------
    # LLM FINE-TUNING
    # -----------------------------------------------------

    {
        "workload_id": "LLM-FINETUNE-001",
        "workload_type": "LLM_FINETUNING",
        "gpu_required": 4,
        "duration_hours": 4,
        "deadline_hour": 14,
        "priority": "HIGH",
    },

    {
        "workload_id": "LLM-FINETUNE-002",
        "workload_type": "LLM_FINETUNING",
        "gpu_required": 4,
        "duration_hours": 3,
        "deadline_hour": 20,
        "priority": "MEDIUM",
    },

    # -----------------------------------------------------
    # LLM INFERENCE
    # -----------------------------------------------------

    {
        "workload_id": "LLM-INFER-001",
        "workload_type": "LLM_INFERENCE",
        "gpu_required": 2,
        "duration_hours": 2,
        "deadline_hour": 10,
        "priority": "HIGH",
    },

    {
        "workload_id": "LLM-INFER-002",
        "workload_type": "LLM_INFERENCE",
        "gpu_required": 2,
        "duration_hours": 4,
        "deadline_hour": 22,
        "priority": "MEDIUM",
    },

    # -----------------------------------------------------
    # IMAGE GENERATION
    # -----------------------------------------------------

    {
        "workload_id": "IMG-GEN-001",
        "workload_type": "IMAGE_GENERATION",
        "gpu_required": 4,
        "duration_hours": 3,
        "deadline_hour": 16,
        "priority": "MEDIUM",
    },

    {
        "workload_id": "IMG-GEN-002",
        "workload_type": "IMAGE_GENERATION",
        "gpu_required": 8,
        "duration_hours": 4,
        "deadline_hour": 21,
        "priority": "MEDIUM",
    },

    # -----------------------------------------------------
    # COMPUTER VISION
    # -----------------------------------------------------

    {
        "workload_id": "CV-TRAIN-001",
        "workload_type": "COMPUTER_VISION",
        "gpu_required": 4,
        "duration_hours": 5,
        "deadline_hour": 17,
        "priority": "MEDIUM",
    },

    {
        "workload_id": "CV-TRAIN-002",
        "workload_type": "COMPUTER_VISION",
        "gpu_required": 2,
        "duration_hours": 3,
        "deadline_hour": 23,
        "priority": "LOW",
    },

    # -----------------------------------------------------
    # BATCH PROCESSING
    # -----------------------------------------------------

    {
        "workload_id": "BATCH-001",
        "workload_type": "BATCH_PROCESSING",
        "gpu_required": 4,
        "duration_hours": 4,
        "deadline_hour": 23,
        "priority": "LOW",
    },

    {
        "workload_id": "BATCH-002",
        "workload_type": "BATCH_PROCESSING",
        "gpu_required": 2,
        "duration_hours": 2,
        "deadline_hour": 24,
        "priority": "LOW",
    },

    # -----------------------------------------------------
    # EMBEDDING
    # -----------------------------------------------------

    {
        "workload_id": "EMBED-001",
        "workload_type": "EMBEDDING",
        "gpu_required": 2,
        "duration_hours": 2,
        "deadline_hour": 15,
        "priority": "MEDIUM",
    },

    # -----------------------------------------------------
    # RESEARCH / EXPERIMENTATION
    # -----------------------------------------------------

    {
        "workload_id": "RESEARCH-001",
        "workload_type": "AI_RESEARCH",
        "gpu_required": 8,
        "duration_hours": 5,
        "deadline_hour": 24,
        "priority": "LOW",
    },
]


# =========================================================
# DATASET LOADER
# =========================================================

def get_realistic_workloads() -> List[Dict]:
    """
    Return a copy of the realistic workload dataset.
    """

    return [
        workload.copy()
        for workload in REALISTIC_WORKLOADS
    ]


# =========================================================
# DATASET SUMMARY
# =========================================================

def summarize_realistic_workloads(
    workloads: List[Dict],
) -> Dict:
    """
    Generate summary statistics for the workload dataset.
    """

    total_workloads = len(workloads)

    total_gpu_demand = sum(
        workload["gpu_required"]
        for workload in workloads
    )

    total_compute_hours = sum(
        workload["gpu_required"]
        * workload["duration_hours"]
        for workload in workloads
    )

    high_priority = sum(
        1
        for workload in workloads
        if workload["priority"] == "HIGH"
    )

    medium_priority = sum(
        1
        for workload in workloads
        if workload["priority"] == "MEDIUM"
    )

    low_priority = sum(
        1
        for workload in workloads
        if workload["priority"] == "LOW"
    )

    workload_types = sorted(
        set(
            workload["workload_type"]
            for workload in workloads
        )
    )

    return {
        "total_workloads": total_workloads,
        "total_gpu_demand": total_gpu_demand,
        "total_compute_gpu_hours": total_compute_hours,
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "workload_types": workload_types,
    }


# =========================================================
# PRINT DATASET
# =========================================================

def print_realistic_workloads(
    workloads: List[Dict],
) -> None:
    """
    Print all realistic workloads.
    """

    print()
    print("=" * 80)
    print("POWEROS REALISTIC WORKLOAD DATASET")
    print("=" * 80)

    for workload in workloads:

        print(
            f"{workload['workload_id']:18} | "
            f"{workload['workload_type']:20} | "
            f"GPU: {workload['gpu_required']:2} | "
            f"Duration: {workload['duration_hours']:2}h | "
            f"Deadline: {workload['deadline_hour']:2} | "
            f"Priority: {workload['priority']}"
        )

    print("=" * 80)


# =========================================================
# TEST
# =========================================================

def main():

    workloads = get_realistic_workloads()

    summary = summarize_realistic_workloads(
        workloads
    )

    print_realistic_workloads(
        workloads
    )

    print()
    print("DATASET SUMMARY")
    print("-" * 40)

    print(
        f"Total workloads: "
        f"{summary['total_workloads']}"
    )

    print(
        f"Total GPU demand: "
        f"{summary['total_gpu_demand']}"
    )

    print(
        f"Total compute: "
        f"{summary['total_compute_gpu_hours']} GPU-hours"
    )

    print(
        f"High priority: "
        f"{summary['high_priority']}"
    )

    print(
        f"Medium priority: "
        f"{summary['medium_priority']}"
    )

    print(
        f"Low priority: "
        f"{summary['low_priority']}"
    )

    print()
    print("POWEROS REALISTIC DATASET READY")


if __name__ == "__main__":
    main()