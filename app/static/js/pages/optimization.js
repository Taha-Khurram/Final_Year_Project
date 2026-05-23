(function() {
    // Tab switching
    var tabs = document.querySelectorAll('.opt-tab');
    var tabContents = document.querySelectorAll('.opt-tab-content');

    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            tabs.forEach(function(t) { t.classList.remove('active'); });
            tabContents.forEach(function(c) { c.classList.remove('active'); });
            tab.classList.add('active');
            var target = tab.getAttribute('data-tab');
            if (target === 'url-metrics') {
                document.getElementById('tabUrlMetrics').classList.add('active');
            } else if (target === 'keyword-research') {
                document.getElementById('tabKeywordResearch').classList.add('active');
            } else if (target === 'site-audit') {
                document.getElementById('tabSiteAudit').classList.add('active');
            }
        });
    });

    // ========== URL METRICS ==========
    var urlInput = document.getElementById('urlInput');
    var urlResultsSection = document.getElementById('urlResultsSection');
    var urlEmptyState = document.getElementById('urlEmptyState');
    var urlMetricsGrid = document.getElementById('urlMetricsGrid');
    var urlDetailsGrid = document.getElementById('urlDetailsGrid');
    var analyzedUrlText = document.getElementById('analyzedUrlText');
    var analyzeUrlBtn = document.getElementById('analyzeUrlBtn');

    urlInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') analyzeUrl();
    });

    window.analyzeUrl = async function() {
        var url = urlInput.value.trim();
        if (!url) {
            showToast({ type: 'warning', title: 'Missing URL', message: 'Please enter a URL to analyze.' });
            urlInput.focus();
            return;
        }

        analyzeUrlBtn.disabled = true;
        analyzeUrlBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analyzing...';
        urlEmptyState.style.display = 'none';
        urlResultsSection.classList.remove('show');

        try {
            var response = await fetch('/api/optimization/url-metrics?url=' + encodeURIComponent(url));
            var result = await response.json();

            if (!response.ok || !result.success) {
                showToast({ type: 'error', title: 'Analysis Failed', message: result.error || 'Unable to fetch metrics.' });
                urlEmptyState.style.display = 'block';
                return;
            }

            renderUrlResults(url, result.data);

        } catch (err) {
            showToast({ type: 'error', title: 'Connection Error', message: 'Failed to connect. Please try again.' });
            urlEmptyState.style.display = 'block';
        } finally {
            analyzeUrlBtn.disabled = false;
            analyzeUrlBtn.innerHTML = '<i class="bi bi-search"></i> Analyze';
        }
    };

    var urlMetricDefs = [
        { key: 'domainRating', altKeys: ['domain_rating', 'dr'], label: 'Domain Rating', icon: 'bi-award-fill', color: 'purple' },
        { key: 'backlinks', altKeys: ['total_backlinks', 'backlink'], label: 'Backlinks', icon: 'bi-link-45deg', color: 'green' },
        { key: 'refDomains', altKeys: ['referring_domains', 'ref_domains'], label: 'Referring Domains', icon: 'bi-diagram-3-fill', color: 'blue' },
        { key: 'traffic', altKeys: ['organic_traffic', 'org_traffic'], label: 'Organic Traffic', icon: 'bi-graph-up-arrow', color: 'orange' },
        { key: 'organicKeywords', altKeys: ['organic_keywords', 'keywords'], label: 'Organic Keywords', icon: 'bi-key-fill', color: 'pink' },
        { key: 'urlRating', altKeys: ['url_rating', 'ur'], label: 'URL Rating', icon: 'bi-shield-check', color: 'teal' }
    ];

    function formatNumber(num) {
        if (num === null || num === undefined || num === '') return 'N/A';
        num = Number(num);
        if (isNaN(num)) return 'N/A';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toLocaleString();
    }

    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getMetricValue(data, def) {
        var val = data[def.key];
        if (val !== undefined && val !== null) return val;
        for (var i = 0; i < def.altKeys.length; i++) {
            val = data[def.altKeys[i]];
            if (val !== undefined && val !== null) return val;
        }
        return null;
    }

    function renderUrlResults(url, data) {
        analyzedUrlText.textContent = url;

        var metricsHtml = '';
        urlMetricDefs.forEach(function(def) {
            var val = getMetricValue(data, def);
            metricsHtml += '<div class="metric-card">' +
                '<div class="metric-icon ' + def.color + '"><i class="bi ' + def.icon + '"></i></div>' +
                '<div class="metric-info">' +
                    '<div class="metric-label">' + def.label + '</div>' +
                    '<div class="metric-value">' + formatNumber(val) + '</div>' +
                '</div></div>';
        });
        urlMetricsGrid.innerHTML = metricsHtml;

        var detailsHtml = '';
        var skipKeys = {};
        urlMetricDefs.forEach(function(def) {
            skipKeys[def.key] = true;
            def.altKeys.forEach(function(k) { skipKeys[k] = true; });
        });

        Object.keys(data).forEach(function(key) {
            if (skipKeys[key]) return;
            var val = data[key];
            if (val === null || val === undefined || val === '') return;
            if (typeof val === 'object') return;
            var label = key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, function(s) { return s.toUpperCase(); });
            detailsHtml += '<div class="detail-row">' +
                '<span class="detail-label">' + escapeHtml(label) + '</span>' +
                '<span class="detail-value">' + escapeHtml(String(val)) + '</span>' +
                '</div>';
        });

        if (detailsHtml) {
            urlDetailsGrid.innerHTML = detailsHtml;
            document.getElementById('urlDetailsCard').style.display = 'block';
        } else {
            document.getElementById('urlDetailsCard').style.display = 'none';
        }

        urlResultsSection.classList.add('show');
    }

    // ========== KEYWORD RESEARCH ==========
    var draftSelect = document.getElementById('draftSelect');
    var countrySelect = document.getElementById('countrySelect');
    var kwResultsSection = document.getElementById('kwResultsSection');
    var kwEmptyState = document.getElementById('kwEmptyState');
    var kwResultsBody = document.getElementById('kwResultsBody');
    var analyzedKeywordText = document.getElementById('analyzedKeywordText');
    var analyzeKeywordBtn = document.getElementById('analyzeKeywordBtn');
    var draftsLoaded = false;

    function loadDrafts() {
        if (draftsLoaded) return;
        fetch('/api/seo/drafts')
            .then(function(r) { return r.json(); })
            .then(function(result) {
                if (result.success && result.drafts) {
                    draftSelect.innerHTML = '<option value="">-- Select a draft --</option>';
                    result.drafts.forEach(function(d) {
                        var opt = document.createElement('option');
                        opt.value = d.id;
                        opt.textContent = d.title || 'Untitled';
                        draftSelect.appendChild(opt);
                    });
                    draftsLoaded = true;
                }
            })
            .catch(function() {});
    }

    // Load drafts when keyword tab is clicked
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            if (tab.getAttribute('data-tab') === 'keyword-research') {
                loadDrafts();
            }
        });
    });

    window.analyzeKeyword = async function() {
        var blogId = draftSelect.value;
        if (!blogId) {
            showToast({ type: 'warning', title: 'No Draft Selected', message: 'Please select a draft blog to analyze.' });
            draftSelect.focus();
            return;
        }

        var country = countrySelect.value;
        analyzeKeywordBtn.disabled = true;
        analyzeKeywordBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analyzing...';
        kwEmptyState.style.display = 'none';
        kwResultsSection.classList.remove('show');

        try {
            var response = await fetch('/api/optimization/draft-keywords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ blog_id: blogId, country: country })
            });
            var result = await response.json();

            if (!response.ok || !result.success) {
                showToast({ type: 'error', title: 'Research Failed', message: result.error || 'Unable to analyze draft.' });
                kwEmptyState.style.display = 'block';
                return;
            }

            renderKeywordResults(result.data);

        } catch (err) {
            showToast({ type: 'error', title: 'Connection Error', message: 'Failed to connect. Please try again.' });
            kwEmptyState.style.display = 'block';
        } finally {
            analyzeKeywordBtn.disabled = false;
            analyzeKeywordBtn.innerHTML = '<i class="bi bi-search"></i> Research';
        }
    };

    function formatKwNum(num) {
        if (num === null || num === undefined) return '-';
        num = Number(num);
        if (isNaN(num)) return '-';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toLocaleString();
    }

    function getDifficultyClass(val) {
        if (val === null || val === undefined) return '';
        val = Number(val);
        if (val >= 70) return 'difficulty-hard';
        if (val >= 40) return 'difficulty-medium';
        return 'difficulty-easy';
    }

    function renderKeywordResults(data) {
        analyzedKeywordText.textContent = data.blog_title || 'Draft Analysis';

        var html = '';
        data.keywords.forEach(function(kw) {
            if (kw.error) {
                html += '<tr class="kw-row-error"><td>' + escapeHtml(kw.keyword) + '</td><td colspan="5">Failed to fetch metrics</td></tr>';
                return;
            }
            var diff = kw.difficulty;
            var diffClass = getDifficultyClass(diff);
            html += '<tr>' +
                '<td class="kw-cell-keyword">' + escapeHtml(kw.keyword || '') + '</td>' +
                '<td>' + formatKwNum(kw.searchVolume) + '</td>' +
                '<td><span class="difficulty-badge ' + diffClass + '">' + (diff !== null && diff !== undefined ? diff + '/100' : '-') + '</span></td>' +
                '<td>' + (kw.cpc !== null && kw.cpc !== undefined ? '$' + Number(kw.cpc).toFixed(2) : '-') + '</td>' +
                '<td>' + formatKwNum(kw.clicks) + '</td>' +
                '<td>' + formatKwNum(kw.trafficPotential) + '</td>' +
                '</tr>';
        });
        kwResultsBody.innerHTML = html;
        kwResultsSection.classList.add('show');
    }

    // ========== SITE AUDIT ==========
    var auditDomainInput = document.getElementById('auditDomainInput');
    var auditResultsSection = document.getElementById('auditResultsSection');
    var auditEmptyState = document.getElementById('auditEmptyState');
    var auditResultsHead = document.getElementById('auditResultsHead');
    var auditResultsBody = document.getElementById('auditResultsBody');
    var auditedDomainText = document.getElementById('auditedDomainText');
    var auditBtn = document.getElementById('auditBtn');
    var auditDetailsCard = document.getElementById('auditDetailsCard');
    var auditDetailsGrid = document.getElementById('auditDetailsGrid');

    auditDomainInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') runSiteAudit();
    });

    window.runSiteAudit = async function() {
        var domain = auditDomainInput.value.trim();
        if (!domain) {
            showToast({ type: 'warning', title: 'Missing Domain', message: 'Please enter a domain to audit.' });
            auditDomainInput.focus();
            return;
        }

        auditBtn.disabled = true;
        auditBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Auditing...';
        auditEmptyState.style.display = 'none';
        auditResultsSection.classList.remove('show');

        try {
            var response = await fetch('/api/optimization/site-audit?domain=' + encodeURIComponent(domain));
            var result = await response.json();

            if (!response.ok || !result.success) {
                showToast({ type: 'error', title: 'Audit Failed', message: result.error || 'Unable to audit this domain.' });
                auditEmptyState.style.display = 'block';
                return;
            }

            renderAuditResults(domain, result.data);

        } catch (err) {
            showToast({ type: 'error', title: 'Connection Error', message: 'Failed to connect. Please try again.' });
            auditEmptyState.style.display = 'block';
        } finally {
            auditBtn.disabled = false;
            auditBtn.innerHTML = '<i class="bi bi-shield-check"></i> Audit';
        }
    };

    function renderAuditResults(domain, data) {
        auditedDomainText.textContent = domain;

        // Handle array of keywords (expected response format)
        if (Array.isArray(data)) {
            renderAuditTable(data);
            auditDetailsCard.style.display = 'none';
            auditResultsSection.classList.add('show');
            return;
        }

        // Handle object with nested array (e.g., { keywords: [...], ... })
        if (typeof data === 'object' && data !== null) {
            var arrayKey = null;
            var extraFields = {};
            Object.keys(data).forEach(function(key) {
                if (Array.isArray(data[key]) && data[key].length > 0 && typeof data[key][0] === 'object') {
                    arrayKey = key;
                } else if (typeof data[key] !== 'object') {
                    extraFields[key] = data[key];
                }
            });

            if (arrayKey) {
                renderAuditTable(data[arrayKey]);
            } else {
                // No array found — display all fields as detail rows
                auditResultsHead.innerHTML = '';
                auditResultsBody.innerHTML = '';
                renderAuditDetails(data);
                auditResultsSection.classList.add('show');
                return;
            }

            // Show extra top-level fields
            if (Object.keys(extraFields).length > 0) {
                renderAuditDetails(extraFields);
                auditDetailsCard.style.display = 'block';
            } else {
                auditDetailsCard.style.display = 'none';
            }

            auditResultsSection.classList.add('show');
            return;
        }

        // Fallback: unexpected format
        showToast({ type: 'warning', title: 'Unexpected Data', message: 'The API returned an unexpected format.' });
        auditEmptyState.style.display = 'block';
    }

    function renderAuditTable(rows) {
        if (!rows || rows.length === 0) {
            auditResultsHead.innerHTML = '';
            auditResultsBody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#94a3b8;">No keywords found for this domain.</td></tr>';
            return;
        }

        // Build table headers from first row keys
        var keys = Object.keys(rows[0]);
        var headHtml = '<tr>';
        keys.forEach(function(key) {
            var label = key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, function(s) { return s.toUpperCase(); });
            headHtml += '<th>' + escapeHtml(label) + '</th>';
        });
        headHtml += '</tr>';
        auditResultsHead.innerHTML = headHtml;

        // Build table body
        var bodyHtml = '';
        rows.forEach(function(row) {
            bodyHtml += '<tr>';
            keys.forEach(function(key, idx) {
                var val = row[key];
                if (val === null || val === undefined) val = '-';
                var cellClass = idx === 0 ? ' class="kw-cell-keyword"' : '';
                bodyHtml += '<td' + cellClass + '>' + escapeHtml(String(val)) + '</td>';
            });
            bodyHtml += '</tr>';
        });
        auditResultsBody.innerHTML = bodyHtml;
    }

    function renderAuditDetails(obj) {
        var html = '';
        Object.keys(obj).forEach(function(key) {
            var val = obj[key];
            if (val === null || val === undefined || val === '') return;
            if (typeof val === 'object') return;
            var label = key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, function(s) { return s.toUpperCase(); });
            html += '<div class="detail-row">' +
                '<span class="detail-label">' + escapeHtml(label) + '</span>' +
                '<span class="detail-value">' + escapeHtml(String(val)) + '</span>' +
                '</div>';
        });
        auditDetailsGrid.innerHTML = html;
        if (html) {
            auditDetailsCard.style.display = 'block';
        }
    }
})();
