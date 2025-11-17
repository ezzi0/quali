# Platform Account Setup Guide

This guide helps you set up test/sandbox accounts for Meta, Google Ads, and TikTok.

**Note**: This is the ONLY remaining step that requires manual user action. Everything else is complete and ready to use!

---

## Overview

You can run the entire system **WITHOUT** these accounts using:
- **Dry-run mode** for testing (no actual ads created)
- **Mock data** for development
- **Local-only features** (persona discovery, creative generation)

But to actually deploy real campaigns, you'll need API access to at least one platform.

---

## Meta (Facebook/Instagram) - Recommended First

### 1. Create Meta Developer Account

**URL**: https://developers.facebook.com/

**Steps**:
1. Go to Facebook Developers
2. Click "Get Started"
3. Create a developer account (use your personal Facebook)
4. Verify your account (email + phone)

### 2. Create an App

1. Click "Create App"
2. Select "Business" type
3. Name: "Real Estate Marketing CRM"
4. Contact email: your email
5. Click "Create App"

### 3. Get App Credentials

1. In app dashboard, go to "Settings" → "Basic"
2. Copy **App ID** and **App Secret**
3. Add to `.env`:
   ```bash
   META_APP_ID=your_app_id
   META_APP_SECRET=your_app_secret
   ```

### 4. Set Up Marketing API

1. In left sidebar, click "Add Product"
2. Find "Marketing API" and click "Set Up"
3. Accept terms

### 5. Create Test Ad Account

1. Go to https://business.facebook.com/
2. Create a Business Manager account
3. Go to "Business Settings" → "Accounts" → "Ad Accounts"
4. Click "Add" → "Create a new ad account"
5. Name: "Test Ad Account"
6. Currency: AED (or your currency)
7. Time zone: Dubai
8. **Important**: Enable "Test Account" mode (no real charges)

### 6. Get Ad Account ID

1. In Ad Account settings
2. Copy the "Ad Account ID" (format: `act_123456789`)
3. Add to `.env`:
   ```bash
   META_AD_ACCOUNT_ID=act_123456789
   ```

### 7. Generate Access Token

**Option A: Test Token (Quick, 24 hours)**
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app
3. Click "Generate Access Token"
4. Grant permissions:
   - `ads_management`
   - `ads_read`
   - `business_management`
5. Copy token

**Option B: Long-Lived Token (60 days)**
```bash
# Exchange short token for long token
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token" \
  -d "grant_type=fb_exchange_token" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "fb_exchange_token=SHORT_TOKEN"
```

**Option C: System User Token (Never expires - Production)**
1. In Business Manager → "Business Settings"
2. Go to "Users" → "System Users"
3. Click "Add" → create system user
4. Assign assets (your ad account)
5. Generate token with never-expire option

Add to `.env`:
```bash
META_ACCESS_TOKEN=your_access_token
```

### 8. Set Up Conversions API (Optional)

1. In Business Manager → "Events Manager"
2. Click "Connect Data Sources" → "Web"
3. Create a pixel
4. Copy Pixel ID
5. Add to `.env`:
   ```bash
   META_PIXEL_ID=123456789
   ```

### 9. Test Connection

```bash
curl -X GET "https://graph.facebook.com/v19.0/act_YOUR_ACCOUNT_ID/campaigns" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Should return empty campaigns list or existing campaigns.

**Estimated Time**: 30-60 minutes  
**Cost**: FREE (test mode)

---

## Google Ads - Optional

### 1. Create Google Ads Account

**URL**: https://ads.google.com/

**Steps**:
1. Go to Google Ads
2. Click "Start Now"
3. Create account (use Google/Gmail account)
4. Skip campaign creation for now
5. Switch to "Expert Mode"

### 2. Apply for API Access

**URL**: https://developers.google.com/google-ads/api/docs/first-call/dev-token

**Steps**:
1. Go to Google Ads UI
2. Click "Tools & Settings" → "Setup" → "API Center"
3. Apply for Developer Token
4. Fill out application (explain use case)
5. **Wait for approval** (can take 24-48 hours)

### 3. Create Google Cloud Project

**URL**: https://console.cloud.google.com/

1. Create new project: "Real Estate Marketing"
2. Enable "Google Ads API"
3. Create OAuth 2.0 credentials
4. Add authorized redirect URIs
5. Download credentials JSON

### 4. Generate Refresh Token

Use Google's OAuth Playground:
1. Go to https://developers.google.com/oauthplayground/
2. Settings → Use your OAuth credentials
3. Scope: `https://www.googleapis.com/auth/adwords`
4. Authorize APIs
5. Exchange auth code for tokens
6. Copy Refresh Token

