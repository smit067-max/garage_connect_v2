document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on the analytics page
    if (!document.getElementById('revenue-trend-chart')) return;

    // Global Chart.js defaults
    Chart.defaults.color = '#94a3b8'; // text-secondary
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.9)'; // dark bg
    Chart.defaults.plugins.tooltip.titleFont = { size: 14, family: "'Outfit', sans-serif" };
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    
    const chartColors = [
        '#f97316', '#06b6d4', '#22c55e', '#a855f7', 
        '#ec4899', '#eab308', '#3b82f6', '#14b8a6', 
        '#f43f5e', '#8b5cf6', '#10b981', '#f59e0b'
    ];

    // Store chart instances to destroy them before re-rendering
    const chartInstances = new Map();

    // Formatters
    const formatCurrency = (value) => {
        if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
        if (value >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
        return `₹${value}`;
    };

    const formatPercent = (value) => `${value.toFixed(1)}%`;

    // Initialize
    fetchAndRender('month');

    // Period toggle buttons
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Update active state
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active', 'btn-primary'));
            document.querySelectorAll('.period-btn').forEach(b => b.classList.add('btn-secondary'));
            
            const target = e.currentTarget;
            target.classList.remove('btn-secondary');
            target.classList.add('active', 'btn-primary');
            
            const period = target.getAttribute('data-period');
            fetchAndRender(period);
        });
    });

    async function fetchAndRender(period) {
        try {
            // In a real app, this would be: 
            // const response = await fetch(`/api/garage/analytics?period=${period}`);
            // const data = await response.json();
            
            // Mock data for demonstration purposes
            const data = getMockData(period);
            
            renderKPIs(data.kpis);
            renderRevenueTrend(data.revenue_trend);
            renderProfitVsRevenue(data.revenue_trend);
            renderServiceBreakdown(data.service_breakdown);
            renderRevenueByService(data.service_breakdown);
            renderMonthlyComparison(data.monthly_comparison);
            renderCustomerStats(data.customer_stats);
            renderPartsUsage(data.parts_usage);
            renderPeakDays(data.peak_days);
            
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    }

    function createOrUpdateChart(canvasId, config) {
        if (chartInstances.has(canvasId)) {
            chartInstances.get(canvasId).destroy();
        }
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        const chart = new Chart(ctx, config);
        chartInstances.set(canvasId, chart);
        return chart;
    }

    function renderKPIs(kpis) {
        // Animate counter values
        document.getElementById('kpi-revenue').setAttribute('data-value', kpis.revenue);
        document.getElementById('kpi-profit').setAttribute('data-value', kpis.profit);
        document.getElementById('kpi-jobs').setAttribute('data-value', kpis.jobs);
        
        // Trigger the counter animation from main.js (or implement simple version here)
        const formatValue = (el, val, prefix='') => {
            el.innerText = prefix + val.toLocaleString();
        };
        
        formatValue(document.getElementById('kpi-revenue'), kpis.revenue, '₹');
        formatValue(document.getElementById('kpi-profit'), kpis.profit, '₹');
        formatValue(document.getElementById('kpi-jobs'), kpis.jobs, '');
    }

    function renderRevenueTrend(data) {
        const ctx = document.getElementById('revenue-trend-chart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(249, 115, 22, 0.5)'); // orange
        gradient.addColorStop(1, 'rgba(249, 115, 22, 0.0)');

        createOrUpdateChart('revenue-trend-chart', {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Revenue',
                    data: data.revenue,
                    borderColor: '#f97316',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4, // Smooth curve
                    pointBackgroundColor: '#0f172a',
                    pointBorderColor: '#f97316',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => formatCurrency(context.raw)
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { callback: (value) => formatCurrency(value) }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                animation: { duration: 800, easing: 'easeOutQuart' }
            }
        });
    }

    function renderProfitVsRevenue(data) {
        createOrUpdateChart('profit-revenue-chart', {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: data.revenue,
                        borderColor: '#f97316',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        tension: 0.4
                    },
                    {
                        label: 'Profit',
                        data: data.profit,
                        borderColor: '#06b6d4', // teal
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        tension: 0.4,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { callback: (value) => formatCurrency(value) }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    function renderServiceBreakdown(data) {
        createOrUpdateChart('service-breakdown-chart', {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.counts,
                    backgroundColor: chartColors.slice(0, data.labels.length),
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#f8fafc', padding: 20 }
                    }
                }
            }
        });
    }

    function renderRevenueByService(data) {
        createOrUpdateChart('revenue-service-chart', {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Revenue',
                    data: data.revenue,
                    backgroundColor: 'rgba(6, 182, 212, 0.8)', // teal
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bar chart
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { callback: (value) => formatCurrency(value) }
                    },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    function renderMonthlyComparison(data) {
        createOrUpdateChart('monthly-comparison-chart', {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'This Month',
                        data: data.current,
                        backgroundColor: '#f97316',
                        borderRadius: 4
                    },
                    {
                        label: 'Last Month',
                        data: data.previous,
                        backgroundColor: '#334155',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { callback: (value) => formatCurrency(value) }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    function renderCustomerStats(data) {
        createOrUpdateChart('customer-stats-chart', {
            type: 'line', // Area chart
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'New Customers',
                        data: data.new,
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.2)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Returning',
                        data: data.returning,
                        borderColor: '#a855f7',
                        backgroundColor: 'rgba(168, 85, 247, 0.2)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    y: { stacked: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    function renderPartsUsage(data) {
        createOrUpdateChart('parts-usage-chart', {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Units Used',
                    data: data.values,
                    backgroundColor: '#eab308', // yellow
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    function renderPeakDays(data) {
        createOrUpdateChart('peak-days-chart', {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Jobs Completed',
                    data: data.values,
                    backgroundColor: data.values.map((v, i) => 
                        i === data.values.indexOf(Math.max(...data.values)) 
                        ? '#f97316' // Highlight max day
                        : '#334155'
                    ),
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Mock Data Generator for demonstration
    function getMockData(period) {
        const labels = period === 'week' ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] 
                     : period === 'month' ? Array.from({length: 4}, (_, i) => `Week ${i+1}`)
                     : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                     
        const multiplier = period === 'week' ? 1 : period === 'month' ? 4 : 40;

        return {
            kpis: {
                revenue: 45000 * multiplier,
                profit: 12000 * multiplier,
                jobs: 15 * multiplier
            },
            revenue_trend: {
                labels,
                revenue: labels.map(() => Math.floor(Math.random() * 10000 * multiplier) + 5000 * multiplier),
                profit: labels.map(() => Math.floor(Math.random() * 3000 * multiplier) + 1000 * multiplier)
            },
            service_breakdown: {
                labels: ['General Service', 'Denting/Painting', 'AC Service', 'Tyre/Wheel', 'Engine Repair'],
                counts: [45, 25, 15, 10, 5],
                revenue: [150000, 200000, 45000, 30000, 120000]
            },
            monthly_comparison: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                current: [45000, 52000, 48000, 61000],
                previous: [40000, 42000, 45000, 49000]
            },
            customer_stats: {
                labels,
                new: labels.map(() => Math.floor(Math.random() * 10 * multiplier)),
                returning: labels.map(() => Math.floor(Math.random() * 15 * multiplier))
            },
            parts_usage: {
                labels: ['Engine Oil', 'Oil Filter', 'Brake Pads', 'Air Filter', 'Wiper Blades'],
                values: [120, 115, 45, 80, 30]
            },
            peak_days: {
                values: [12, 15, 18, 14, 25, 30, 22] // Sat usually busiest
            }
        };
    }
});
