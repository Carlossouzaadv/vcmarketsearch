"""
Funding Analysis Module
Analyzes funding data, investment rounds, and investor landscape.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import google.generativeai as genai


class FundingClient:
    """
    Simulated funding data client.
    In production, replace with actual API integration (Crunchbase, PitchBook, etc.)
    """

    # Simulated database of funding data
    FUNDING_DATABASE = {
        "seed": {
            "range": (500_000, 3_000_000),
            "typical_investors": [
                "Y Combinator", "Techstars", "500 Startups", "Seedcamp",
                "Angel List", "First Round Capital", "SV Angel"
            ]
        },
        "series_a": {
            "range": (3_000_000, 15_000_000),
            "typical_investors": [
                "Sequoia Capital", "Andreessen Horowitz", "Accel Partners",
                "Benchmark", "Greylock Partners", "NEA", "Lightspeed Venture Partners"
            ]
        },
        "series_b": {
            "range": (10_000_000, 50_000_000),
            "typical_investors": [
                "Tiger Global", "Insight Partners", "General Catalyst",
                "Index Ventures", "Bessemer Venture Partners", "Redpoint Ventures"
            ]
        },
        "series_c": {
            "range": (30_000_000, 100_000_000),
            "typical_investors": [
                "Softbank Vision Fund", "Coatue Management", "T. Rowe Price",
                "Fidelity Investments", "GGV Capital", "DST Global"
            ]
        },
        "series_d_plus": {
            "range": (75_000_000, 500_000_000),
            "typical_investors": [
                "Softbank Vision Fund", "Tiger Global", "DST Global",
                "Fidelity Investments", "T. Rowe Price", "BlackRock"
            ]
        }
    }

    ROUND_TYPES = ["Seed", "Series A", "Series B", "Series C", "Series D+"]

    def __init__(self, use_simulation: bool = True):
        """
        Initialize funding client.

        Args:
            use_simulation: If True, use simulated data. If False, use real API.
        """
        self.use_simulation = use_simulation

    def _simulate_funding_data(self, company_name: str) -> Optional[Dict]:
        """
        Simulate funding data for a company.

        Args:
            company_name: Name of the company

        Returns:
            Dictionary with simulated funding data or None
        """
        # Randomly decide if company has funding data (80% chance)
        if random.random() > 0.80:
            return None

        # Randomly select funding stage
        round_type = random.choice(self.ROUND_TYPES)
        round_key = round_type.lower().replace(" ", "_").replace("+", "_plus")

        # Get funding data for this stage
        funding_info = self.FUNDING_DATABASE.get(round_key, self.FUNDING_DATABASE["seed"])

        # Generate random funding amount within range
        min_amount, max_amount = funding_info["range"]
        total_funding = random.randint(min_amount, max_amount)

        # Select 2-4 random investors
        num_investors = random.randint(2, 4)
        investors = random.sample(funding_info["typical_investors"], num_investors)

        # Generate random date within last 2 years
        days_ago = random.randint(30, 730)
        funding_date = datetime.now() - timedelta(days=days_ago)

        # Calculate previous rounds (cumulative funding)
        previous_rounds = []
        total_raised = total_funding

        if round_type != "Seed":
            # Add previous rounds
            round_index = self.ROUND_TYPES.index(round_type)
            for i in range(round_index):
                prev_round_type = self.ROUND_TYPES[i]
                prev_round_key = prev_round_type.lower().replace(" ", "_").replace("+", "_plus")
                prev_info = self.FUNDING_DATABASE[prev_round_key]
                prev_amount = random.randint(prev_info["range"][0], prev_info["range"][1])
                prev_investors = random.sample(prev_info["typical_investors"], random.randint(2, 3))

                # Date should be older
                prev_days_ago = days_ago + random.randint(180, 365) * (round_index - i)
                prev_date = datetime.now() - timedelta(days=prev_days_ago)

                previous_rounds.append({
                    "round_type": prev_round_type,
                    "amount": prev_amount,
                    "investors": prev_investors,
                    "date": prev_date.strftime("%Y-%m-%d")
                })

                total_raised += prev_amount

        return {
            "company_name": company_name,
            "latest_round": round_type,
            "latest_round_amount": total_funding,
            "total_funding": total_raised,
            "key_investors": investors,
            "date_of_latest_round": funding_date.strftime("%Y-%m-%d"),
            "previous_rounds": previous_rounds,
            "number_of_rounds": len(previous_rounds) + 1,
            "is_funded": True
        }

    def _fetch_real_funding_data(self, company_name: str) -> Optional[Dict]:
        """
        Fetch real funding data from API (Crunchbase, PitchBook, etc.)

        Args:
            company_name: Name of the company

        Returns:
            Dictionary with funding data or None

        Note:
            This is a placeholder for real API integration.
            Replace with actual API calls in production.
        """
        # TODO: Implement real API integration
        # Example:
        # response = requests.get(
        #     f"https://api.crunchbase.com/v4/entities/organizations/{company_name}",
        #     headers={"X-cb-user-key": self.api_key}
        # )
        # return response.json()

        raise NotImplementedError("Real API integration not implemented yet")

    def get_funding_data(self, company_name: str) -> Optional[Dict]:
        """
        Get funding data for a company.

        Args:
            company_name: Name of the company

        Returns:
            Dictionary with funding data or None if not found
        """
        try:
            if self.use_simulation:
                return self._simulate_funding_data(company_name)
            else:
                return self._fetch_real_funding_data(company_name)

        except Exception as e:
            print(f"      ⚠ Error fetching funding data for {company_name}: {e}")
            return None


class FundingAnalyzer:
    """Analyzes funding data and generates insights."""

    def __init__(self, gemini_api_key: str, use_simulation: bool = True):
        """
        Initialize Funding Analyzer.

        Args:
            gemini_api_key: Google Gemini API key
            use_simulation: Whether to use simulated data
        """
        self.client = FundingClient(use_simulation=use_simulation)

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_funding(self, company_name: str) -> Dict:
        """
        Analyze funding data for a company.

        Args:
            company_name: Name of the company

        Returns:
            Dictionary with analyzed funding data
        """
        print(f"      → Fetching funding data for {company_name}")

        # Get raw funding data
        raw_data = self.client.get_funding_data(company_name)

        if not raw_data:
            print(f"      ℹ No funding data found for {company_name}")
            return {
                "company_name": company_name,
                "has_funding_data": False,
                "is_funded": False,
                "latest_round": "Unknown",
                "total_funding": 0,
                "key_investors": [],
                "funding_stage": "Unknown",
                "capital_efficiency": "Unknown"
            }

        # Analyze and enrich the data
        funding_stage = self._determine_funding_stage(raw_data)
        capital_efficiency = self._assess_capital_efficiency(raw_data)

        return {
            "company_name": company_name,
            "has_funding_data": True,
            "is_funded": raw_data.get("is_funded", False),
            "latest_round": raw_data["latest_round"],
            "latest_round_amount": raw_data["latest_round_amount"],
            "total_funding": raw_data["total_funding"],
            "key_investors": raw_data["key_investors"],
            "date_of_latest_round": raw_data["date_of_latest_round"],
            "previous_rounds": raw_data.get("previous_rounds", []),
            "number_of_rounds": raw_data.get("number_of_rounds", 1),
            "funding_stage": funding_stage,
            "capital_efficiency": capital_efficiency
        }

    def _determine_funding_stage(self, funding_data: Dict) -> str:
        """
        Determine funding stage maturity.

        Args:
            funding_data: Raw funding data

        Returns:
            Funding stage description
        """
        latest_round = funding_data.get("latest_round", "Unknown")

        stage_mapping = {
            "Seed": "Early Stage",
            "Series A": "Growth Stage",
            "Series B": "Growth Stage",
            "Series C": "Late Stage",
            "Series D+": "Late Stage"
        }

        return stage_mapping.get(latest_round, "Unknown")

    def _assess_capital_efficiency(self, funding_data: Dict) -> str:
        """
        Assess capital efficiency based on funding rounds.

        Args:
            funding_data: Raw funding data

        Returns:
            Capital efficiency assessment
        """
        num_rounds = funding_data.get("number_of_rounds", 1)
        total_funding = funding_data.get("total_funding", 0)

        # Simple heuristic
        if num_rounds <= 2:
            return "High - Few rounds needed"
        elif num_rounds <= 4:
            return "Moderate - Standard progression"
        else:
            return "Lower - Multiple rounds required"

    def analyze_market_funding_landscape(
        self,
        target_startup: Dict,
        competitors: List[Dict]
    ) -> Dict:
        """
        Analyze overall market funding landscape.

        Args:
            target_startup: Target startup with funding data
            competitors: List of competitors with funding data

        Returns:
            Dictionary with market funding analysis
        """
        print("  → Analyzing market funding landscape with Gemini")

        # Calculate aggregate metrics
        funded_competitors = [c for c in competitors if c.get("funding_data", {}).get("is_funded")]
        total_market_funding = sum(
            c.get("funding_data", {}).get("total_funding", 0)
            for c in funded_competitors
        )

        # Collect all investors
        all_investors = []
        for comp in funded_competitors:
            investors = comp.get("funding_data", {}).get("key_investors", [])
            all_investors.extend(investors)

        # Count investor frequency
        investor_counts = {}
        for investor in all_investors:
            investor_counts[investor] = investor_counts.get(investor, 0) + 1

        # Get most active investors
        most_active_investors = sorted(
            investor_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Prepare data for Gemini analysis
        target_funding = target_startup.get("funding_data", {})
        competitor_funding_summary = [{
            "name": comp.get("name"),
            "total_funding": comp.get("funding_data", {}).get("total_funding", 0),
            "latest_round": comp.get("funding_data", {}).get("latest_round", "Unknown"),
            "key_investors": comp.get("funding_data", {}).get("key_investors", [])
        } for comp in funded_competitors]

        prompt = f"""Analyze this market's funding landscape and provide strategic insights.

