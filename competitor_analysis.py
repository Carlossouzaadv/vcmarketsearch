"""
Competitor Analysis Module
Analyzes competitors in depth and identifies market opportunities.
"""

import json
import requests
import google.generativeai as genai
from typing import Dict, List


class CompetitorAnalyzer:
    """Analyzes competitors and identifies market whitespace."""

    def __init__(self, parallel_api_key: str, gemini_api_key: str):
        """
        Initialize Competitor Analyzer with API keys.

        Args:
            parallel_api_key: Parallel AI API key
            gemini_api_key: Google Gemini API key
        """
        self.parallel_api_key = parallel_api_key
        self.base_url = "https://api.parallel.ai"
        self.headers = {
            "x-api-key": parallel_api_key,
            "Content-Type": "application/json",
            "parallel-beta": "search-extract-2025-10-10"
        }

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def analyze_competitor(
        self,
        url: str,
        name: str,
        target_startup: Dict
    ) -> Dict:
        """
        Perform deep analysis of a competitor.

        Args:
            url: Competitor website URL
            name: Competitor name
            target_startup: Target startup information for comparison

        Returns:
            Dictionary with detailed competitor analysis
        """
        print(f"    → Extracting data from {name}")

        # Extract comprehensive competitor information
        try:
            response = requests.post(
                f"{self.base_url}/v1beta/extract",
                headers=self.headers,
                json={
                    "urls": [url],
                    "objective": f"""Extract comprehensive information about {name}:

PRODUCT INFORMATION:
- Complete product/service offerings and features
- Core capabilities and unique selling points
- Technology stack, approach, or methodology (if mentioned)
- Product differentiators

MARKET INFORMATION:
- Target market and customer segments (company size, industries, roles)
- Customer testimonials, case studies, or notable clients
- Market positioning and messaging

BUSINESS MODEL:
- Pricing model and tiers (if available)
- Revenue model (subscription, usage-based, etc.)

COMPANY INFORMATION:
- Company size, funding status (if mentioned)
- Founding story or mission
- Geographic presence

CONTENT & MESSAGING:
- Key value propositions
- Main marketing messages
- Pain points they address""",
                    "excerpts": True,
                    "full_content": True
                },
                timeout=60
            )
            response.raise_for_status()
            extract_data = response.json()

            if not extract_data.get("results"):
                raise ValueError("No extraction results")

            content = extract_data["results"][0].get("content", "")

        except Exception as e:
            print(f"    ⚠ Could not extract from {url}: {e}")
            content = f"Website: {url}"

        # Analyze with Gemini
        print(f"    → Analyzing {name} with Gemini")

        prompt = f"""Perform a deep competitive analysis of this competitor relative to our target startup.

TARGET STARTUP:
Name: {target_startup.get('name', 'Unknown')}
Description: {target_startup.get('description', 'Unknown')}
Category: {target_startup.get('category', 'Unknown')}
Target Market: {target_startup.get('target_market', 'Unknown')}
Key Features: {json.dumps(target_startup.get('key_features', []))}

COMPETITOR: {name}
COMPETITOR WEBSITE CONTENT:
{content[:10000]}

Provide a JSON object with:

- product_overview: comprehensive 3-4 sentence overview of their offering (string)
- target_customers: detailed description of their customer base (string)
- key_features: array of 5-8 main features/capabilities (array of strings)
- unique_selling_points: array of 2-4 things that differentiate them (array of strings)
- strengths: array of 4-6 competitive advantages (be specific about what they do well) (array of strings)
- weaknesses: array of 4-6 gaps, limitations, or areas where they fall short (be critical and specific) (array of strings)
- pricing_model: their pricing approach if known (string or "Not specified")
- market_position: their market positioning (e.g., "Enterprise leader", "Developer-focused challenger", "Budget-friendly option") (string)
- technology_approach: their technical approach or stack if mentioned (string or "Not specified")
- notable_customers: array of notable customers/case studies if mentioned (array of strings or empty array)
- comparison_to_target: 2-3 sentences comparing them directly to target startup - how are they similar/different? (string)

ANALYSIS GUIDELINES:
- Be objective and analytical, not promotional
- Identify both strengths AND weaknesses (no company is perfect)
- Focus on specific, actionable insights
- Consider: product depth, market fit, pricing, ease of use, scalability, support
- Look for what they do better than target AND where they fall short

Respond ONLY with valid JSON, no markdown formatting."""

        try:
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            analysis = json.loads(response_text)

            # Add metadata
            analysis["name"] = name
            analysis["website"] = url

            return analysis

        except Exception as e:
            print(f"    ⚠ Analysis failed for {name}: {e}")
            return {
                "name": name,
                "website": url,
                "product_overview": "Analysis failed",
                "target_customers": "Unknown",
                "key_features": [],
                "strengths": [],
                "weaknesses": [],
                "pricing_model": "Unknown",
                "market_position": "Unknown",
                "comparison_to_target": "Could not analyze"
            }

    def identify_market_gaps(
        self,
        target_startup: Dict,
        competitors: List[Dict]
    ) -> Dict:
        """
        Identify market opportunities and whitespace.

        Args:
            target_startup: Target startup information
            competitors: List of analyzed competitors

        Returns:
            Dictionary with market analysis and opportunities
        """
        print("  → Identifying market opportunities and whitespace")

        # Filter competitors with valid analysis
        valid_competitors = [
            comp for comp in competitors
            if comp.get("strengths") and comp.get("weaknesses")
        ]

        if not valid_competitors:
            print("  ⚠ No valid competitor analyses to process")
            return {
                "market_overview": {},
                "competitor_patterns": {},
                "whitespaces": [],
                "target_startup_positioning": {}
            }

        # Prepare competitor summary
        competitor_summary = [{
            "name": comp["name"],
            "product_overview": comp.get("product_overview", ""),
            "target_customers": comp.get("target_customers", ""),
            "strengths": comp.get("strengths", []),
            "weaknesses": comp.get("weaknesses", []),
            "market_position": comp.get("market_position", ""),
            "key_features": comp.get("key_features", []),
            "pricing_model": comp.get("pricing_model", ""),
            "unique_selling_points": comp.get("unique_selling_points", [])
        } for comp in valid_competitors]

        prompt = f"""Perform strategic market analysis to identify opportunities.

TARGET STARTUP:
{json.dumps(target_startup, indent=2)}

COMPETITORS ANALYSIS:
{json.dumps(competitor_summary, indent=2)}

Provide a JSON object with:

1. market_overview:
   - total_competitors: number of competitors analyzed (integer)
   - market_maturity: "emerging" / "growing" / "mature" - based on number and sophistication of players (string)
   - market_size_indicator: "niche" / "mid-market" / "large" - based on number of players and their scale (string)
   - key_trends: array of 3-5 observable market trends (array of strings)
   - competitive_intensity: "low" / "medium" / "high" - how crowded is this space (string)

2. competitor_patterns:
   - common_strengths: array of 3-5 things most competitors do well (table stakes features) (array of strings)
   - common_weaknesses: array of 3-5 shared gaps across multiple competitors (array of strings)
   - positioning_clusters: array of 2-4 groups showing how competitors cluster by positioning, e.g., "Enterprise-focused (Company A, Company B)", "SMB self-serve (Company C)" (array of strings)
   - pricing_patterns: description of pricing approaches observed (string)

3. whitespaces: array of 4-7 specific opportunities where market is underserved:
   For each opportunity:
   - opportunity: clear description of the gap (string)
   - why_exists: why this gap hasn't been filled - technical difficulty, market dynamics, etc. (string)
   - potential_value: business impact if captured - revenue potential, market size, strategic value (string)
   - difficulty: "low" / "medium" / "high" - difficulty of execution (string)
   - relevant_competitors_weakness: which competitors struggle here (string)

4. target_startup_positioning:
   - competitive_advantages: array of 3-5 specific things target does better than competitors (array of strings)
   - vulnerability_areas: array of 2-4 areas where target is at risk vs competitors (array of strings)
   - differentiation_opportunities: array of 2-3 ways target could further differentiate (array of strings)
   - recommended_strategy: 3-4 sentence strategic recommendation for how to compete and win (string)
   - positioning_statement: 1-2 sentence positioning vs market (string)

ANALYSIS APPROACH:
- Look for patterns across ALL competitors
- Identify what EVERYONE does (table stakes) vs what NO ONE does well (opportunities)
- Consider: features, pricing, target markets, use cases, technical approaches
- Be specific and actionable - avoid generic insights
- Focus on whitespace where target startup could win

Respond ONLY with valid JSON, no markdown formatting."""

        try:
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            analysis = json.loads(response_text)
            return analysis

        except Exception as e:
            print(f"  ⚠ Market gap analysis failed: {e}")
            return {
                "market_overview": {
                    "total_competitors": len(valid_competitors),
                    "market_maturity": "unknown",
                    "key_trends": [],
                    "competitive_intensity": "unknown"
                },
                "competitor_patterns": {
                    "common_strengths": [],
                    "common_weaknesses": [],
                    "positioning_clusters": []
                },
                "whitespaces": [],
                "target_startup_positioning": {
                    "competitive_advantages": [],
                    "vulnerability_areas": [],
                    "recommended_strategy": "Analysis could not be completed"
                }
            }
