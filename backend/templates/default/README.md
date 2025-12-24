# Modern Blog Template

A clean, modern, and responsive blog template perfect for news sites and personal blogs.

## Features

- **Fully Responsive**: Works beautifully on mobile, tablet, and desktop
- **SEO Optimized**: Includes meta tags, structured data, and sitemap support
- **Fast Loading**: Optimized CSS and JavaScript
- **Accessible**: WCAG compliant with proper ARIA labels and semantic HTML
- **Customizable**: Easy theming through CSS variables
- **Social Sharing**: Built-in social sharing buttons
- **RSS Feed**: Automatic RSS feed generation
- **Sitemap**: XML sitemap support

## Template Structure

```
default/
├── templates/
│   ├── base.html      # Base template with header/footer
│   ├── home.html      # Homepage/blog listing
│   ├── post.html      # Single post view
│   ├── category.html  # Category archive
│   ├── page.html      # Static pages
│   └── 404.html       # Error page
├── assets/
│   ├── css/
│   │   └── style.css  # Main stylesheet
│   └── js/
│       └── main.js    # JavaScript functionality
├── config.json        # Template configuration
└── README.md          # This file
```

## Template Variables

The template receives the following context variables:

### Site Object
- `site.name` - Site name
- `site.description` - Site description
- `site.meta_title` - SEO title
- `site.meta_description` - SEO description
- `site.domain.name` - Domain name
- `site.branding` - Branding object (colors, fonts, logo)
- `site.settings` - Site settings (analytics, custom code, etc.)
- `site.menus` - Navigation menus

### Post Object (for post.html)
- `post.title` - Post title
- `post.slug` - Post URL slug
- `post.content` - Post content (HTML)
- `post.excerpt` - Post excerpt
- `post.featured_image` - Featured image URL
- `post.author_name` - Author name
- `post.published_at` - Publication date
- `post.category` - Category object
- `post.tags` - Comma-separated tags
- `related_posts` - List of related posts

### Category Object (for category.html)
- `category.name` - Category name
- `category.slug` - Category slug
- `category.description` - Category description
- `category.color` - Category color (hex)
- `posts` - List of posts in category

### Page Object (for page.html)
- `page.title` - Page title
- `page.slug` - Page slug
- `page.content` - Page content (HTML)
- `page.meta_title` - SEO title
- `page.meta_description` - SEO description

## Customization

### Colors
Colors are controlled via CSS variables in `base.html`:
- `--primary-color` - Primary brand color
- `--secondary-color` - Secondary color
- `--accent-color` - Accent color
- `--background-color` - Background color
- `--text-color` - Text color

### Fonts
Fonts can be customized through the `font_family` setting in site branding. The template supports Google Fonts (Inter is included by default).

### Custom CSS/JS
Users can inject custom CSS and JavaScript through the site settings panel.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

This template is part of the MetaView platform.

