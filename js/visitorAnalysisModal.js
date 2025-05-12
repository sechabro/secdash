import { startCase } from './flagAccount.js';

export async function showVisitorAnalysis(visitor) {
    const modal = document.getElementById("analysis-modal");
    const content = document.querySelector(".modal-content");
    const spinner = document.getElementById("analysis-loading");
    const riskLevelSpan = document.getElementById("risk-level");
    const justificationSpan = document.getElementById("justification");
    const actionSpan = document.getElementById("recommended-action");
    const caseBtn = document.getElementById("case-action-button");
    const closeBtn = document.getElementById("modal-close");

    // Setup: hide content, show spinner
    content.classList.remove("visible");
    content.style.display = "none";
    spinner.classList.remove("hidden");
    modal.classList.remove("hidden");

    // Modal close logic
    closeBtn.onclick = () => modal.classList.add("hidden");
    window.onclick = (e) => { if (e.target === modal) modal.classList.add("hidden"); };

    try {
        const response = await fetch("/visitor-analysis", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(visitor)
        });
        const result = await response.json();

        riskLevelSpan.textContent = result.risk_level;
        justificationSpan.textContent = result.justification;
        actionSpan.textContent = result.recommended_action;

        caseBtn.textContent = "Create Case";
        caseBtn.onclick = async () => {
            startCase(visitor, result);
            alert(`User "${visitor.username}" flagged and added to cases.`);
            modal.classList.add("hidden");
        };

        spinner.classList.add("hidden");
        content.style.display = "block";
        setTimeout(() => content.classList.add("visible"), 10);

    } catch (err) {
        console.error("Analysis failed:", err);
        alert("Failed to analyze visitor.");
        modal.classList.add("hidden");
    } finally {
        spinner.classList.add("hidden");
    }
}