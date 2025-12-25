# Domain Routing Alternatives - Scalable Solutions

## The Problem

While Railway supports wildcard domains for subdomains (`*.yourdomain.com`), adding individual custom domains for each user requires either:
1. Manual addition in Railway dashboard (not scalable)
2. Using Railway API to add domains programmatically ✅ (now implemented!)
3. Using a proxy service like Cloudflare

## ✅ Good News!

Railway **DOES support**:
- ✅ Wildcard domains (`*.yourdomain.com`)
- ✅ GraphQL API for programmatic domain management
- ✅ Automatic SSL provisioning

This means you have multiple scalable options!

## ✅ Solution Options

### Option 1: Cloudflare Proxy (RECOMMENDED - Industry Standard) ⭐⭐⭐

**How it works:**
- Cloudflare handles DNS and SSL for all domains
- Routes traffic to your Railway backend
- Supports wildcard DNS and SSL
- Free SSL certificates for all domains

**Setup:**

1. **Point all domains to Cloudflare:**
   ```
   Users add their domain to Cloudflare
   Cloudflare handles DNS and SSL
   ```

2. **Configure Cloudflare DNS:**
   ```
   Type: CNAME (or A record)
   Name: @ (or www)
   Target: your-railway-backend.railway.app
   Proxy: ON (orange cloud)
   ```

3. **Update Railway:**
   - Only need ONE custom domain: Your main Railway domain
   - All traffic comes through Cloudflare proxy
   - Railway sees Cloudflare IPs, not user domains

4. **Update Backend:**
   - Read `X-Forwarded-Host` header instead of `Host` header
   - Cloudflare passes original domain in headers

**Pros:**
- ✅ Unlimited domains (wildcard support)
- ✅ Free SSL for all domains
- ✅ DDoS protection
- ✅ CDN caching
- ✅ No Railway domain limits

**Cons:**
- ⚠️ Users need Cloudflare account (or you manage it)
- ⚠️ Need to handle Cloudflare API for domain management (optional)

**This is what successful SaaS platforms use!**
- Vercel, Netlify, Shopify, and many others use Cloudflare
- Industry standard for custom domain management
- Your backend already supports it (X-Forwarded-Host header)

**Implementation:**
```python
# In routes_public_site.py
def get_site_from_host(request: Request, db: Session):
    # Check Cloudflare headers first
    host = (
        request.headers.get("X-Forwarded-Host") or  # Cloudflare
        request.headers.get("Host") or              # Direct
        ""
    )
    domain_name = host.split(":")[0]
    return get_site_by_domain(db, domain_name)
```

---

### Option 2: Subdomain Approach

**How it works:**
- All sites use subdomains: `site1.yourplatform.com`, `site2.yourplatform.com`
- Single wildcard DNS: `*.yourplatform.com` → Railway
- One Railway custom domain: `*.yourplatform.com`

**Setup:**

1. **DNS Configuration:**
   ```
   Type: CNAME
   Name: *
   Value: your-railway-backend.railway.app
   ```

2. **Railway:**
   - Add custom domain: `*.yourplatform.com` (if Railway supports)
   - Or add: `yourplatform.com` and handle subdomains in app

3. **Backend:**
   - Extract subdomain from Host header
   - Map subdomain to site in database

**Pros:**
- ✅ Single domain to manage
- ✅ Easier SSL (wildcard cert)
- ✅ Simpler DNS setup

**Cons:**
- ❌ Users don't get their own domain
- ❌ Less professional
- ❌ SEO limitations

**Implementation:**
```python
def get_site_from_subdomain(request: Request, db: Session):
    host = request.headers.get("host", "")
    subdomain = host.split(".")[0]  # site1.yourplatform.com -> site1
    
    # Look up site by subdomain
    site = db.query(PublishedSite).filter(
        PublishedSite.subdomain == subdomain,
        PublishedSite.status == 'published'
    ).first()
    return site
```

---

### Option 3: Railway API + Wildcard Domain (RECOMMENDED FOR RAILWAY) ⭐

**Railway supports:**
- ✅ **Wildcard domains** (`*.yourdomain.com`)
- ✅ **GraphQL API** for programmatic domain management
- ✅ **Automatic SSL** provisioning

**Setup:**

1. **Add Wildcard Domain in Railway:**
   ```
   Railway Dashboard → Backend Service → Settings → Networking
   Add Custom Domain: *.yourplatform.com
   ```

2. **Configure DNS:**
   ```
   Type: CNAME
   Name: *
   Value: your-railway-backend.railway.app
   ```

3. **Use Railway API for Custom Domains:**
   - When user adds their own domain, call Railway API
   - Railway automatically provisions SSL
   - No manual Railway dashboard steps needed

**Implementation:**

```python
# backend/services/railway_domain_service.py
def add_domain_to_railway(domain: str):
    """Add custom domain to Railway via GraphQL API."""
    response = requests.post(
        "https://backboard.railway.app/graphql/v2",
        headers={
            "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "query": """
                mutation customDomainCreate($input: CustomDomainCreateInput!) {
                    customDomainCreate(input: $input) {
                        id domain status
                    }
                }
            """,
            "variables": {
                "input": {
                    "domain": domain,
                    "serviceId": RAILWAY_SERVICE_ID
                }
            }
        }
    )
    return response.json()
```

**Environment Variables Needed:**
```
RAILWAY_API_TOKEN=your_railway_api_token
RAILWAY_SERVICE_ID=your_backend_service_id
RAILWAY_ENVIRONMENT_ID=your_environment_id (optional)
```

