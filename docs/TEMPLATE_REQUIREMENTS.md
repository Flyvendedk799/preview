# Template Requirements for White-Label Site Hosting

This document specifies the requirements for templates used in the white-label blog/news site hosting system.

## Template Structure

### Required Pages

Each template must provide the following page templates:

1. **Home** (`home.html` or `index.html`)
   - Blog post listing page
   - Should display featured posts prominently
   - Pagination support

2. **Single Post** (`post.html`)
   - Individual blog post view
   - Post content, featured image, author info
   - Related posts section
   - Social sharing buttons

3. **Category Archive** (`category.html`)
   - Category listing page
   - Shows all posts in a category
   - Category description and metadata

4. **Static Page** (`page.html`)
   - Generic page template for About, Contact, etc.
   - Custom content support

5. **404 Error** (`404.html`)
   - Custom 404 page

### Folder Structure

```
template-name/
├── templates/
│   ├── home.html
│   ├── post.html
│   ├── category.html
│   ├── page.html
│   └── 404.html
├── assets/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
│       └── logo.png
├── config.json
└── README.md
```

### Template Configuration (`config.json`)

```json
{
  "name": "Template Name",
  "version": "1.0.0",
  "description": "Template description",
  "author": "Author Name",
  "preview_image": "preview.jpg",
  "features": [
    "responsive",
    "dark-mode",
    "custom-fonts"
  ],
  "required_variables": [
    "site.name",
    "site.branding.primary_color"
  ]
}
```

## Template Variables

Templates receive the following variables in their context:

### Site Variables

- `site.name` - Site name/title
- `site.meta_title` - SEO title
- `site.meta_description` - SEO description
- `site.meta_keywords` - SEO keywords
- `site.domain.name` - Domain name

### Branding Variables

- `site.branding.logo_url` - Logo image URL
- `site.branding.logo_alt` - Logo alt text
- `site.branding.favicon_url` - Favicon URL
- `site.branding.primary_color` - Primary color (hex)
- `site.branding.secondary_color` - Secondary color (hex)
- `site.branding.accent_color` - Accent color (hex)
- `site.branding.background_color` - Background color (hex)
- `site.branding.text_color` - Text color (hex)
- `site.branding.font_family` - Font family
- `site.branding.heading_font` - Heading font
- `site.branding.body_font` - Body font
- `site.branding.custom_css` - Custom CSS (if any)

### Navigation Variables

- `site.menus.header` - Header menu items (array)
- `site.menus.footer` - Footer menu items (array)
- `site.menus.sidebar` - Sidebar menu items (array)

Each menu item contains:
- `label` - Menu item label
- `url` - Menu item URL
- `type` - Item type (link, post, page, category)
- `children` - Submenu items (array)

### Post Variables (for post.html)

- `post.title` - Post title
- `post.slug` - Post slug
- `post.content` - Post content (Markdown rendered to HTML)
- `post.excerpt` - Post excerpt
- `post.featured_image` - Featured image URL
- `post.featured_image_alt` - Featured image alt text
- `post.author_name` - Author name
- `post.author_bio` - Author bio
- `post.author_avatar` - Author avatar URL
- `post.category` - Category object (if assigned)
- `post.tags` - Tags (comma-separated string)
- `post.published_at` - Publication date
- `post.read_time_minutes` - Estimated reading time
- `post.views_count` - View count
- `post.meta_title` - SEO title
- `post.meta_description` - SEO description

### Category Variables (for category.html)

- `category.name` - Category name
- `category.slug` - Category slug
- `category.description` - Category description
- `category.color` - Category color (hex)
- `posts` - Array of posts in category

### Page Variables (for page.html)

- `page.title` - Page title
- `page.slug` - Page slug
- `page.content` - Page content (Markdown rendered to HTML)
- `page.meta_title` - SEO title
- `page.meta_description` - SEO description

### Settings Variables

- `site.settings.language` - Site language code
- `site.settings.contact_email` - Contact email
- `site.settings.social_links` - Social media links (object)
- `site.settings.google_analytics_id` - Google Analytics ID
- `site.settings.header_code` - Custom header code (HTML)
- `site.settings.footer_code` - Custom footer code (HTML)

## Component System

### Header Component

Templates should include a header component that:
- Displays site logo or name
- Renders navigation menu
- Is responsive
- Supports sticky header (optional)

### Footer Component

Templates should include a footer component that:
- Displays footer navigation
- Shows copyright information
- Includes social media links
- Is responsive

### Post Card Component

For listing pages, templates should provide a post card component that displays:
- Post featured image (if available)
- Post title
- Post excerpt
- Post metadata (date, author, category)
- Read time
- Link to full post

### Pagination Component

