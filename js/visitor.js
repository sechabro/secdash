
async function fetchVisitorData() {
    try {
        const response = await fetch('/visitor');
        const data = await response.json();
        const { ipdb: { data: ipDetails }, ...rest } = data;

        let visitorContent = "<ul>";
        for (const key in rest) {
            if (typeof rest[key] === "object" && rest[key] !== null) {
                visitorContent += `<li><strong>${key}:</strong><pre>${JSON.stringify(rest[key], null, 2)}</pre></li>`;
            } else {
                visitorContent += `<li><strong>${key}:</strong> ${rest[key]}</li>`;
            }
        }
        visitorContent += "</ul>";

        let abuseIpdb = "<ul>";
        for (const key in ipDetails) {
            if (typeof ipDetails[key] === "object" && ipDetails[key] !== null) {
                abuseIpdb += `<li><strong>${key}:</strong><pre>${JSON.stringify(ipDetails[key], null, 2)}</pre></li>`;
            } else {
                abuseIpdb += `<li><strong>${key}:</strong> ${ipDetails[key]}</li>`;
            }
        }
        abuseIpdb += "</ul>";

        // Display data in appropriate divs
        document.getElementById('visitor-data').innerHTML = visitorContent;
        document.getElementById('ipdb-data').innerHTML = abuseIpdb;
    } catch (error) {
        console.error('Error fetching visitor data:', error);
    }
}
// Collapsible content functionality
document.querySelector('.collapsible').addEventListener('click', () => {
    const content = document.querySelector('.collapsible-content');
    content.style.display = content.style.display === 'block' ? 'none' : 'block';
});