### 5. Configure Environment

```bash
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_DEVELOPER_TOKEN=your_dev_token
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=1234567890  # 10 digits, no hyphens
```

### 6. Test Connection

```bash
# Use Google Ads Python library
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_env()
customer_service = client.get_service("CustomerService")
customer = customer_service.get_customer(resource_name=f"customers/{customer_id}")
```

**Estimated Time**: 2-3 hours (includes approval wait)  
**Cost**: FREE (test account)

---

## TikTok Ads - Optional

### 1. Create TikTok For Business Account

**URL**: https://ads.tiktok.com/

**Steps**:
1. Go to TikTok Ads Manager
2. Click "Sign Up"
3. Choose "Sign up with email"
4. Complete registration
5. Verify email

### 2. Create Ad Account

1. Log into TikTok Ads Manager
2. Complete business verification (may require documents)
3. Create ad account
4. Select country/region: UAE
5. Currency: AED
6. Time zone: Dubai

### 3. Apply for Marketing API Access

**URL**: https://ads.tiktok.com/marketing_api/

**Steps**:
1. Go to Marketing API homepage
2. Click "Apply for Access"
3. Fill application:
   - Company name
   - Use case: Lead generation for real estate
   - Monthly spend estimate
4. Submit and wait for approval (1-2 weeks)

### 4. Get Access Token

Once approved:
1. Go to TikTok Ads Manager
2. Click "Assets" → "Event" → "Web Events"
3. Create pixel (for tracking)
4. Go to "Tools" → "Marketing API"
5. Generate Access Token
6. Copy token and Advertiser ID

### 5. Configure Environment

```bash
TIKTOK_ACCESS_TOKEN=your_access_token
TIKTOK_ADVERTISER_ID=your_advertiser_id
TIKTOK_PIXEL_ID=your_pixel_id
```

### 6. Test Connection

```bash
curl -X GET "https://business-api.tiktok.com/open_api/v1.3/advertiser/info/" \
  -H "Access-Token: YOUR_ACCESS_TOKEN" \
  -d '{"advertiser_ids": ["YOUR_ADVERTISER_ID"]}'
```

**Estimated Time**: 2-3 hours + approval time (1-2 weeks)  
**Cost**: FREE (test mode)

---

## WhatsApp Business Cloud - Optional

### 1. Prerequisites

- Meta Business Account (from Meta setup above)
- Phone number for WhatsApp Business
- Facebook Page

### 2. Set Up WhatsApp Business

1. In Meta Business Manager
2. Go to "WhatsApp Accounts"
3. Click "Add" → "Create a WhatsApp Business Account"
4. Follow setup wizard
5. Verify phone number

### 3. Get API Credentials

1. In WhatsApp Manager
2. Go to "API Setup"
3. Copy:
   - Phone Number ID
   - WhatsApp Business Account ID
   - Permanent Token

### 4. Configure Environment

```bash
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_ACCESS_TOKEN=your_permanent_token
```

**Estimated Time**: 1-2 hours  
**Cost**: FREE (test mode), $0.005-0.02 per message in production

---

## Testing Without Real Accounts

You can fully test the system without any real platform accounts:

### 1. Use Dry-Run Mode

All adapters support `dry_run=True`:

```python
# In creative_generator.py or budget_optimizer.py
await adapter.create_campaign(..., dry_run=True)
```

This logs the API call but doesn't actually create campaigns.

### 2. Use Mock Adapters

