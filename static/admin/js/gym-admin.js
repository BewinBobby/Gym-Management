document.addEventListener("DOMContentLoaded", function () {

    const ctx = document.getElementById("gymChart");

    if (ctx) {
        new Chart(ctx, {
            type: "line",
            data: {
                labels: ["Jan", "Feb", "Mar", "Apr", "May"],
                datasets: [{
                    label: "New Members",
                    data: [12, 19, 8, 15, 22],
                    borderColor: "#f97316",
                    tension: 0.4
                }]
            },
            options: {
                responsive: true
            }
        });
    }

});
