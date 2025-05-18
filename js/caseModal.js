export async function showCaseDetails(caseID) {
    const modal = document.getElementById("case-modal");
    const spinner = document.getElementById("wait-spinner-case");
    const content = document.querySelector(".case-modal-content");
    const caseBtn = document.getElementById("suspend-acct-button");
    const closeBtn = document.getElementById("modal-close");
    const caseIDSpan = document.getElementById("case-id-no-span");
    const userID = document.getElementById("user-id-span");
    const dateCreated = document.getElementById("created-at-span");
    const riskLevel = document.getElementById("risk-level-span");
    const recommendedAction = document.getElementById("reco-action-span");
    const justificationSpan = document.getElementById("justification-span");
    const username = document.getElementById("username-span");
    const acctCreated = document.getElementById("acct-created-span");
    const ipAdd = document.getElementById("ip-span");
    const deviceInfo = document.getElementById("device-info-span");
    const browserInfo = document.getElementById("browser-info-span");
    const botBool = document.getElementById("is-bot-span");
    const geoInfo = document.getElementById("geo-info-span");
    const lastActive = document.getElementById("last-active-span");
    const idleTime = document.getElementById("time-idle-span");
    const isActive = document.getElementById("is-active-span");
    const ipdbInfo = document.getElementById("ipdb-json");
    //const ipAddress = document.getElementById("ip-address");
    //const isPublic = document.getElementById("is-public");
    //const isTor = document.getElementById("is-tor");
    //const totalReports = document.getElementById("total-reports");
    //const lastReported = document.getElementById("last-reported");
    //const isWhitelisted = document.getElementById("is-whitelisted");
    //const abuseScore = document.getElementById("abuse-score");
    //const countryCode = document.getElementById("country-code");
    //const usageType = document.getElementById("usage-type");
    //const ispName = document.getElementById("isp-name");
    //const domainName = document.getElementById("domain-name");
    //const hostName = document.getElementById("host-name");

    // Reset UI
    content.classList.remove("visible");
    content.style.display = "none";
    spinner.classList.remove("hidden");
    modal.classList.remove("hidden");

    caseBtn.onclick = () => {
        alert(`Account Suspend for Case ${caseID}`);
        modal.classList.add("hidden");
    }
    closeBtn.onclick = () => modal.classList.add("hidden");
    window.onclick = (e) => { if (e.target === modal) modal.classList.add("hidden"); };

    try {
        const response = await fetch(`/flagged-visitors/${caseID}`);

        const result = await response.json();

        const {
            id,
            visitor_id,
            risk_level,
            justification,
            recommended_action,
            created_at,
            visitor_info
        } = result;

        // Populate modal fields
        caseIDSpan.textContent = caseID;
        dateCreated.textContent = created_at;
        riskLevel.textContent = risk_level;
        justificationSpan.textContent = justification;
        recommendedAction.textContent = recommended_action;
        caseBtn.textContent = `Suspend Account for Visitor ${visitor_id}`;

        // Visitor info block
        userID.textContent = id;
        username.textContent = visitor_info.username;
        acctCreated.textContent = visitor_info.acct_created;
        ipAdd.textContent = `${visitor_info.ip}:${visitor_info.port}`;
        deviceInfo.textContent = visitor_info.device_info;
        browserInfo.textContent = visitor_info.browser_info;
        botBool.textContent = visitor_info.is_bot ? "Yes" : "No";
        geoInfo.textContent = visitor_info.geo_info;
        lastActive.textContent = visitor_info.last_active;
        idleTime.textContent = visitor_info.time_idle;
        isActive.textContent = visitor_info.is_active ? "Yes" : "No";

        ipdbInfo.textContent = JSON.stringify(visitor_info.ipdb, null, 2);
        // Format and populate IPDB fields
        //const ipdb = visitor_info.ipdb || {};

        //ipAddress.textContent = ipdb.ipAddress ?? "N/A";
        //isPublic.textContent = ipdb.isPublic ? "Yes" : "No";
        //isTor.textContent = ipdb.isTor ? "Yes" : "No";
        //totalReports.textContent = ipdb.totalReports ?? "0";
        //lastReported.textContent = ipdb.lastReportedAt ?? "N/A";
        //isWhitelisted.textContent = ipdb.isWhitelisted === true ? "Yes" : ipdb.isWhitelisted === false ? "No" : "Unknown";
        //abuseScore.textContent = ipdb.abuseConfidenceScore ?? "0";
        //countryCode.textContent = ipdb.countryCode ?? "N/A";
        //usageType.textContent = ipdb.usageType ?? "N/A";
        //ispName.textContent = ipdb.isp ?? "N/A";
        //domainName.textContent = ipdb.domain ?? "N/A";
        //hostName.textContent = (ipdb.hostnames && ipdb.hostnames.length > 0) ? ipdb.hostnames[0] : "N/A";

        spinner.classList.add("hidden");
        modal.classList.remove("hidden");
        content.style.display = "block";
        setTimeout(() => content.classList.add("visible"), 10);


    } catch (err) {
        console.error("failed to load case details:", err);
        alert("Failed to load case details.");
        modal.classList.add("hidden");
    } finally {
        spinner.classList.add("hidden");
    }

}