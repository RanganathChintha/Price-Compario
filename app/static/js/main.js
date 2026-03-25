// Global variables
let currentProducts = [];
let currentBestDeal = null;
let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
let searchTimeout = null;
let currentPage = 1;
let itemsPerPage = 12;
let selectedForComparison = [];

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Get elements
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const themeToggle = document.getElementById('themeToggle');
    
    // Add event listeners
    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
        console.log('Search button attached');
    }
    
    if (searchInput) {
        searchInput.addEventListener('input', debouncedSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') performSearch();
        });
        console.log('Search input attached');
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Load theme
    loadTheme();
    
    // Show welcome message
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        resultsContainer.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-search"></i>
                <h3>Start Searching</h3>
                <p>Enter a product name above to compare prices across multiple vendors</p>
                <div class="example-searches">
                    <small>Popular searches:</small>
                    <button class="example-btn" onclick="document.getElementById('searchInput').value='iPhone'; performSearch()">iPhone</button>
                    <button class="example-btn" onclick="document.getElementById('searchInput').value='MacBook'; performSearch()">MacBook</button>
                    <button class="example-btn" onclick="document.getElementById('searchInput').value='Headphones'; performSearch()">Headphones</button>
                    <button class="example-btn" onclick="document.getElementById('searchInput').value='Smartwatch'; performSearch()">Smartwatch</button>
                </div>
            </div>
        `;
    }
});

// Perform Search
async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value.trim() : '';
    
    if (!query) {
        showNotification('Please enter a search term', 'warning');
        return;
    }
    
    showLoading();
    currentPage = 1;
    
    try {
        // Get filter values
        const minPrice = document.getElementById('minPrice') ? document.getElementById('minPrice').value : '';
        const maxPrice = document.getElementById('maxPrice') ? document.getElementById('maxPrice').value : '';
        const minRating = document.getElementById('minRating') ? document.getElementById('minRating').value : '';
        const vendor = document.getElementById('vendor') ? document.getElementById('vendor').value : '';
        
        const params = new URLSearchParams({ q: query });
        if (minPrice) params.append('min_price', minPrice);
        if (maxPrice) params.append('max_price', maxPrice);
        if (minRating) params.append('min_rating', minRating);
        if (vendor) params.append('vendor', vendor);
        
        const response = await fetch(`/api/search?${params.toString()}`);
        const result = await response.json();
        
        if (result.success) {
            currentProducts = result.data.products;
            currentBestDeal = result.data.best_deal;
            
            displayProducts(currentProducts);
            displayFilters(currentProducts, result.data.statistics);
            
            showNotification(`Found ${currentProducts.length} products`, 'success');
        } else {
            showError(result.error || 'Search failed');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to fetch products. Please try again.');
    }
}

// Show Loading
function showLoading() {
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="skeleton-grid">
            ${Array(6).fill().map(() => `
                <div class="skeleton-card">
                    <div class="skeleton-image"></div>
                    <div class="skeleton-title"></div>
                    <div class="skeleton-title" style="width: 60%"></div>
                    <div class="skeleton-price"></div>
                </div>
            `).join('')}
        </div>
    `;
}

