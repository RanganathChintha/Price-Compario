// Performance tracking
class PerformanceTracker {
    constructor() {
        this.metrics = [];
        this.init();
    }
    
    init() {
        // Track page load time
        window.addEventListener('load', () => {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            this.trackMetric('page_load', loadTime);
        });
        
        // Track First Paint
        if (window.performance.getEntriesByType) {
            const paintEntries = performance.getEntriesByType('paint');
            paintEntries.forEach(entry => {
                this.trackMetric(entry.name, entry.startTime);
            });
        }
        
        // Track search performance
        document.addEventListener('searchPerformed', (e) => {
            this.trackMetric('search_time', e.detail.duration);
        });
    }
    
    trackMetric(name, value) {
        this.metrics.push({ name, value, timestamp: Date.now() });
        
        // Send to server if needed
        if (this.metrics.length > 10) {
            this.sendMetrics();
        }
    }
    
    sendMetrics() {
        fetch('/api/analytics/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ metrics: this.metrics })
        }).catch(console.error);
        
        this.metrics = [];
    }
}

// Initialize performance tracking
const performanceTracker = new PerformanceTracker();

// Track search time
function trackSearchTime(startTime) {
    const duration = Date.now() - startTime;
    document.dispatchEvent(new CustomEvent('searchPerformed', {
        detail: { duration }
    }));
}

// Track product click
function trackProductClick(productId, vendor, price) {
    fetch('/api/analytics/track-click', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            product_id: productId,
            vendor: vendor,
            price: price
        })
    }).catch(console.error);
}