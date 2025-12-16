// Track current state
let currentTimeframe = 'max';
let currentMode = 'Returns';

// Add event listeners to timeframe buttons
document.querySelectorAll('button[data-timeframe]').forEach(button => {
    button.addEventListener('click', function() {
        // Update active button styling
        document.querySelectorAll('button[data-timeframe]').forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
        
        // Update timeframe and fetch new data
        currentTimeframe = this.dataset.timeframe;
        updateChart();
    });
});

// Add event listeners to mode radio buttons
document.querySelectorAll('input[name="chartMode"]').forEach(radio => {
    radio.addEventListener('change', function() {
        currentMode = this.value;
        updateChart();
    });
});

// Function to fetch and update chart
function updateChart() {
    // Build URL with parameters
    const url = `/api/chart-data?timeframe=${currentTimeframe}&mode=${currentMode}`;
    
    // Fetch new chart data
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Update chart using Plotly.react (more efficient than newPlot)
            Plotly.react('chartDiv', data.chart.data, data.chart.layout, {responsive: true});
        })
        .catch(error => console.error('Error updating chart:', error));
}