// Display Products
function displayProducts(products) {
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) return;
    
    if (!products || products.length === 0) {
        resultsContainer.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-search"></i>
                <h3>No products found</h3>
                <p>Try searching with different keywords or adjust your filters</p>
            </div>
        `;
        return;
    }
    
    // Paginate
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const paginatedProducts = products.slice(start, end);
    
    resultsContainer.innerHTML = `
        <div class="products-grid">
            ${paginatedProducts.map(product => createProductCard(product)).join('')}
        </div>
        ${renderPagination(products.length)}
    `;
}

// Create Product Card
function createProductCard(product) {
    const isFavorite = favorites.includes(product.id);
    const isBestDeal = currentBestDeal && currentBestDeal.id === product.id;
    const fullStars = Math.floor(product.rating);
    const emptyStars = 5 - fullStars;
    const stars = '★'.repeat(fullStars) + '☆'.repeat(emptyStars);
    
    const availabilityClass = product.availability === 'In Stock' ? 'in-stock' : 'out-of-stock';
    
    return `
        <div class="product-card">
            ${isBestDeal ? '<div class="best-price-badge">🏆 Best Price</div>' : ''}
            <img src="${product.image_url || 'https://via.placeholder.com/300x200?text=Product'}" 
                 alt="${escapeHtml(product.name)}" 
                 class="product-image"
                 onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
            <div class="product-info">
                <h3 class="product-title">${escapeHtml(product.name)}</h3>
                <div class="product-price">$${product.price.toFixed(2)}</div>
                <div class="product-vendor">
                    <i class="fas fa-store"></i> ${escapeHtml(product.vendor)}
                </div>
                <div class="product-rating">
                    <span class="stars">${stars}</span>
                    <span class="rating-count">(${product.rating_count})</span>
                </div>
                <div class="availability ${availabilityClass}">
                    ${product.availability}
                </div>
                <div class="card-actions">
                    <a href="${product.buy_link}" target="_blank" class="btn btn-primary">
                        <i class="fas fa-shopping-cart"></i> Buy Now
                    </a>
                    <button class="btn btn-outline" onclick="toggleFavorite('${product.id}')">
                        <i class="fas ${isFavorite ? 'fa-heart' : 'fa-heart'}"></i>
                    </button>
                    <button class="btn btn-outline" onclick="toggleCompare('${product.id}')">
                        <i class="fas fa-chart-line"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Render Pagination
function renderPagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    if (totalPages <= 1) return '';
    
    let html = '<div class="pagination">';
    html += `<button class="pagination-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>`;
    
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
        html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }
    
    if (totalPages > 5) {
        html += `<button class="pagination-btn" disabled>...</button>`;
        html += `<button class="pagination-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
    }
    
    html += `<button class="pagination-btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>`;
    html += '</div>';
    return html;
}

// Change Page
function changePage(page) {
    currentPage = page;
    displayProducts(currentProducts);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Display Filters
function displayFilters(products, statistics) {
    const filtersContainer = document.getElementById('filtersContainer');
    if (!filtersContainer) return;
    
    const vendors = [...new Set(products.map(p => p.vendor))];
    const maxPrice = Math.max(...products.map(p => p.price), 1000);
    
    filtersContainer.innerHTML = `
        <div class="filters-container">
            <div class="filter-group">
                <div class="filter-item">
                    <label>💰 Min Price ($)</label>
                    <input type="number" id="minPrice" placeholder="Min" min="0" step="10">
                </div>
                <div class="filter-item">
                    <label>💰 Max Price ($)</label>
                    <input type="number" id="maxPrice" placeholder="Max" min="0" step="10">
                </div>
                <div class="filter-item">
                    <label>⭐ Min Rating</label>
                    <select id="minRating">
                        <option value="">Any</option>
                        <option value="3">3★ & above</option>
                        <option value="3.5">3.5★ & above</option>
                        <option value="4">4★ & above</option>
                        <option value="4.5">4.5★ & above</option>
                    </select>
                </div>
                <div class="filter-item">
                    <label>🏪 Vendor</label>
                    <select id="vendor">
                        <option value="">All Vendors</option>
                        ${vendors.map(v => `<option value="${v}">${v}</option>`).join('')}
                    </select>
                </div>
                <div class="filter-item">
                    <label>📊 Sort By</label>
                    <select id="sortBy">
                        <option value="relevance">Relevance</option>
                        <option value="price_asc">Price: Low to High</option>
                        <option value="price_desc">Price: High to Low</option>
                        <option value="rating_desc">Best Rating</option>
                    </select>
                </div>
            </div>
            <div class="filter-actions">
                <button class="btn btn-primary" onclick="applyFilters()">
                    <i class="fas fa-filter"></i> Apply Filters
                </button>
                <button class="btn btn-outline" onclick="clearFilters()">
                    <i class="fas fa-times"></i> Clear
                </button>
            </div>
            ${statistics ? `
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color); font-size: 0.875rem; color: var(--text-secondary);">
                    <i class="fas fa-chart-bar"></i> 
                    Price Range: $${statistics.price_stats.min.toFixed(2)} - $${statistics.price_stats.max.toFixed(2)} | 
                    Avg: $${statistics.price_stats.avg.toFixed(2)} | 
                    ${statistics.vendor_count} Vendors
                </div>
            ` : ''}
        </div>
    `;
}

