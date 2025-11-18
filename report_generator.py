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

    def __init__(self, gemini_api_key: str, language: str = "en"):
        """
        Initialize Report Generator.

        Args:
            gemini_api_key: Google Gemini API key
            language: Language for report generation ("en" or "pt")
        """
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.language = language

        # Language-specific instruction
        self.lang_instruction = ""
        if language == "pt":
            self.lang_instruction = "\n\nIMPORTANTE: Escreva TODO o conteúdo em PORTUGUÊS BRASILEIRO. Use terminologia de negócios em português."

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
- No bullet points in this section - flowing prose only{self.lang_instruction}

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

    def generate_funding_section(
        self,
        startup: Dict,
        competitors: List[Dict],
        funding_landscape: Dict
    ) -> str:
        """
        Generate funding analysis section using Gemini.

        Args:
            startup: Target startup information with funding data
            competitors: List of analyzed competitors with funding data
            funding_landscape: Market funding landscape analysis

        Returns:
            Markdown formatted funding section
        """
        target_funding = startup.get('funding_data', {})
        funded_competitors = [c for c in competitors if c.get('funding_data', {}).get('is_funded')]

        prompt = f"""Synthesize funding and capitalization insights for this market analysis.

TARGET STARTUP FUNDING:
{json.dumps(target_funding, indent=2)}

FUNDED COMPETITORS: {len(funded_competitors)} out of {len(competitors)}

MARKET FUNDING LANDSCAPE:
{json.dumps(funding_landscape, indent=2)}

Write a comprehensive funding analysis in markdown format covering:

1. TARGET CAPITAL TRACTION - Analyze the target's funding position (2-3 sentences)
2. MARKET CAPITAL INTENSITY - Total capital in market and what it means (2-3 sentences)
3. ACTIVE INVESTORS - Who are the most active VCs and what does their presence indicate (2-3 sentences)
4. FUNDING & WHITESPACE - How does competitor funding affect market gaps? Are opportunities already capitalized or still open? (3-4 sentences)
5. STRATEGIC IMPLICATIONS - What does the funding landscape mean for investment thesis? (2-3 sentences)

STYLE:
- Data-driven and analytical
- Specific dollar amounts and investor names
- Connect funding to competitive dynamics
- Highlight implications for investment decision

Return markdown formatted text with clear headings."""

        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"  ⚠ Could not generate funding section: {e}")
            # Fallback: basic funding summary
            total_market = funding_landscape.get('total_market_funding', 0)
            funded_count = funding_landscape.get('funded_competitors_count', 0)

            return f"""### Capital Traction

**Target Funding:** {target_funding.get('latest_round', 'Unknown')} - ${target_funding.get('total_funding', 0):,}

**Market Capital:** ${total_market:,} raised across {funded_count} competitors

### Strategic Implications

The funding landscape indicates {'high' if total_market > 100_000_000 else 'moderate'} capital intensity in this market."""

    def generate_report(
        self,
        startup: Dict,
        competitors: List[Dict],
        market_analysis: Dict,
        funding_landscape: Dict = None,
        output_dir: str = "reports"
    ) -> str:
        """
        Generate comprehensive markdown report.

        Args:
            startup: Target startup information
            competitors: List of analyzed competitors
            market_analysis: Market gaps and opportunities
            funding_landscape: Market funding landscape analysis (optional)
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

        # Funding Analysis Section (if available)
        if funding_landscape:
            print("  → Generating funding analysis section")
            report += "## Funding Analysis & Investor Landscape\n\n"

            funding_section = self.generate_funding_section(
                startup=startup,
                competitors=competitors,
                funding_landscape=funding_landscape
            )

            report += funding_section + "\n\n"

            # Add raw funding data table
            report += "### Funding Summary Table\n\n"
            report += "| Company | Latest Round | Total Funding | Key Investors |\n"
            report += "|---------|--------------|---------------|---------------|\n"

            # Add target
            target_funding = startup.get('funding_data', {})
            if target_funding.get('is_funded'):
                investors_str = ", ".join(target_funding.get('key_investors', [])[:3])
                report += f"| **{startup.get('name')}** (Target) | {target_funding.get('latest_round', 'N/A')} | ${target_funding.get('total_funding', 0):,} | {investors_str} |\n"
            else:
                report += f"| **{startup.get('name')}** (Target) | Not funded | $0 | - |\n"

            # Add competitors
            for comp in competitors:
                comp_funding = comp.get('funding_data', {})
                if comp_funding.get('is_funded'):
                    investors_str = ", ".join(comp_funding.get('key_investors', [])[:3])
                    report += f"| {comp.get('name', 'Unknown')} | {comp_funding.get('latest_round', 'N/A')} | ${comp_funding.get('total_funding', 0):,} | {investors_str} |\n"
                else:
                    report += f"| {comp.get('name', 'Unknown')} | Not funded | $0 | - |\n"

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
