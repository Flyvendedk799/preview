(function() {
  'use strict';
  
  // Production API domain - hardcoded for reliability
  var API_DOMAIN = 'https://mymetaview.com';
  
  // Get current page URL
  var fullUrl = window.location.href;
  
  // Build API URL with production domain
  var apiUrl = API_DOMAIN + '/api/v1/public/preview?full_url=' + encodeURIComponent(fullUrl);
  
  // Fetch preview data asynchronously (non-blocking)
  // Use setTimeout to ensure this doesn't block page rendering
  setTimeout(function() {
    fetch(apiUrl, { 
      method: 'GET',
      credentials: 'omit',
      mode: 'cors',
      cache: 'default'
    })
      .then(function(res) {
        if (!res.ok) {
          throw new Error('Failed to fetch preview: ' + res.status);
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
        // Fail silently - do not log errors in production
        // This ensures the script never breaks the host page
      });
  }, 0);
})();