// Apply Filters
function applyFilters() {
    let filtered = [...currentProducts];
    
    const minPrice = parseFloat(document.getElementById('minPrice')?.value);
    const maxPrice = parseFloat(document.getElementById('maxPrice')?.value);
    const minRating = parseFloat(document.getElementById('minRating')?.value);
    const vendor = document.getElementById('vendor')?.value;
    const sortBy = document.getElementById('sortBy')?.value;
    
    if (minPrice) filtered = filtered.filter(p => p.price >= minPrice);
    if (maxPrice) filtered = filtered.filter(p => p.price <= maxPrice);
    if (minRating) filtered = filtered.filter(p => p.rating >= minRating);
    if (vendor) filtered = filtered.filter(p => p.vendor === vendor);
    
    // Sort
    switch(sortBy) {
        case 'price_asc':
            filtered.sort((a, b) => a.price - b.price);
            break;
        case 'price_desc':
            filtered.sort((a, b) => b.price - a.price);
            break;
        case 'rating_desc':
            filtered.sort((a, b) => b.rating - a.rating);
            break;
    }
    
    currentProducts = filtered;
    currentPage = 1;
    displayProducts(currentProducts);
    showNotification(`Filtered to ${filtered.length} products`, 'info');
}

// Clear Filters
function clearFilters() {
    if (document.getElementById('minPrice')) document.getElementById('minPrice').value = '';
    if (document.getElementById('maxPrice')) document.getElementById('maxPrice').value = '';
    if (document.getElementById('minRating')) document.getElementById('minRating').value = '';
    if (document.getElementById('vendor')) document.getElementById('vendor').value = '';
    if (document.getElementById('sortBy')) document.getElementById('sortBy').value = 'relevance';
    
    performSearch();
}

// Debounced Search
function debouncedSearch() {
    clearTimeout(searchTimeout);
    const query = document.getElementById('searchInput')?.value.trim();
    if (query && query.length >= 2) {
        searchTimeout = setTimeout(() => {
            getSuggestions(query);
        }, 300);
    } else {
        const suggestionsContainer = document.getElementById('suggestionsContainer');
        if (suggestionsContainer) suggestionsContainer.style.display = 'none';
    }
}

