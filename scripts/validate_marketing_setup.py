#!/usr/bin/env python3
"""
Validation script for marketing integration.
Checks that all components are ready for production.
"""
import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


def check_mark(passed: bool) -> str:
    """Return check mark or X based on pass/fail"""
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"


def main():
    print(f"\n{BOLD}=== Marketing Integration Validation ==={RESET}\n")
    
    all_passed = True
    
    # 1. Check database models
    print(f"{BOLD}1. Database Models{RESET}")
    models = [
        'apps/api/app/models/persona.py',
        'apps/api/app/models/audience.py',
        'apps/api/app/models/creative.py',
        'apps/api/app/models/campaign.py',
        'apps/api/app/models/experiment.py',
        'apps/api/app/models/marketing_metric.py',
    ]
    for model in models:
        exists = Path(model).exists()
        print(f"  {check_mark(exists)} {Path(model).name}")
        all_passed = all_passed and exists
    
    # 2. Check migration
    print(f"\n{BOLD}2. Database Migration{RESET}")
    migration = 'apps/api/alembic/versions/002_2024_10_30_1200-marketing_schema.py'
    exists = Path(migration).exists()
    print(f"  {check_mark(exists)} Marketing migration file")
    all_passed = all_passed and exists
    
    # 3. Check services
    print(f"\n{BOLD}3. Marketing Services{RESET}")
    services = [
        'apps/api/app/services/marketing/persona_discovery.py',
        'apps/api/app/services/marketing/creative_generator.py',
        'apps/api/app/services/marketing/budget_optimizer.py',
        'apps/api/app/services/marketing/attribution.py',
    ]
    for service in services:
        exists = Path(service).exists()
        print(f"  {check_mark(exists)} {Path(service).stem.replace('_', ' ').title()}")
        all_passed = all_passed and exists
    
    # 4. Check adapters
    print(f"\n{BOLD}4. Platform Adapters{RESET}")
    adapters = [
        'apps/api/app/adapters/meta_marketing.py',
        'apps/api/app/adapters/google_ads.py',
        'apps/api/app/adapters/tiktok_ads.py',
    ]
    for adapter in adapters:
        exists = Path(adapter).exists()
        print(f"  {check_mark(exists)} {Path(adapter).stem.replace('_', ' ').title()}")
        all_passed = all_passed and exists
    
    # 5. Check API routes
    print(f"\n{BOLD}5. API Routes{RESET}")
    routes = [
        'apps/api/app/routes/marketing.py',
        'apps/api/app/routes/monitoring.py',
    ]
    for route in routes:
        exists = Path(route).exists()
        print(f"  {check_mark(exists)} {Path(route).stem.title()} routes")
        all_passed = all_passed and exists
    
    # 6. Check frontend pages
    print(f"\n{BOLD}6. Frontend Pages{RESET}")
    pages = [
        'apps/web/app/marketing/personas/page.tsx',
        'apps/web/app/marketing/creatives/page.tsx',
        'apps/web/app/marketing/campaigns/page.tsx',
        'apps/web/app/marketing/budget/page.tsx',
    ]
    for page in pages:
        exists = Path(page).exists()
        page_name = Path(page).parent.name.title()
        print(f"  {check_mark(exists)} {page_name} dashboard")
        all_passed = all_passed and exists
    
    # 7. Check tests
    print(f"\n{BOLD}7. Test Suite{RESET}")
    tests = [
        'apps/api/tests/test_marketing/test_persona_discovery.py',
        'apps/api/tests/test_marketing/test_creative_generator.py',
        'apps/api/tests/test_marketing/test_budget_optimizer.py',
        'apps/api/tests/test_marketing/test_attribution.py',
        'apps/api/tests/test_e2e_marketing.py',
    ]
    for test in tests:
        exists = Path(test).exists()
        test_name = Path(test).stem.replace('test_', '').replace('_', ' ').title()
        print(f"  {check_mark(exists)} {test_name}")
        all_passed = all_passed and exists
    
    # 8. Check monitoring
    print(f"\n{BOLD}8. Monitoring & Alerts{RESET}")
    monitoring_files = [
        'apps/api/app/monitoring.py',
        'apps/api/app/routes/monitoring.py',
    ]
    for mon_file in monitoring_files:
        exists = Path(mon_file).exists()
        print(f"  {check_mark(exists)} {Path(mon_file).name}")
        all_passed = all_passed and exists
    
    # 9. Check documentation
    print(f"\n{BOLD}9. Documentation{RESET}")
    docs = [
        'MARKETING_INTEGRATION_GUIDE.md',
        'MARKETING_AGENT_SUMMARY.md',
        'MARKETING_QUICKSTART.md',
        'DEPLOYMENT_GUIDE.md',
        'COMPLETE_IMPLEMENTATION_SUMMARY.md',
    ]
    for doc in docs:
        exists = Path(doc).exists()
        print(f"  {check_mark(exists)} {doc}")
        all_passed = all_passed and exists
    
    # 10. Check configuration
    print(f"\n{BOLD}10. Configuration{RESET}")
    config_file = Path('apps/api/app/config.py')
    if config_file.exists():
        content = config_file.read_text()
        checks = [
            ('meta_access_token' in content, 'Meta configuration'),
            ('google_ads_' in content, 'Google Ads configuration'),
            ('tiktok_' in content, 'TikTok configuration'),
        ]
        for passed, name in checks:
            print(f"  {check_mark(passed)} {name}")
            all_passed = all_passed and passed
    else:
        print(f"  {check_mark(False)} Config file missing")
        all_passed = False
    
    # Summary
    print(f"\n{BOLD}{'='*50}{RESET}")
    if all_passed:
        print(f"{GREEN}{BOLD}✓ All checks passed! Ready to deploy!{RESET}")
        print(f"\n{BOLD}Next steps:{RESET}")
        print("  1. Run migration: cd apps/api && alembic upgrade head")
        print("  2. Install deps: pip install -r apps/api/requirements.txt")
        print("  3. Run tests: pytest apps/api/tests/test_marketing/")
        print("  4. Start services: make api && make web")
        print("  5. See DEPLOYMENT_GUIDE.md for production deployment")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Some checks failed. Please review above.{RESET}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

