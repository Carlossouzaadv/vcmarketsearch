"""
VC Market Research Agent
Automates due diligence process for venture capital firms.

This agent analyzes startups, discovers competitors, identifies market gaps,
and generates investment-ready reports with visualizations.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

from market_discovery import MarketDiscovery
from competitor_analysis import CompetitorAnalyzer
from report_generator import ReportGenerator
from visualization import MarketVisualizer
from funding_analysis import FundingAnalyzer


def print_banner():
    """Print application banner."""
    print("\n" + "="*70)
    print("  VC MARKET RESEARCH AGENT")
    print("  Automated Due Diligence for Venture Capital")
    print("="*70 + "\n")


def validate_environment():
    """
    Validate required environment variables are set.

    Returns:
        Tuple of (parallel_api_key, gemini_api_key) or None if validation fails
    """
    parallel_key = os.getenv("PARALLEL_AI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not parallel_key:
        print("❌ ERROR: PARALLEL_AI_API_KEY not found in environment")
        print("   Please set it in .env file or environment variables")
        return None

    if not gemini_key:
        print("❌ ERROR: GEMINI_API_KEY not found in environment")
        print("   Please set it in .env file or environment variables")
        return None

    return parallel_key, gemini_key


def save_intermediate_data(data: dict, filename: str, data_dir: str = "data"):
    """
    Save intermediate data to JSON file.

    Args:
        data: Data to save
        filename: Filename (without extension)
        data_dir: Directory to save data
    """
    os.makedirs(data_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(data_dir, f"{filename}_{timestamp}.json")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  💾 Saved intermediate data: {filepath}")


def run_due_diligence(
    startup_url: str,
    startup_name: str = None,
    max_competitors: int = 10,
    skip_visualizations: bool = False,
    parallel_api_key: str = None,
    gemini_api_key: str = None
):
    """
    Run complete market research analysis (Due Diligence).

    This function can be called programmatically from other Python code
    or via the CLI. It returns a comprehensive dictionary with all results.

    Args:
        startup_url: URL of target startup
        startup_name: Optional company name
        max_competitors: Maximum number of competitors to analyze
        skip_visualizations: Skip creating visualizations
        parallel_api_key: Parallel AI API key (optional, uses env if not provided)
        gemini_api_key: Gemini API key (optional, uses env if not provided)

    Returns:
        Dictionary with analysis results or None if failed:
        {
            'startup_info': Dict,
            'competitors': List[Dict],
            'market_analysis': Dict,
            'funding_landscape': Dict,
            'report_path': str,
            'visualization_paths': List[str],
            'timestamp': str
        }
    """
    # Use provided keys or validate environment
    if parallel_api_key and gemini_api_key:
        parallel_key, gemini_key = parallel_api_key, gemini_api_key
    else:
        keys = validate_environment()
        if not keys:
            return None
        parallel_key, gemini_key = keys

    # Initialize components
    print("🔧 Initializing analysis components...")
    discovery = MarketDiscovery(parallel_key, gemini_key)
    analyzer = CompetitorAnalyzer(parallel_key, gemini_key)
    funding_analyzer = FundingAnalyzer(parallel_key, gemini_key, use_simulation=False)
    reporter = ReportGenerator(gemini_key)
    visualizer = MarketVisualizer() if not skip_visualizations else None

    print("\n" + "="*70)
    print("STEP 1: ANALYZING TARGET STARTUP")
    print("="*70)

    try:
        startup_info = discovery.analyze_startup(startup_url, startup_name)

        # Check if analysis was successful
        if (startup_info['name'] == "Unknown Company" or
            startup_info['category'] == "Unknown" or
            not startup_info.get('keywords')):
            print(f"\n⚠️  WARNING: Failed to extract complete startup information")
            print(f"   Name: {startup_info['name']}")
            print(f"   Category: {startup_info['category']}")
            print(f"   This will significantly limit the quality of competitor discovery")
            print(f"\n   Possible causes:")
            print(f"   - Website might be blocking automated access")
            print(f"   - Gemini API might be unavailable")
            print(f"   - API keys might be invalid")
        else:
            print(f"\n✅ Analyzed: {startup_info['name']}")
            print(f"   Category: {startup_info['category']}")
            print(f"   Target Market: {startup_info['target_market']}")
            print(f"   Keywords: {', '.join(startup_info.get('keywords', [])[:5])}")

        save_intermediate_data(startup_info, "startup_info")

    except Exception as e:
        print(f"\n❌ ERROR: Failed to analyze target startup: {e}")
        return None

    print("\n" + "="*70)
    print("STEP 2: DISCOVERING COMPETITORS")
    print("="*70)

    try:
        competitors = discovery.discover_competitors(
            category=startup_info['category'],
            description=startup_info['description'],
            keywords=startup_info.get('keywords', []),
            company_name=startup_info['name'],
            max_competitors=max_competitors
        )

        if not competitors:
            print("\n⚠️  WARNING: No competitors found")
            print("   The analysis will continue but results may be limited")
        else:
            print(f"\n✅ Discovered {len(competitors)} competitors:")
            for i, comp in enumerate(competitors, 1):
                print(f"   {i}. {comp['name']} - {comp['website']}")

        save_intermediate_data(competitors, "competitors")

    except Exception as e:
        print(f"\n❌ ERROR: Failed to discover competitors: {e}")
        return None

    print("\n" + "="*70)
    print("STEP 3: ANALYZING COMPETITORS")
    print("="*70)

    competitor_details = []
    total = len(competitors)

    for i, comp in enumerate(competitors, 1):
        print(f"\n[{i}/{total}] {comp['name']}")

        try:
            details = analyzer.analyze_competitor(
                url=comp['website'],
                name=comp['name'],
                target_startup=startup_info
            )
            competitor_details.append(details)

            # Show preview
            strengths_count = len(details.get('strengths', []))
            weaknesses_count = len(details.get('weaknesses', []))
            print(f"    ✓ Found {strengths_count} strengths, {weaknesses_count} weaknesses")

        except Exception as e:
            print(f"    ⚠️  Failed to analyze {comp['name']}: {e}")
            continue

    if competitor_details:
        print(f"\n✅ Completed analysis of {len(competitor_details)} competitors")
        save_intermediate_data(competitor_details, "competitor_analysis")
    else:
        print("\n⚠️  WARNING: No competitors were successfully analyzed")

    print("\n" + "="*70)
    print("STEP 4: ANALYZING FUNDING & CAPITALIZATION")
    print("="*70)

    # Analyze funding for target startup
    print(f"\n  📊 Analyzing funding data...")
    print(f"\n  [Target] {startup_info['name']}")

    try:
        target_funding = funding_analyzer.analyze_funding(startup_info['name'])
        startup_info['funding_data'] = target_funding

        if target_funding.get('is_funded'):
            print(f"    ✓ Latest Round: {target_funding['latest_round']}")
            print(f"    ✓ Total Funding: ${target_funding['total_funding']:,}")
        else:
            print(f"    ℹ No funding data available")

    except Exception as e:
        print(f"    ⚠️  Failed to analyze funding: {e}")
        startup_info['funding_data'] = {"has_funding_data": False, "is_funded": False}

    # Analyze funding for competitors
    print(f"\n  [Competitors]")
    for i, comp in enumerate(competitor_details, 1):
        print(f"    [{i}/{len(competitor_details)}] {comp['name']}")

        try:
            comp_funding = funding_analyzer.analyze_funding(comp['name'])
            comp['funding_data'] = comp_funding

            if comp_funding.get('is_funded'):
                print(f"        Latest: {comp_funding['latest_round']} - ${comp_funding['total_funding']:,}")

        except Exception as e:
            print(f"        ⚠️  Failed: {e}")
            comp['funding_data'] = {"has_funding_data": False, "is_funded": False}

    # Analyze overall funding landscape
    print(f"\n  → Analyzing market funding landscape...")

    try:
        funding_landscape = funding_analyzer.analyze_market_funding_landscape(
            target_startup=startup_info,
            competitors=competitor_details
        )

        funded_count = funding_landscape.get('funded_competitors_count', 0)
        total_market = funding_landscape.get('total_market_funding', 0)

        print(f"\n✅ Funding analysis complete:")
        print(f"   Funded competitors: {funded_count}/{len(competitor_details)}")
        print(f"   Total market funding: ${total_market:,}")

        save_intermediate_data(funding_landscape, "funding_landscape")

    except Exception as e:
        print(f"\n⚠️  Warning: Funding landscape analysis failed: {e}")
        funding_landscape = {}

    print("\n" + "="*70)
    print("STEP 5: IDENTIFYING MARKET OPPORTUNITIES")
    print("="*70)

    try:
        market_analysis = analyzer.identify_market_gaps(
            target_startup=startup_info,
            competitors=competitor_details
        )

        whitespaces = market_analysis.get('whitespaces', [])
        print(f"\n✅ Identified {len(whitespaces)} market opportunities")

        if whitespaces:
            print("\n   Top Opportunities:")
            for i, opp in enumerate(whitespaces[:3], 1):
                print(f"   {i}. {opp.get('opportunity', 'Unknown')}")
                print(f"      Difficulty: {opp.get('difficulty', 'unknown').upper()}")

        save_intermediate_data(market_analysis, "market_analysis")

    except Exception as e:
        print(f"\n❌ ERROR: Failed to identify market gaps: {e}")
        return None

    print("\n" + "="*70)
    print("STEP 6: GENERATING REPORT")
    print("="*70)

    try:
        report_path = reporter.generate_report(
            startup=startup_info,
            competitors=competitor_details,
            market_analysis=market_analysis,
            funding_landscape=funding_landscape
        )

        print(f"\n✅ Report generated: {report_path}")

    except Exception as e:
        print(f"\n❌ ERROR: Failed to generate report: {e}")
        return None

    # Generate visualizations
    visualization_paths = []

    if not skip_visualizations and visualizer and competitor_details:
        print("\n" + "="*70)
        print("STEP 7: CREATING VISUALIZATIONS")
        print("="*70)

        try:
            market_map, comp_matrix, investor_network = visualizer.create_all_visualizations(
                competitors=competitor_details,
                startup=startup_info,
                funding_landscape=funding_landscape
            )

            if market_map:
                visualization_paths.append(market_map)
            if comp_matrix:
                visualization_paths.append(comp_matrix)
            if investor_network:
                visualization_paths.append(investor_network)

            print(f"\n✅ Created {len(visualization_paths)} visualizations")

        except Exception as e:
            print(f"\n⚠️  Warning: Failed to create visualizations: {e}")

    # Final summary
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\n📊 Report: {report_path}")

    if visualization_paths:
        print(f"\n📈 Visualizations:")
        for path in visualization_paths:
            print(f"   - {path}")

    print(f"\n💾 Intermediate data saved in: data/")

    # Determine if analysis was truly successful
    analysis_success = (
        startup_info['name'] != "Unknown Company" and
        len(competitor_details) > 0 and
        startup_info['category'] != "Unknown"
    )

    if analysis_success:
        print(f"\n✅ Analysis completed successfully!")
        print(f"   Found {len(competitor_details)} competitors")
        print(f"   Generated comprehensive report with insights\n")
    else:
        print(f"\n⚠️  Analysis completed with LIMITED results")
        print(f"   Competitors found: {len(competitor_details)}")
        print(f"   Startup data quality: {'POOR' if startup_info['name'] == 'Unknown Company' else 'PARTIAL'}")
        print(f"\n   Please check:")
        print(f"   1. Are your API keys valid and have credits?")
        print(f"   2. Is the target website accessible?")
        print(f"   3. Check error messages above for details\n")

    # Return comprehensive results dictionary
    return {
        'startup_info': startup_info,
        'competitors': competitor_details,
        'market_analysis': market_analysis,
        'funding_landscape': funding_landscape,
        'report_path': report_path,
        'visualization_paths': visualization_paths,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'success': analysis_success
    }


def main():
    """Main entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="VC Market Research Agent - Automated Due Diligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://example.com
  python main.py https://example.com --name "Example Inc"
  python main.py https://example.com --max-competitors 15
  python main.py https://example.com --skip-viz

Environment Variables:
  PARALLEL_AI_API_KEY   - Parallel AI API key (required)
  GEMINI_API_KEY        - Google Gemini API key (required)
  MAX_COMPETITORS       - Default max competitors (default: 10)
        """
    )

    parser.add_argument(
        'url',
        help='Target startup website URL'
    )

    parser.add_argument(
        '--name',
        help='Company name (optional, will be extracted if not provided)',
        default=None
    )

    parser.add_argument(
        '--max-competitors',
        type=int,
        help='Maximum number of competitors to analyze (default: 10)',
        default=int(os.getenv('MAX_COMPETITORS', '10'))
    )

    parser.add_argument(
        '--skip-viz',
        action='store_true',
        help='Skip creating visualizations'
    )

    args = parser.parse_args()

    print_banner()

    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        print(f"❌ ERROR: Invalid URL: {args.url}")
        print("   URL must start with http:// or https://")
        sys.exit(1)

    # Run due diligence
    result = run_due_diligence(
        startup_url=args.url,
        startup_name=args.name,
        max_competitors=args.max_competitors,
        skip_visualizations=args.skip_viz
    )

    if result and result.get('success'):
        sys.exit(0)
    else:
        print("\n❌ Analysis failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
