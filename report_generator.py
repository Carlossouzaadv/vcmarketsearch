"""
Report Generator Module
Generates investment-ready markdown reports with executive summaries.
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import google.generativeai as genai


class ReportGenerator:
    """Generates comprehensive market research reports."""

    def __init__(self, gemini_api_key: str):
        """
        Initialize Report Generator.

        Args:
            gemini_api_key: Google Gemini API key
        """
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_executive_summary(
        self,
        startup: Dict,
        competitors: List[Dict],
        analysis: Dict
    ) -> str:
        """
        Generate executive summary using Gemini.

        Args:
            startup: Target startup information
            competitors: List of analyzed competitors
            analysis: Market analysis and opportunities

        Returns:
            Executive summary text
        """
        market_overview = analysis.get("market_overview", {})
        whitespaces = analysis.get("whitespaces", [])
        positioning = analysis.get("target_startup_positioning", {})

        prompt = f"""Write a compelling executive summary for a VC investment committee.

COMPANY: {startup.get('name')} - {startup.get('description')}
CATEGORY: {startup.get('category')}
COMPETITORS ANALYZED: {len(competitors)}
MARKET MATURITY: {market_overview.get('market_maturity', 'unknown')}
COMPETITIVE INTENSITY: {market_overview.get('competitive_intensity', 'unknown')}
OPPORTUNITIES IDENTIFIED: {len(whitespaces)}

KEY INSIGHTS:
{json.dumps(positioning, indent=2)}

Write 4-5 well-structured paragraphs covering:

1. MARKET OPPORTUNITY - Size, maturity, and growth potential of this market
2. COMPETITIVE LANDSCAPE - Overview of key players and market dynamics
3. WHITESPACE & OPPORTUNITIES - Most compelling gaps in the market
4. TARGET POSITIONING - How the target company is positioned vs competition
5. INVESTMENT THESIS - Why this could be an attractive opportunity (be balanced, note risks too)

STYLE GUIDELINES:
- Professional, data-driven tone for sophisticated investors
- Lead with insights, not descriptions
- Use specific examples and data points
- Be objective - acknowledge both opportunities and challenges
- 200-250 words total
- No bullet points in this section - flowing prose only

Write the executive summary:"""

        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"  ⚠ Could not generate executive summary: {e}")
            return f"""## Executive Summary

This report analyzes {startup.get('name')} in the context of the {startup.get('category')} market.
We identified {len(competitors)} direct competitors and analyzed market opportunities.

The analysis reveals several potential whitespace opportunities and provides strategic recommendations
for market positioning. See detailed findings below."""

    def generate_report(
        self,
        startup: Dict,
        competitors: List[Dict],
        market_analysis: Dict,
        output_dir: str = "reports"
    ) -> str:
        """
        Generate comprehensive markdown report.

        Args:
            startup: Target startup information
            competitors: List of analyzed competitors
            market_analysis: Market gaps and opportunities
            output_dir: Directory to save report

        Returns:
            Path to generated report file
        """
        print("  → Generating executive summary")
        exec_summary = self.generate_executive_summary(
            startup,
            competitors,
            market_analysis
        )

        # Start building the report
        report = f"""# Market Research Report: {startup.get('name', 'Unknown Company')}

**Generated:** {datetime.now().strftime('%B %d, %Y')}
**Category:** {startup.get('category', 'Unknown')}
**Target Market:** {startup.get('target_market', 'Unknown')}

---

## Executive Summary

{exec_summary}

---

## Target Company Analysis

### {startup.get('name', 'Unknown Company')}

**Website:** {startup.get('url', 'N/A')}

**Description:**
{startup.get('description', 'No description available')}

**Market Position:** {startup.get('market_position', 'N/A')}

**Key Features:**
"""

        for feature in startup.get('key_features', []):
            report += f"- {feature}\n"

        report += f"\n**Pricing Model:** {startup.get('pricing_model', 'Not specified')}\n\n"

        # Market Overview
        market_overview = market_analysis.get('market_overview', {})
        report += f"""---

## Market Overview

**Market Maturity:** {market_overview.get('market_maturity', 'Unknown').title()}
**Competitive Intensity:** {market_overview.get('competitive_intensity', 'Unknown').title()}
**Market Size:** {market_overview.get('market_size_indicator', 'Unknown').title()}
**Competitors Analyzed:** {market_overview.get('total_competitors', len(competitors))}

### Key Market Trends

