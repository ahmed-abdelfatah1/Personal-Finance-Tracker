/**
 * Chart.js utility functions for Personal Finance Tracker
 */

/**
 * Load and display monthly cash flow chart
 * @param {number} year - The year to display data for
 */
function loadMonthlyCashFlowChart(year, currency) {
    const ctx = document.getElementById('cashFlowChart');
    if (!ctx) {
        console.error('Chart canvas not found');
        return;
    }

    // Default currency if not provided
    currency = currency || 'EGP';

    // Fetch chart data from API
    fetch(`/reports/monthly-cash-flow/chart-data?year=${year}&currency=${currency}`)
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(2) + ' ' + currency;
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + 
                                           context.parsed.y.toFixed(2) + ' ' + currency;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            ctx.parentElement.innerHTML = '<p class="text-danger">Error loading chart data. Please try again.</p>';
        });
}

/**
 * Initialize dashboard charts (if needed)
 */
function initDashboardCharts() {
    // Add dashboard-specific chart initialization here
    console.log('Dashboard charts initialized');
}

