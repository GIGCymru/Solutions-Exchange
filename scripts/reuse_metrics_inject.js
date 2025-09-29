// ...existing code...
// Fetch and display private metrics
async function fetchPrivateMetrics() {
    // ...existing code...
}

// Fetch and display reuse metrics
async function fetchReuseMetrics() {
    try {
        const response = await fetch('data/reuse_metrics.json');
        const metrics = await response.json();
        // Count repos with forks, clones, or downloads > 0
        const reusedRepos = metrics.filter(m => (m.forks_count > 0) || (m.clones_count > 0) || (m.downloads_count > 0));
        const totalReused = reusedRepos.length;
        // Top 3 reused repos by sum of metrics
        const topRepos = [...reusedRepos].sort((a, b) => {
            const aTotal = (a.forks_count || 0) + (a.clones_count || 0) + (a.downloads_count || 0);
            const bTotal = (b.forks_count || 0) + (b.clones_count || 0) + (b.downloads_count || 0);
            return bTotal - aTotal;
        }).slice(0, 3);
        let topHtml = '';
        if (topRepos.length > 0) {
            topHtml = '<ul class="list-unstyled">' + topRepos.map(r =>
                `<li><strong>${r.owner}/${r.name}</strong>: Forks: ${r.forks_count || 0}, Clones: ${r.clones_count || 0}, Downloads: ${r.downloads_count || 0}</li>`
            ).join('') + '</ul>';
        }
        const reuseHtml = `
            <div class="col-md-12 mb-4">
                <div class="private-metric-card">
                    <div class="icon">
                        <i class="fas fa-recycle"></i>
                    </div>
                    <h2>${totalReused}</h2>
                    <p>Re-used Repositories</p>
                    <div class="metric-source">Based on forks, clones, or downloads</div>
                    ${topHtml ? `<div class="mt-3"><strong>Top Re-used:</strong>${topHtml}</div>` : ''}
                </div>
            </div>
        `;
        // Insert after private metrics
        const metricsDiv = document.getElementById('privateMetricsCards');
        metricsDiv.insertAdjacentHTML('beforeend', reuseHtml);
    } catch (error) {
        console.error('Error fetching reuse metrics:', error);
    }
}

// Fetch data and render charts
// ...existing code...
document.addEventListener('DOMContentLoaded', async function() {
    const repoData = await fetch('data/repositories.json').then(r => r.json());
    // Load private metrics first
    await fetchPrivateMetrics();
    // Load reuse metrics next
    await fetchReuseMetrics();
    // Then load charts
    renderRepoGrowthChart(repoData);
    renderOrgReposChart(repoData);
    renderLangDistChart(repoData);
    renderStarsDistChart(repoData);
    renderActivityTrendChart(repoData);
});
// ...existing code...