TARGET STARTUP FUNDING:
{target_funding}

COMPETITOR FUNDING DATA:
{competitor_funding_summary}

MARKET METRICS:
- Total competitors with funding: {len(funded_competitors)} out of {len(competitors)}
- Total market funding: ${total_market_funding:,}
- Average funding per competitor: ${total_market_funding // max(len(funded_competitors), 1):,}

MOST ACTIVE INVESTORS:
{most_active_investors[:5]}

Provide a JSON object with:

1. market_capital_intensity:
   - level: "Low" / "Medium" / "High" / "Very High"
   - explanation: why this level (string)

2. target_funding_position:
   - relative_position: "Underfunded" / "Appropriately Funded" / "Well Funded" / "Overfunded"
   - implications: what this means strategically (string)

3. most_active_vcs:
   - array of top 5 most active VCs with their investment count

4. funding_concentration:
   - is_concentrated: boolean (true if few VCs dominate)
   - description: explanation (string)

5. whitespace_funding_impact:
   - are_gaps_capitalized: "Yes" / "Partially" / "No"
   - explanation: how funding affects identified market gaps (string)
   - opportunities: array of 2-3 funding-related opportunities (strings)

6. strategic_funding_insights:
   - array of 3-5 key insights about funding landscape (strings)

Be specific and actionable. Focus on investment implications.
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

            import json
            analysis = json.loads(response_text)

            # Add raw metrics
            analysis["total_market_funding"] = total_market_funding
            analysis["funded_competitors_count"] = len(funded_competitors)
            analysis["unfunded_competitors_count"] = len(competitors) - len(funded_competitors)
            analysis["average_competitor_funding"] = total_market_funding // max(len(funded_competitors), 1)

            return analysis

        except Exception as e:
            print(f"  ⚠ Funding landscape analysis failed: {e}")
            return {
                "total_market_funding": total_market_funding,
                "funded_competitors_count": len(funded_competitors),
                "average_competitor_funding": total_market_funding // max(len(funded_competitors), 1),
                "market_capital_intensity": {"level": "Unknown", "explanation": "Analysis failed"},
                "most_active_vcs": [{"name": inv[0], "investment_count": inv[1]} for inv in most_active_investors[:5]],
                "strategic_funding_insights": ["Analysis could not be completed"]
            }
