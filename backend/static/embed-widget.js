/**
 * MyMetaView 4.0 — Embeddable Preview Widget
 *
 * Usage:
 *   <script src="https://mymetaview.com/static/embed-widget.js"
 *           data-preview-url="https://cdn.../preview.png"
 *           data-page-url="https://example.com/page"
 *           data-title="Page Title"
 *           data-width="1200"
 *           data-height="630"></script>
 *
 * Or with URL to fetch preview (requires CORS):
 *   <script src="https://mymetaview.com/static/embed-widget.js"
 *           data-url="https://example.com/page"></script>
 *
 * The script creates a container div with class "mymetaview-preview-widget" and
 * inserts the preview image. Add your own CSS to style the container.
 */
(function() {
  'use strict';

  var API_BASE = 'https://mymetaview.com/api/v1';
  var script = document.currentScript;
  if (!script) return;

  var previewUrl = script.getAttribute('data-preview-url');
  var pageUrl = script.getAttribute('data-page-url') || script.getAttribute('data-url');
  var title = script.getAttribute('data-title') || 'Preview';
  var width = script.getAttribute('data-width') || '1200';
  var height = script.getAttribute('data-height') || '630';
  var containerId = script.getAttribute('data-container-id') || 'mymetaview-preview-container';

  function createWidget(imgSrc, linkHref, altText) {
    var container = document.getElementById(containerId);
    if (!container) {
      container = document.createElement('div');
      container.id = containerId;
      container.className = 'mymetaview-preview-widget';
      script.parentNode.insertBefore(container, script);
    }

    var link = document.createElement('a');
    link.href = linkHref || '#';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.style.display = 'block';
    link.style.maxWidth = '100%';

    var img = document.createElement('img');
    img.src = imgSrc;
    img.alt = altText || title;
    img.loading = 'lazy';
    img.style.maxWidth = '100%';
    img.style.height = 'auto';
    img.style.display = 'block';
    img.style.borderRadius = '4px';
    img.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';

    link.appendChild(img);
    container.appendChild(link);
  }

  if (previewUrl) {
    createWidget(previewUrl, pageUrl || '#', title);
    return;
  }

  if (pageUrl) {
    var apiUrl = API_BASE + '/public/preview?full_url=' + encodeURIComponent(pageUrl);
    fetch(apiUrl, { credentials: 'omit', mode: 'cors' })
      .then(function(res) { return res.ok ? res.json() : Promise.reject(res); })
      .then(function(data) {
        var imgUrl = data.image_url || data.composited_preview_image_url || data.screenshot_url;
        if (imgUrl) {
          createWidget(imgUrl, data.url || pageUrl, data.title || title);
        }
      })
      .catch(function() {
        if (console && console.warn) {
          console.warn('MyMetaView: Could not fetch preview for ' + pageUrl);
        }
      });
  }
})();
