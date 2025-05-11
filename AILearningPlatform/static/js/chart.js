/**
 * Chart.js implementation for dashboard visualizations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Course Progress Chart
    const progressChartElement = document.getElementById('courseProgressChart');
    if (progressChartElement) {
        // Get data from the data attributes
        const courseTitles = JSON.parse(progressChartElement.getAttribute('data-titles'));
        const courseProgress = JSON.parse(progressChartElement.getAttribute('data-progress'));
        
        new Chart(progressChartElement, {
            type: 'bar',
            data: {
                labels: courseTitles,
                datasets: [{
                    label: 'Course Progress (%)',
                    data: courseProgress,
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw + '%';
                            }
                        }
                    }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    
    // Weekly Activity Chart
    const activityChartElement = document.getElementById('weeklyActivityChart');
    if (activityChartElement) {
        // Generate some demo data for weekly activity
        const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const activityData = [];
        
        // Generate random activity data or use actual data if available
        for (let i = 0; i < 7; i++) {
            activityData.push(Math.floor(Math.random() * 120));
        }
        
        new Chart(activityChartElement, {
            type: 'line',
            data: {
                labels: daysOfWeek,
                datasets: [{
                    label: 'Minutes Spent Learning',
                    data: activityData,
                    fill: true,
                    backgroundColor: 'rgba(0, 200, 255, 0.2)',
                    borderColor: 'rgba(0, 200, 255, 1)',
                    tension: 0.4
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + ' min';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw + ' minutes';
                            }
                        }
                    }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    
    // Achievement Progress Chart
    const achievementChartElement = document.getElementById('achievementProgressChart');
    if (achievementChartElement) {
        // Get data from the data attributes or use demo data
        const earnedCount = parseInt(achievementChartElement.getAttribute('data-earned') || 3);
        const totalCount = parseInt(achievementChartElement.getAttribute('data-total') || 10);
        
        new Chart(achievementChartElement, {
            type: 'doughnut',
            data: {
                labels: ['Earned', 'Remaining'],
                datasets: [{
                    data: [earnedCount, totalCount - earnedCount],
                    backgroundColor: [
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(108, 117, 125, 0.5)'
                    ],
                    borderColor: [
                        'rgba(255, 193, 7, 1)',
                        'rgba(108, 117, 125, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label;
                                const value = context.raw;
                                return label + ': ' + value + ' badge' + (value !== 1 ? 's' : '');
                            }
                        }
                    }
                },
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%'
            }
        });
        
        // Add center text
        Chart.register({
            id: 'achievementCenterText',
            beforeDraw: function(chart) {
                if (chart.config.type === 'doughnut') {
                    const width = chart.width;
                    const height = chart.height;
                    const ctx = chart.ctx;
                    
                    ctx.restore();
                    const fontSize = (height / 114).toFixed(2);
                    ctx.font = fontSize + 'em sans-serif';
                    ctx.textBaseline = 'middle';
                    
                    const text = earnedCount + '/' + totalCount;
                    const textX = Math.round((width - ctx.measureText(text).width) / 2);
                    const textY = height / 2;
                    
                    ctx.fillStyle = '#fff';
                    ctx.fillText(text, textX, textY);
                    ctx.save();
                }
            }
        });
    }
});
