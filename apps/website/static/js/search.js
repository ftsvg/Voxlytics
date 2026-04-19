let currentUrl = null;

async function searchPlayer() {
    const ign = document.getElementById("ignInput").value.trim();

    const img = document.getElementById("resultImage");
    const error = document.getElementById("errorMsg");
    const loader = document.getElementById("loader");

    if (!ign) return;

    error.textContent = "";
    img.style.display = "none";
    loader.style.display = "block";

    try {
        const response = await fetch(
            `/api/player?ign=${encodeURIComponent(ign)}&t=${Date.now()}`
        );

        if (!response.ok) {
            let message = "Something went wrong";

            try {
                const data = await response.json();
                message = data.error || message;
            } catch (_) {
            }

            error.textContent = message;

            loader.style.display = "none";
            return;
        }

        const blob = await response.blob();

        if (currentUrl) {
            URL.revokeObjectURL(currentUrl);
        }

        currentUrl = URL.createObjectURL(blob);

        img.src = currentUrl;

        loader.style.display = "none";
        img.style.display = "block";

    } catch (err) {
        console.error(err);

        error.textContent = "Failed to fetch player";

        loader.style.display = "none";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("ignInput");
    const button = document.getElementById("searchBtn");

    button.addEventListener("click", searchPlayer);

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            searchPlayer();
        }
    });
});