/**
 * ATS MAFIA Charts & Visualizations
 * Handles all chart rendering using Chart.js
 */

class ATSCharts {
    constructor() {
        this.charts = new Map();
        this.defaultColors = {
            gold: '#ffd700',
            darkGold: '#b8860b',
            red: '#b71c1c',
            lightRed: '#ef5350',
            green: '#4caf50',
            blue: '#2196f3',
            orange: '#ff9800',
            gray: '#9e9e9e'
        };
        
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#f5f5f5',
                        font: {
                            family: 'Roboto',
                            size: 12
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#9e9e9e'
                    },
                    grid: {
                        color: 'rgba(158, 158, 158, 0.1)'
                    }
                },
                y: {
                    ticks: {
                        color: '#9e9e9e'
                    },
                    grid: {
                        color: 'rgba(158, 158, 158, 0.1)'
                    }
                }
            }
        };
    }

    /**
     * Create or update performance chart
     */
    createPerformanceChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        // Destroy existing chart if present
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Success Rate',
                        data: data.successRates || [],
                        borderColor: this.defaultColors.gold,
                        backgroundColor: 'rgba(255, 215, 0, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Completion Time',
                        data: data.completionTimes || [],
                        borderColor: this.defaultColors.red,
                        backgroundColor: 'rgba(183, 28, 28, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                ...this.defaultOptions,
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create cost tracking chart
     */
    createCostChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Used Budget', 'Remaining Budget'],
                datasets: [{
                    data: [data.spent || 0, data.remaining || 0],
                    backgroundColor: [
                        this.defaultColors.red,
                        this.defaultColors.green
                    ],
                    borderColor: '#1a1a1a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f5f5f5',
                            font: {
                                family: 'Roboto',
                                size: 12
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create score progression chart
     */
    createScoreProgressionChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Score',
                    data: data.scores || [],
                    borderColor: this.defaultColors.gold,
                    backgroundColor: 'rgba(255, 215, 0, 0.2)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create time efficiency chart
     */
    createTimeEfficiencyChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.phases || [],
                datasets: [
                    {
                        label: 'Time Spent (minutes)',
                        data: data.timeSpent || [],
                        backgroundColor: this.defaultColors.blue,
                        borderColor: this.defaultColors.blue,
                        borderWidth: 1
                    },
                    {
                        label: 'Expected Time (minutes)',
                        data: data.expectedTime || [],
                        backgroundColor: this.defaultColors.gray,
                        borderColor: this.defaultColors.gray,
                        borderWidth: 1
                    }
                ]
            },
            options: this.defaultOptions
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create cost analysis chart
     */
    createCostAnalysisChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.models || [],
                datasets: [{
                    label: 'Cost ($)',
                    data: data.costs || [],
                    backgroundColor: this.defaultColors.lightRed,
                    borderColor: this.defaultColors.red,
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                indexAxis: 'y',
                scales: {
                    x: {
                        ticks: {
                            color: '#9e9e9e',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        },
                        grid: {
                            color: 'rgba(158, 158, 158, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#9e9e9e'
                        },
                        grid: {
                            color: 'rgba(158, 158, 158, 0.1)'
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create stealth rating chart (radar)
     */
    createStealthRatingChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.categories || ['Stealth', 'Speed', 'Accuracy', 'Coverage', 'Efficiency'],
                datasets: [{
                    label: 'Performance',
                    data: data.values || [0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(255, 215, 0, 0.2)',
                    borderColor: this.defaultColors.gold,
                    borderWidth: 2,
                    pointBackgroundColor: this.defaultColors.gold,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: this.defaultColors.gold
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f5f5f5',
                            font: {
                                family: 'Roboto',
                                size: 12
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#9e9e9e',
                            backdropColor: 'transparent'
                        },
                        grid: {
                            color: 'rgba(158, 158, 158, 0.2)'
                        },
                        pointLabels: {
                            color: '#f5f5f5',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create mini performance chart for situation room
     */
    createMiniPerformanceChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Score',
                    data: data.scores || [],
                    borderColor: this.defaultColors.gold,
                    backgroundColor: 'rgba(255, 215, 0, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false,
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create tool usage chart
     */
    createToolUsageChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.tools || [],
                datasets: [{
                    data: data.usage || [],
                    backgroundColor: [
                        this.defaultColors.gold,
                        this.defaultColors.red,
                        this.defaultColors.blue,
                        this.defaultColors.green,
                        this.defaultColors.orange,
                        this.defaultColors.gray
                    ],
                    borderColor: '#1a1a1a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#f5f5f5',
                            font: {
                                family: 'Roboto',
                                size: 11
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Update chart data
     */
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (!chart) return false;

        if (newData.labels) {
            chart.data.labels = newData.labels;
        }

        if (newData.datasets) {
            newData.datasets.forEach((dataset, index) => {
                if (chart.data.datasets[index]) {
                    chart.data.datasets[index].data = dataset.data;
                    if (dataset.label) {
                        chart.data.datasets[index].label = dataset.label;
                    }
                }
            });
        }

        chart.update();
        return true;
    }

    /**
     * Destroy a specific chart
     */
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
            return true;
        }
        return false;
    }

    /**
     * Destroy all charts
     */
    destroyAll() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }

    /**
     * Get chart instance
     */
    getChart(canvasId) {
        return this.charts.get(canvasId);
    }

    /**
     * Check if chart exists
     */
    hasChart(canvasId) {
        return this.charts.has(canvasId);
    }
}

// Create global instance
window.atsCharts = new ATSCharts();