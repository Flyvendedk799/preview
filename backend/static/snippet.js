(function() {
  'use strict';
  
  // Get current page URL
  const fullUrl = window.location.href;
  
  // Build API URL - assumes snippet.js is served from the same origin as the API
  // For production, this would be the actual API domain
  const apiUrl = '/api/v1/public/preview?full_url=' + encodeURIComponent(fullUrl);
  
  // Fetch preview data
  fetch(apiUrl, { credentials: 'omit' })
    .then(function(res) {
      if (!res.ok) {
        throw new Error('Failed to fetch preview');
      }
      return res.json();
    })
    .then(function(data) {
      if (!data || !data.title) {
        return;
      }
      
      // Helper function to set meta tags
      function setMeta(property, content, isName) {
        if (!content) return;
        
        var selector = isName
          ? 'meta[name="' + property + '"]'
          : 'meta[property="' + property + '"]';
        
        var el = document.querySelector(selector);
        
        if (!el) {
          el = document.createElement('meta');
          if (isName) {
            el.setAttribute('name', property);
          } else {
            el.setAttribute('property', property);
          }
          document.head.appendChild(el);
        }
        
        el.setAttribute('content', content);
      }
      
      // Set Open Graph tags
      setMeta('og:url', data.url || fullUrl, false);
      setMeta('og:title', data.title, false);
      setMeta('og:description', data.description || '', false);
      if (data.image_url) {
        setMeta('og:image', data.image_url, false);
      }
      if (data.site_name) {
        setMeta('og:site_name', data.site_name, false);
      }
      
      // Set Twitter Card tags
      setMeta('twitter:card', 'summary_large_image', true);
      setMeta('twitter:title', data.title, true);
      setMeta('twitter:description', data.description || '', true);
      if (data.image_url) {
        setMeta('twitter:image', data.image_url, true);
      }
    })
    .catch(function(err) {
      // Fail silently in production, but log in development
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.warn('[Preview SaaS] Failed to fetch preview:', err);
      }
    });
})();