// Get Suggestions
async function getSuggestions(query) {
    try {
        const response = await fetch(`/api/suggestions?q=${encodeURIComponent(query)}`);
        const result = await response.json();
        if (result.success && result.data.suggestions) {
            showSuggestions(result.data.suggestions);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Show Suggestions
function showSuggestions(suggestions) {
    const container = document.getElementById('suggestionsContainer');
    if (!container) return;
    
    if (suggestions.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.innerHTML = suggestions.map(s => `
        <div class="suggestion-item" onclick="selectSuggestion('${s.replace(/'/g, "\\'")}')">
            <i class="fas fa-search"></i> ${escapeHtml(s)}
        </div>
    `).join('');
    container.style.display = 'block';
}

// Select Suggestion
function selectSuggestion(suggestion) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = suggestion;
        const container = document.getElementById('suggestionsContainer');
        if (container) container.style.display = 'none';
        performSearch();
    }
}

// Toggle Favorite
function toggleFavorite(productId) {
    const index = favorites.indexOf(productId);
    if (index === -1) {
        favorites.push(productId);
        showNotification('Added to favorites ❤️', 'success');
    } else {
        favorites.splice(index, 1);
        showNotification('Removed from favorites 💔', 'info');
    }
    localStorage.setItem('favorites', JSON.stringify(favorites));
    displayProducts(currentProducts);
}

// Toggle Compare
function toggleCompare(productId) {
    const index = selectedForComparison.indexOf(productId);
    if (index === -1) {
        if (selectedForComparison.length >= 4) {
            showNotification('Maximum 4 products can be compared', 'warning');
            return;
        }
        selectedForComparison.push(productId);
        showNotification('Added to comparison', 'success');
    } else {
        selectedForComparison.splice(index, 1);
        showNotification('Removed from comparison', 'info');
    }
    
    const compareBtn = document.getElementById('compareBtn');
    if (compareBtn) {
        if (selectedForComparison.length > 0) {
            compareBtn.style.display = 'flex';
            compareBtn.innerHTML = `<i class="fas fa-chart-line"></i> Compare (${selectedForComparison.length})`;
        } else {
            compareBtn.style.display = 'none';
        }
    }
}

// Show Comparison
async function showComparison() {
    if (selectedForComparison.length === 0) {
        showNotification('Select products to compare first', 'warning');
        return;
    }
    
    const productsToCompare = currentProducts.filter(p => selectedForComparison.includes(p.id));
    
    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_ids: selectedForComparison,
                products: productsToCompare
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayComparisonModal(result.data);
        } else {
            showNotification('Failed to load comparison', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error loading comparison', 'error');
    }
}

// Display Comparison Modal
function displayComparisonModal(data) {
    const modal = document.getElementById('compareModal');
    const content = document.getElementById('comparisonContent');
    if (!modal || !content) return;
    
    const products = data.products;
    const rows = data.comparison_table.rows;
    
    content.innerHTML = `
        <h3>Product Comparison</h3>
        ${data.highlights ? `
            <div style="background: var(--light-bg); padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
                <strong>🏆 Highlights:</strong><br>
                Best Price: ${data.highlights.best_price.vendor} ($${data.highlights.best_price.price})<br>
                Best Rating: ${data.highlights.best_rating.vendor} (${data.highlights.best_rating.rating}★)
            </div>
        ` : ''}
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Feature</th>
                    ${products.map(p => `<th>${p.vendor}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${rows.map(row => `
                    <tr>
                        <td><strong>${row.feature}</strong></td>
                        ${products.map(p => `<td>${row[p.vendor] || '-'}</td>`).join('')}
                    </tr>
                `).join('')}
                <tr>
                    <td><strong>Action</strong></td>
                    ${products.map(p => `
                        <td><a href="${p.buy_link}" target="_blank" class="btn btn-primary" style="font-size:0.75rem">Buy Now</a></td>
                    `).join('')}
                </tr>
            </tbody>
        </table>
        <div style="margin-top:1rem; text-align:right">
            <button class="btn btn-outline" onclick="closeModal()">Close</button>
        </div>
    `;
    
    modal.classList.add('active');
}

// Close Modal
function closeModal() {
    const modal = document.getElementById('compareModal');
    if (modal) modal.classList.remove('active');
}

// Toggle Theme
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = document.querySelector('#themeToggle i');
    if (icon) {
        icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Load Theme
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const icon = document.querySelector('#themeToggle i');
    if (icon) {
        icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Show Notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = 'notification';
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    notification.innerHTML = `${icons[type]} ${message}`;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Show Error
function showError(message) {
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        resultsContainer.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-exclamation-triangle" style="color: var(--danger-color);"></i>
                <h3>Error</h3>
                <p>${message}</p>
                <button onclick="location.reload()" class="btn btn-primary" style="margin-top:1rem">Try Again</button>
            </div>
        `;
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions global
window.performSearch = performSearch;
window.applyFilters = applyFilters;
window.clearFilters = clearFilters;
window.toggleFavorite = toggleFavorite;
window.toggleCompare = toggleCompare;
window.showComparison = showComparison;
window.closeModal = closeModal;
window.changePage = changePage;
window.selectSuggestion = selectSuggestion;