**Pros:**
- ✅ Automated domain addition
- ✅ Stays on Railway (no external services)
- ✅ Automatic SSL provisioning
- ✅ Wildcard support for subdomains
- ✅ Free SSL certificates

**Cons:**
- ⚠️ Requires Railway API token
- ⚠️ Users still need to configure DNS
- ⚠️ API rate limits may apply

**This is now implemented!** See `backend/services/railway_domain_service.py`

---

### Option 4: External Reverse Proxy

**Services:**
- **Cloudflare Workers** - Serverless proxy
- **AWS CloudFront** - CDN with custom domains
- **Fastly** - Edge computing platform
- **Nginx Proxy Manager** - Self-hosted

**How it works:**
- Proxy service handles all domains
- Routes to Railway backend
- Manages SSL certificates

**Pros:**
- ✅ Unlimited domains
- ✅ Better control
- ✅ Can add domains programmatically

**Cons:**
- ⚠️ Additional service to manage
- ⚠️ Additional costs
- ⚠️ More complex setup

---

### Option 5: Different Hosting Provider

**Providers with wildcard support:**
- **Fly.io** - Supports wildcard domains
- **Render** - Custom domain support
- **DigitalOcean App Platform** - Wildcard domains
- **Heroku** - With add-ons
- **AWS Elastic Beanstalk** - Full control

**Pros:**
- ✅ Native wildcard support
- ✅ Better for SaaS platforms

**Cons:**
- ❌ Migration required
- ❌ Different pricing
- ❌ Learning curve

---

## 🎯 Recommended Solution: Cloudflare Proxy

### Why Cloudflare?

1. **Free SSL** - Automatic SSL for all domains
2. **Wildcard DNS** - Support unlimited domains
3. **DDoS Protection** - Built-in security
4. **CDN** - Faster content delivery
5. **Easy Integration** - Works with Railway

### Implementation Steps

#### Step 1: Update Backend to Read Cloudflare Headers

```python
# backend/api/v1/routes_public_site.py
def get_site_from_host(request: Request, db: Session):
    # Cloudflare passes original host in X-Forwarded-Host
    host = (
        request.headers.get("X-Forwarded-Host") or
        request.headers.get("Host") or
        ""
    )
    domain_name = host.split(":")[0]
    
    # Skip Railway domains
    railway_domains = [".railway.app", ".up.railway.app"]
    if any(rd in domain_name for rd in railway_domains):
        return None
    
    return get_site_by_domain(db, domain_name)
```

#### Step 2: User Domain Setup Flow

1. **User adds domain in your platform**
2. **Platform verifies ownership** (TXT record)
3. **Platform provides DNS instructions:**
   ```
   Type: CNAME
   Name: @
   Value: your-platform.railway.app
   Proxy: ON (Cloudflare)
   ```
4. **User configures DNS** (or you do it via Cloudflare API)
5. **Site works automatically** - No Railway configuration needed!

#### Step 3: Cloudflare API Integration (Optional)

If you want to automate DNS setup:

```python
# Install: pip install cloudflare
import cloudflare

def setup_domain_dns(domain: str, target: str):
    """Add DNS record via Cloudflare API."""
    cf = cloudflare.CloudFlare(
        email=CLOUDFLARE_EMAIL,
        token=CLOUDFLARE_API_TOKEN
    )
    
    zone_id = cf.zones.get(params={"name": domain})[0]["id"]
    
    cf.zones.dns_records.post(zone_id, data={
        "type": "CNAME",
        "name": "@",
        "content": target,
        "proxied": True  # Enable Cloudflare proxy
    })
```

---

## 🔄 Migration Path

### Current Setup → Cloudflare Proxy

1. **Keep Railway backend** (no changes needed)
2. **Add Cloudflare in front**
3. **Update backend** to read `X-Forwarded-Host`
4. **Users point domains to Cloudflare**
5. **Cloudflare proxies to Railway**

### No Railway Changes Needed!

- Railway backend stays the same
- Only need ONE Railway custom domain (your main domain)
- All user domains go through Cloudflare

---

## 📊 Comparison Table

| Solution | Scalability | Cost | Complexity | User Experience |
|----------|------------|------|-------------|-----------------|
| **Cloudflare Proxy** | ⭐⭐⭐⭐⭐ | Free | Medium | ⭐⭐⭐⭐⭐ |
| **Subdomain** | ⭐⭐⭐⭐ | Free | Low | ⭐⭐⭐ |
| **Railway API** | ⭐⭐⭐ | Free/Paid | Low | ⭐⭐⭐⭐ |
| **External Proxy** | ⭐⭐⭐⭐ | Paid | High | ⭐⭐⭐⭐ |
| **Different Host** | ⭐⭐⭐⭐⭐ | Varies | High | ⭐⭐⭐⭐⭐ |

---

## 🚀 Quick Start: Cloudflare Setup

### 1. Create Cloudflare Account
- Sign up at cloudflare.com
- Add your main domain

### 2. Update Backend Code
- Read `X-Forwarded-Host` header
- Handle Cloudflare IP ranges

### 3. DNS Configuration
- Users add CNAME pointing to Railway
- Enable Cloudflare proxy (orange cloud)

### 4. SSL Configuration
- Cloudflare handles SSL automatically
- Free SSL for all domains

---

## 💡 Recommendation

**Use Cloudflare Proxy** - It's the best balance of:
- ✅ Scalability (unlimited domains)
- ✅ Cost (free tier available)
- ✅ Features (SSL, CDN, security)
- ✅ Ease of use (works with Railway)

The backend code changes are minimal - just read the correct header!

