
"use strict";

/* =========================================================
   ZYVARENTH PowerOS — CUSTOMER RESULTS
   Dashboard 2 only
========================================================= */

(function () {
    function byId(id) {
        return document.getElementById(id);
    }

    function escapeHTML(value) {
        return String(value ?? "—").replace(/[&<>"']/g, function (c) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[c];
        });
    }

    function displayValue(value) {
        return value === undefined || value === null || value === ""
            ? "—"
            : value;
    }

    function getValue(item, keys) {
        if (!item || typeof item !== "object") {
            return "—";
        }

        for (const key of keys) {
            if (item[key] !== undefined && item[key] !== null) {
                return item[key];
            }
        }

        return "—";
    }

    function getResultBox() {
        let box = byId("customerResult");

        if (box) {
            return box;
        }

        const button = byId("customerRunButton");

        if (!button) {
            console.error(
                "PowerOS: customerRunButton was not found."
            );
            return null;
        }

        box = document.createElement("section");
        box.id = "customerResult";
        box.className = "customer-result";
        box.setAttribute("aria-live", "polite");

        button.insertAdjacentElement("afterend", box);

        return box;
    }

    function addStyles() {
        if (byId("customerResultsStyles")) {
            return;
        }

        const style = document.createElement("style");
        style.id = "customerResultsStyles";

        style.textContent = `
            #customerResult {
                margin-top: 24px;
                padding: 24px;
                border: 1px solid #dbe4ef;
                border-radius: 16px;
                background: #ffffff;
                color: #102f55;
                overflow: hidden;
            }

            #customerResult h3 {
                margin: 0 0 18px;
                font-size: 25px;
            }

            #customerResult h4 {
                margin: 26px 0 12px;
                font-size: 18px;
            }

            .cr-metrics {
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(150px, 1fr));
                gap: 12px;
                margin: 18px 0;
            }

            .cr-metric {
                padding: 15px;
                border: 1px solid #dbe4ef;
                border-radius: 10px;
                background: #f6f8fc;
                overflow-wrap: anywhere;
            }

            .cr-metric-label {
                display: block;
                color: #61758e;
                font-size: 13px;
                margin-bottom: 8px;
            }

            .cr-metric-value {
                font-size: 21px;
                font-weight: 700;
            }

            .cr-table-wrap {
                width: 100%;
                overflow-x: auto;
                margin: 12px 0 22px;
            }

            .cr-table {
                width: 100%;
                min-width: 720px;
                border-collapse: collapse;
                background: #fff;
            }

            .cr-table th,
            .cr-table td {
                padding: 12px;
                text-align: left;
                vertical-align: top;
                border-bottom: 1px solid #e0e7f0;
                font-size: 13px;
            }

            .cr-table th {
                background: #edf3fa;
                color: #173b64;
            }

            .cr-empty {
                padding: 14px;
                border-radius: 8px;
                background: #f4f7fb;
                color: #526780;
            }

            .cr-status {
                margin-top: 20px;
                padding: 14px;
                border-radius: 9px;
                background: #eaf7ef;
                color: #17683b;
                font-weight: 700;
            }

            .cr-error {
                background: #fff0f0;
                color: #a32121;
                border-color: #efcaca;
            }

            @media (max-width: 600px) {
                #customerResult {
                    padding: 15px;
                }
            }
        `;

        document.head.appendChild(style);
    }

    function renderMetrics(items) {
        return `
            <div class="cr-metrics">
                ${items.map(([label, value, unit]) => `
                    <div class="cr-metric">
                        <span class="cr-metric-label">
                            ${escapeHTML(label)}
                        </span>
                        <span class="cr-metric-value">
                            ${escapeHTML(displayValue(value))}
                            ${escapeHTML(unit || "")}
                        </span>
                    </div>
                `).join("")}
            </div>
        `;
    }

    function renderWorkloadTable(items, emptyMessage) {
        if (!Array.isArray(items) || items.length === 0) {
            return `<div class="cr-empty">${escapeHTML(emptyMessage)}</div>`;
        }

        const rows = items.map(item => `
            <tr>
                <td>${escapeHTML(getValue(item, ["workload_id", "id"]))}</td>
                <td>${escapeHTML(getValue(item, ["gpu_required", "gpus"]))}</td>
                <td>${escapeHTML(getValue(item, ["duration_hours", "duration"]))}</td>
                <td>${escapeHTML(getValue(item, ["deadline_hour", "deadline"]))}</td>
                <td>${escapeHTML(getValue(item, ["priority"]))}</td>
                <td>${escapeHTML(getValue(item, ["start_hour", "start_time"]))}</td>
                <td>${escapeHTML(getValue(item, ["finish_hour", "end_hour", "end_time"]))}</td>
                <td>${escapeHTML(getValue(item, ["reason", "status"]))}</td>
            </tr>
        `).join("");

        return `
            <div class="cr-table-wrap">
                <table class="cr-table">
                    <thead>
                        <tr>
                            <th>Workload ID</th>
                            <th>GPUs</th>
                            <th>Duration (h)</th>
                            <th>Deadline</th>
                            <th>Priority</th>
                            <th>Start hour</th>
                            <th>Finish hour</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    }

    function renderDecisionTable(decisions) {
        if (!Array.isArray(decisions) || decisions.length === 0) {
            return `
                <div class="cr-empty">
                    No individual decision records were returned.
                </div>
            `;
        }

        return `
            <div class="cr-table-wrap">
                <table class="cr-table">
                    <thead>
                        <tr>
                            <th>Workload ID</th>
                            <th>Action</th>
                            <th>Status</th>
                            <th>Start hour</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${decisions.map(item => `
                            <tr>
                                <td>${escapeHTML(getValue(item, ["workload_id", "id"]))}</td>
                                <td>${escapeHTML(getValue(item, ["action", "decision"]))}</td>
                                <td>${escapeHTML(getValue(item, ["status"]))}</td>
                                <td>${escapeHTML(getValue(item, ["start_hour"]))}</td>
                                <td>${escapeHTML(getValue(item, ["reason", "message"]))}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderDecisionSummary(summary) {
        const data = summary || {};

        return renderMetrics([
            ["RUN", data.run ?? 0, "workloads"],
            ["SHIFT", data.shift ?? 0, "workloads"],
            ["WAIT", data.wait ?? 0, "workloads"],
            [
                "PROTECT DEADLINE",
                data.protect_deadline ?? 0,
                "workloads"
            ]
        ]);
    }

    function renderResult(result) {
        const box = getResultBox();

        if (!box) {
            throw new Error("Could not create the customer results area.");
        }

        const infrastructure = result.infrastructure || {};
        const optimization = result.optimization || {};
        const power = result.power_summary || {};

        const scheduled = optimization.scheduled_workloads || [];
        const unscheduled = optimization.unscheduled_workloads || [];

        box.className = "customer-result";

        box.innerHTML = `
            <h3>POWEROS CUSTOMER RESULT</h3>

            <p>
                <strong>Customer:</strong>
                ${escapeHTML(result.customer_name)}
            </p>

            <h4>Infrastructure Summary</h4>

            ${renderMetrics([
                ["GPUs", infrastructure.gpus, ""],
                ["Submitted workloads", infrastructure.workloads, ""],
                ["Scheduled", optimization.scheduled, ""],
                ["Unscheduled", optimization.unscheduled, ""],
                ["Available power", infrastructure.available_power_kw, "kW"],
                ["Grid capacity", infrastructure.grid_capacity_kw, "kW"],
                ["Electricity price", infrastructure.electricity_price_per_kwh, "₹/kWh"],
                ["Solar power", infrastructure.solar_power_kw, "kW"],
                ["Battery power", infrastructure.battery_available_kw, "kW"],
                ["PUE", infrastructure.pue, ""]
            ])}

            <h4>Scheduled Workloads</h4>

            ${renderWorkloadTable(
                scheduled,
                "No scheduled workload records were returned."
            )}

            <h4>Unscheduled Workloads</h4>

            ${renderWorkloadTable(
                unscheduled,
                "No unscheduled workload records were returned."
            )}

            <h4>PowerOS Decision Summary</h4>

            ${renderDecisionSummary(result.decision_summary)}

            <h4>Individual PowerOS Decisions</h4>

            ${renderDecisionTable(result.decisions)}

            <h4>Power Summary</h4>

            ${renderMetrics([
                ["Peak facility power", power.peak_facility_power_kw, "kW"],
                ["Total IT power", power.total_it_power_kw, "kW"],
                ["Cooling overhead", power.cooling_overhead_kw, "kW"],
                ["Total facility energy", power.total_facility_energy_kwh, "kWh"]
            ].filter(item => item[1] !== undefined && item[1] !== null))}

            <div class="cr-status">
                ✓ ${escapeHTML(
                    result.message || "PowerOS customer run completed."
                )}
            </div>
        `;

        box.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    async function runCustomerPowerOS() {
        const button = byId("customerRunButton");
        const box = getResultBox();

        if (!button || !box) {
            console.error("Customer button or result area is missing.");
            return;
        }

        if (typeof window.buildCustomerPayload !== "function") {
            box.className = "customer-result cr-error";
            box.textContent =
                "Customer input builder is missing. Check the Dashboard 2 script.";
            return;
        }

        button.disabled = true;
        const oldText = button.textContent;
        button.textContent = "RUNNING POWEROS...";

        box.className = "customer-result";
        box.textContent = "PowerOS is processing the customer workloads...";

        try {
            const payload = window.buildCustomerPayload();

            if (!payload.customer_name) {
                throw new Error("Enter a customer name.");
            }

            if (!Array.isArray(payload.workloads) ||
                payload.workloads.length === 0) {
                throw new Error("Add at least one workload.");
            }

            const response = await fetch("/api/customer/run", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok || result.status !== "SUCCESS") {
                throw new Error(
                    result.error || "The PowerOS customer API failed."
                );
            }

            renderResult(result);

            console.log("POWEROS CUSTOMER RESULT:", result);

        } catch (error) {
            console.error("Customer PowerOS error:", error);

            box.className = "customer-result cr-error";
            box.textContent = "PowerOS error: " + error.message;

        } finally {
            button.disabled = false;
            button.textContent = oldText || "RUN POWEROS FOR CUSTOMER";
        }
    }

    function initialize() {
        addStyles();

        const button = byId("customerRunButton");

        if (!button) {
            console.error(
                "Dashboard 2: customerRunButton was not found."
            );
            return;
        }

        // Preserve compatibility with an existing inline onclick handler.
        window.runCustomerPowerOS = runCustomerPowerOS;

        // Also support buttons that do not have an onclick attribute.
        if (!button.hasAttribute("onclick")) {
            button.addEventListener("click", runCustomerPowerOS);
        }

        // Create the results section immediately if it is missing.
        getResultBox();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }
})();