Create mock implementations for testing:

```python
class MockMetaAdapter:
    async def create_campaign(self, name, objective, dry_run=False):
        return {
            "id": "mock_campaign_123",
            "name": name,
            "status": "PAUSED"
        }
```

### 3. Test Core Features

These work without any platform accounts:
- ✅ Persona discovery
- ✅ Creative generation
- ✅ Budget optimization logic
- ✅ Attribution parsing
- ✅ All frontend dashboards
- ✅ Monitoring & alerts

---

## Recommended Setup Order

1. **Start Here**: No accounts needed
   - Run persona discovery
   - Generate creatives
   - Test budget optimizer logic
   - Use frontend dashboards

2. **Add Meta** (easiest, best ROI)
   - Most comprehensive API
   - Test campaigns cheap
   - Facebook + Instagram reach
   - Time: 1 hour

3. **Add Google** (if needed)
   - Search intent capture
   - Broader reach
   - Requires API approval
   - Time: 2-3 hours + wait

4. **Add TikTok** (optional)
   - Younger audience
   - Video-first
   - Requires lengthy approval
   - Time: weeks

---

## Security Best Practices

### 1. Token Management

**Never commit tokens to Git:**
```bash
# .gitignore already includes
.env
.env.*
```

**Use environment variables:**
```bash
# Development
export META_ACCESS_TOKEN=xxx

# Production (use secrets manager)
# - Render: Use dashboard secrets
# - AWS: Use Secrets Manager
# - GCP: Use Secret Manager
```

### 2. Token Rotation

- Rotate access tokens every 60 days
- Use system user tokens for production
- Monitor for unauthorized access

### 3. Permissions

Only grant necessary permissions:
- `ads_management` (required)
- `ads_read` (required)
- `business_management` (optional)

### 4. Test Account Limits

Set hard limits on test accounts:
- Daily spend: $10
- Campaign budget: $5
- Automatic pause rules

---

## Cost Breakdown

### Platform API Access
- **Meta**: FREE ✅
- **Google**: FREE (after approval) ✅
- **TikTok**: FREE (after approval) ✅

### Test Campaign Costs
- **Meta Test Account**: $0 (virtual money) ✅
- **Google Test Account**: $350 free credit ✅
- **TikTok Test**: Varies by region

### Production Costs
- **Per lead**: $5-50 (depends on targeting)
- **Per click**: $0.50-5
- **Impressions**: $5-20 per 1000

**Start small**: $10/day = ~2-20 leads/day

---

## Troubleshooting

### "Access token invalid"
- Token expired (regenerate)
- App not approved (check developer dashboard)
- Insufficient permissions (add required scopes)

### "Ad account not found"
- Wrong ad account ID format
- Account not linked to app
- Account deleted or disabled

### "API limit exceeded"
- Too many requests (add rate limiting)
- Test account restrictions (upgrade to standard)

### "Campaign creation failed"
- Missing required fields (check API docs)
- Special ad category required (housing)
- Budget below minimum ($1/day)

---

## Next Steps After Setup

Once you have at least one platform configured:

1. **Test Dry-Run Mode**
   ```bash
   curl -X POST http://localhost:8000/marketing/campaigns/create \
     -d '{"persona_id": 1, "platform": "meta", "dry_run": true}'
   ```

2. **Create Test Campaign**
   - Use frontend dashboard
   - Set daily budget: $5
   - Target small audience
   - Monitor closely

3. **Track Attribution**
   - Add UTM parameters
   - Install tracking pixel
   - Test conversion events

4. **Scale Gradually**
   - Start: $10/day
   - After 1 week: $50/day
   - After 1 month: $200+/day

---

## Summary

**Fastest Path**: Meta only (1 hour)
**Complete Setup**: Meta + Google (4-5 hours + approval)
**Full Platform**: All three (1-2 weeks with approvals)

**Remember**: You can use everything EXCEPT live campaign deployment without any accounts!

---

**Questions?** Check platform documentation or test with dry-run mode first.

**Ready when you are!** The system is waiting for your API keys. 🚀

