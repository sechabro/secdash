export async function fetchVisitorData() {
    const visitorRes = await fetch('/visitor');
    const visitorData = await visitorRes.json();
    const { ipdb: { data: ipDetails }, ...rest } = visitorData;

    let visitorContent = "<ul>";
    for (const key in rest) {
        visitorContent += `<li><strong>${key}:</strong> ${typeof rest[key] === "object" && rest[key] !== null
            ? `<pre>${JSON.stringify(rest[key], null, 2)}</pre>`
            : rest[key]
            }</li>`;
    }
    visitorContent += "</ul>";

    let abuseIpdb = "<ul>";
    for (const key in ipDetails) {
        abuseIpdb += `<li><strong>${key}:</strong> ${typeof ipDetails[key] === "object" && ipDetails[key] !== null
            ? `<pre>${JSON.stringify(ipDetails[key], null, 2)}</pre>`
            : ipDetails[key]
            }</li>`;
    }
    abuseIpdb += "</ul>";

    document.getElementById('visitor-data').innerHTML = visitorContent;
    document.getElementById('ipdb-data').innerHTML = abuseIpdb;
}