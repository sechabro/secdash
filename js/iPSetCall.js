export async function iPSetCall(ip) {
    try {
        const req = await fetch("/ipset-calling", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(ip)
        });
        const resp = await req.json();
        return resp;
    } catch (err) {
        console.error("Ipset Call Failed:", err);
        alert("Failed to complete IP status update. See console.")
    }
};