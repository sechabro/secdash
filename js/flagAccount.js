export async function startCase(visitor, result) {
    try {
        const connRes = await fetch('/visitor-flag', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                visitor_id: visitor.visitor_id,
                risk_level: result.risk_level,
                justification: result.justification,
                recommended_action: result.recommended_action
            })
        });

        if (!connRes.ok) {
            const errorText = await connRes.text();
            console.error("Failed to flag visitor:", errorText);
            alert("Something went wrong creating the case.");
        }

    } catch (err) {
        console.error("Error during case creation:", err);
        alert("Failed to connect to the server.");
    }

}