"""

        for trend in market_overview.get('key_trends', []):
            report += f"- {trend}\n"

        # Competitive Landscape
        report += "\n---\n\n## Competitive Landscape\n\n"

        competitor_patterns = market_analysis.get('competitor_patterns', {})

        report += "### Market Patterns\n\n"
        report += "**Table Stakes (What Everyone Does):**\n"
        for strength in competitor_patterns.get('common_strengths', []):
            report += f"- ✓ {strength}\n"

        report += "\n**Common Gaps (Shared Weaknesses):**\n"
        for weakness in competitor_patterns.get('common_weaknesses', []):
            report += f"- ✗ {weakness}\n"

        report += "\n**Market Positioning Clusters:**\n"
        for cluster in competitor_patterns.get('positioning_clusters', []):
            report += f"- {cluster}\n"

        if competitor_patterns.get('pricing_patterns'):
            report += f"\n**Pricing Patterns:** {competitor_patterns['pricing_patterns']}\n"

        # Competitor Details
        report += "\n---\n\n## Detailed Competitor Analysis\n\n"

        valid_competitors = [c for c in competitors if c.get('strengths')]

        for i, comp in enumerate(valid_competitors, 1):
            report += f"### {i}. {comp.get('name', 'Unknown')}\n\n"
            report += f"**Website:** {comp.get('website', 'N/A')}  \n"
            report += f"**Market Position:** {comp.get('market_position', 'N/A')}\n\n"

            report += f"**Overview:**  \n{comp.get('product_overview', 'N/A')}\n\n"

            report += f"**Target Customers:** {comp.get('target_customers', 'N/A')}\n\n"

            # Strengths
            report += "**Strengths:**\n"
            for strength in comp.get('strengths', [])[:6]:
                report += f"- ✓ {strength}\n"

            # Weaknesses
            report += "\n**Weaknesses:**\n"
            for weakness in comp.get('weaknesses', [])[:6]:
                report += f"- ✗ {weakness}\n"

            # Notable features
            if comp.get('unique_selling_points'):
                report += "\n**Key Differentiators:**\n"
                for usp in comp.get('unique_selling_points', []):
                    report += f"- {usp}\n"

            # Pricing
            pricing = comp.get('pricing_model', 'Not specified')
            report += f"\n**Pricing:** {pricing}\n"

            # Comparison
            comparison = comp.get('comparison_to_target', '')
            if comparison:
                report += f"\n**vs Target:** {comparison}\n"

            report += "\n---\n\n"

        # Market Opportunities
        whitespaces = market_analysis.get('whitespaces', [])
        report += "## Market Opportunities & Whitespace\n\n"

        if not whitespaces:
            report += "*No specific opportunities identified in the analysis.*\n\n"
        else:
            for i, opportunity in enumerate(whitespaces, 1):
                report += f"### {i}. {opportunity.get('opportunity', 'Unknown Opportunity')}\n\n"
                report += f"**Why This Gap Exists:**  \n{opportunity.get('why_exists', 'N/A')}\n\n"
                report += f"**Potential Value:**  \n{opportunity.get('potential_value', 'N/A')}\n\n"
                report += f"**Execution Difficulty:** {opportunity.get('difficulty', 'Unknown').upper()}\n"

                if opportunity.get('relevant_competitors_weakness'):
                    report += f"\n**Who Struggles Here:** {opportunity['relevant_competitors_weakness']}\n"

                report += "\n---\n\n"

        # Strategic Recommendations
        positioning = market_analysis.get('target_startup_positioning', {})
        report += "## Strategic Recommendations\n\n"

        if positioning.get('positioning_statement'):
            report += f"**Recommended Positioning:**  \n{positioning['positioning_statement']}\n\n"

        if positioning.get('recommended_strategy'):
            report += f"**Strategic Approach:**  \n{positioning['recommended_strategy']}\n\n"

        report += "### Competitive Advantages to Leverage\n\n"
        for adv in positioning.get('competitive_advantages', []):
            report += f"- ✓ {adv}\n"

        report += "\n### Vulnerability Areas to Address\n\n"
        for vuln in positioning.get('vulnerability_areas', []):
            report += f"- ⚠ {vuln}\n"

        if positioning.get('differentiation_opportunities'):
            report += "\n### Differentiation Opportunities\n\n"
            for diff in positioning['differentiation_opportunities']:
                report += f"- {diff}\n"

        # Footer
        report += f"\n\n---\n\n*Report generated by VC Market Research Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        # Save report
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{startup.get('name', 'company').replace(' ', '_').lower()}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"  ✓ Report saved to {filepath}")
        return filepath