Templates should include pagination for:
- Post listings
- Category archives

Pagination variables:
- `pagination.page` - Current page number
- `pagination.total_pages` - Total number of pages
- `pagination.has_next` - Whether next page exists
- `pagination.has_prev` - Whether previous page exists

### Category Badge Component

Templates should provide a category badge component that:
- Displays category name
- Uses category color for styling
- Links to category archive page

### Social Sharing Component

Templates should include social sharing buttons for:
- Twitter
- Facebook
- LinkedIn
- Copy link

## Theming Capabilities

### CSS Variable Injection

Templates should use CSS variables for theming:

```css
:root {
  --primary-color: #f97316;
  --secondary-color: #64748b;
  --accent-color: #f59e0b;
  --background-color: #ffffff;
  --text-color: #1f2937;
  --font-family: 'Inter', sans-serif;
  --heading-font: 'Inter', sans-serif;
  --body-font: 'Inter', sans-serif;
}
```

These variables will be automatically injected based on site branding settings.

### Font Loading

Templates can specify fonts in `config.json`:

```json
{
  "fonts": [
    {
      "name": "Inter",
      "weights": [400, 500, 600, 700],
      "source": "google"
    }
  ]
}
```

Supported sources:
- `google` - Google Fonts
- `custom` - Custom font files (uploaded via media library)

### Color Scheme Support

Templates should support:
- Light mode (default)
- Dark mode (optional, via CSS media query or toggle)

Dark mode can be activated via:
- CSS: `@media (prefers-color-scheme: dark)`
- JavaScript toggle (stored in localStorage)

## Template Rendering

### Template Engine

Templates use Jinja2-style syntax:

```html
<h1>{{ site.name }}</h1>
<p>{{ site.meta_description }}</p>

{% for post in posts %}
  <article>
    <h2><a href="/posts/{{ post.slug }}">{{ post.title }}</a></h2>
    <p>{{ post.excerpt }}</p>
  </article>
{% endfor %}
```

### Available Filters

- `markdown` - Convert Markdown to HTML
- `date` - Format dates
- `truncate` - Truncate text
- `url` - Generate URLs
- `asset` - Reference template assets

### Template Helpers

- `url_for('post', slug='...')` - Generate post URL
- `url_for('category', slug='...')` - Generate category URL
- `url_for('page', slug='...')` - Generate page URL
- `asset('css/style.css')` - Reference asset file

## SEO Requirements

Templates must include:

1. **Meta Tags**
   - `<title>` tag (from `site.meta_title` or `post.meta_title`)
   - `<meta name="description">` (from `site.meta_description` or `post.meta_description`)
   - `<meta name="keywords">` (if provided)
   - Open Graph tags (for social sharing)
   - Twitter Card tags

2. **Structured Data**
   - JSON-LD schema for articles
   - Breadcrumb schema
   - Organization schema

3. **Canonical URLs**
   - `<link rel="canonical">` tag

4. **Robots Meta**
   - Respect `no_index` flag from posts/pages

## Performance Requirements

Templates should:

1. **Optimize Images**
   - Use responsive images (`srcset`)
   - Lazy loading for below-fold images
   - WebP format support

2. **Minimize CSS/JS**
   - Minify CSS and JavaScript
   - Use critical CSS inlining
   - Defer non-critical JavaScript

3. **Caching**
   - Set appropriate cache headers
   - Use CDN for static assets

## Accessibility Requirements

Templates must:

1. **Semantic HTML**
   - Use proper heading hierarchy (h1-h6)
   - Use semantic elements (`<article>`, `<nav>`, `<header>`, `<footer>`)
   - Proper form labels

2. **ARIA Labels**
   - Navigation landmarks
   - Button labels
   - Form field descriptions

3. **Keyboard Navigation**
   - All interactive elements keyboard accessible
   - Skip links for main content
   - Focus indicators

4. **Color Contrast**
   - WCAG AA compliance (4.5:1 for text)
   - Don't rely solely on color for information

## Browser Support

Templates should support:
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Template Validation

Before a template can be used, it must:

1. Pass HTML validation (W3C Validator)
2. Pass accessibility audit (WCAG 2.1 AA)
3. Pass performance audit (Lighthouse score > 90)
4. Work on mobile devices (responsive)
5. Include all required templates
6. Have valid `config.json`

## Future Template Features

Planned features for future templates:

1. **Multi-language Support**
   - RTL language support
   - Language switcher component

2. **E-commerce Integration**
   - Product listing templates
   - Shopping cart components

3. **Advanced Components**
   - Newsletter signup forms
   - Comment systems
   - Search functionality
   - Related posts algorithm

4. **Customization Options**
   - Layout variations
   - Color presets
   - Typography options
   - Widget system

