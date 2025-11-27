(function() {
  'use strict';
  
  // Production API domain - hardcoded for reliability
  var API_DOMAIN = 'https://mymetaview.com';
  
  // Track if we've already injected tags to ensure idempotency
  var INJECTED_KEY = 'mymetaview_preview_injected';
  if (document[INJECTED_KEY]) {
    return; // Already injected, skip
  }
  document[INJECTED_KEY] = true;
  
  // Get current page URL deterministically
  var fullUrl = window.location.href;
  
  // Build API URL with production domain (deterministic per URL)
  var apiUrl = API_DOMAIN + '/api/v1/public/preview?full_url=' + encodeURIComponent(fullUrl);
  
  // Helper function to check if meta tag already exists and has content
  function hasExistingMeta(property, isName) {
    var selector = isName
      ? 'meta[name="' + property + '"]'
      : 'meta[property="' + property + '"]';
    var el = document.querySelector(selector);
    return el && el.getAttribute('content') && el.getAttribute('content').trim() !== '';
  }
  
  // Helper function to set meta tags (only if not already present)
  // This preserves existing OG tags and only augments missing ones
  function setMetaIfMissing(property, content, isName) {
    if (!content) return false;
    
    // Don't override existing tags - preserve what's already there
    if (hasExistingMeta(property, isName)) {
      return false; // Tag already exists, skip
    }
    
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
      // Inject early in head for crawler visibility
      var head = document.head || document.getElementsByTagName('head')[0];
      if (head.firstChild) {
        head.insertBefore(el, head.firstChild);
      } else {
        head.appendChild(el);
      }
    }
    
    el.setAttribute('content', content);
    return true;
  }
  
  // Inject meta tags as early as possible (before DOMContentLoaded)
  // This reduces mismatch between render-time and crawl-time
  function injectMetaTags(data) {
    if (!data || !data.title) {
      return;
    }
    
    // Only augment missing tags - never override existing ones
    setMetaIfMissing('og:url', data.url || fullUrl, false);
    setMetaIfMissing('og:title', data.title, false);
    setMetaIfMissing('og:description', data.description || '', false);
    if (data.image_url) {
      setMetaIfMissing('og:image', data.image_url, false);
    }
    if (data.site_name) {
      setMetaIfMissing('og:site_name', data.site_name, false);
    }
    
    // Set Twitter Card tags (only if missing)
    setMetaIfMissing('twitter:card', 'summary_large_image', true);
    setMetaIfMissing('twitter:title', data.title, true);
    setMetaIfMissing('twitter:description', data.description || '', true);
    if (data.image_url) {
      setMetaIfMissing('twitter:image', data.image_url, true);
    }
  }
  
  // Try to inject immediately if DOM is ready, otherwise wait
  function attemptInjection() {
    if (document.head) {
      // DOM is ready, fetch and inject
      fetch(apiUrl, { 
        method: 'GET',
        credentials: 'omit',
        mode: 'cors',
        cache: 'default' // Use browser cache for deterministic results
      })
        .then(function(res) {
          if (!res.ok) {
            throw new Error('Failed to fetch preview: ' + res.status);
          }
          return res.json();
        })
        .then(function(data) {
          injectMetaTags(data);
        })
        .catch(function(err) {
          // Fail silently - do not log errors in production
          // This ensures the script never breaks the host page
        });
    } else {
      // DOM not ready yet, wait a bit and try again
      setTimeout(attemptInjection, 10);
    }
  }
  
  // Start injection attempt immediately (non-blocking)
  if (document.readyState === 'loading') {
    // DOM is still loading, inject as soon as head is available
    attemptInjection();
  } else {
    // DOM already loaded, inject immediately
    attemptInjection();
  }
})();

