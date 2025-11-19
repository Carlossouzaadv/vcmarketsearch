"""
Funding Analysis Module
Analyzes funding data, investment rounds, and investor landscape.
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai


class FundingClient:
    """
    Funding data client using Parallel AI Search and Gemini for real data extraction.
    """

    def __init__(self, parallel_api_key: str = None, gemini_api_key: str = None, language: str = "en"):
        """
        Initialize funding client.

        Args:
            parallel_api_key: Parallel AI API key for real data search
            gemini_api_key: Google Gemini API key for parsing search results
            language: Language for analysis ("en" or "pt")
        """
        self.parallel_api_key = parallel_api_key
        self.gemini_api_key = gemini_api_key

        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

        self.parallel_headers = {
            "x-api-key": parallel_api_key if parallel_api_key else "",
            "Content-Type": "application/json",
            "parallel-beta": "search-extract-2025-10-10"
        }
        # Beta header is REQUIRED for Search and Extract APIs per official docs

        # Language support
        self.language = language
        self.lang_instruction = ""
        if language == "pt":
            self.lang_instruction = "\n\nIMPORTANTE: Escreva TODO o conteúdo em PORTUGUÊS BRASILEIRO. Use terminologia de negócios em português."

    def _fetch_real_funding_data(self, company_name: str, company_website: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch real funding data using Parallel AI Search + Gemini.

        Args:
            company_name: Name of the company
            company_website: Optional company website URL for disambiguation

        Returns:
            Dictionary with funding data or None if no reliable data found
        """
        if not self.parallel_api_key or not self.gemini_api_key:
            print(f"      ℹ No API keys configured for real funding data search")
            return None

        try:
            # Search for funding announcements and data
            print(f"      → Searching for funding data: {company_name}")

            # Extract domain from website for better search disambiguation
            domain_term = ""
            if company_website:
                # Extract domain: https://evollux.com.br -> evollux.com.br
                domain = company_website.replace("https://", "").replace("http://", "").split("/")[0]
                domain_term = f" site:{domain}"
                print(f"      → Using domain for disambiguation: {domain}")

            # Build search queries - include domain for disambiguation and Portuguese terms
            # Use domain WITHOUT site: operator (more flexible for API)
            domain_for_search = domain.replace('www.', '') if company_website else ''

            # Build comprehensive search queries including accelerators/incubators
            search_queries = [
                f"{company_name} {domain_for_search} funding round investment",
                f"{company_name} {domain_for_search} raised capital seed series",
                f"{company_name} {domain_for_search} investimento rodada captação",
                f"{company_name} {domain_for_search} aceleradora incubadora programa",
                f'"{company_name}" {domain_for_search} venture capital investor',
                f"{company_name} startup funding Brazil Brasil"
            ]

            # Prepare request payload - ensure all fields are valid
            search_payload = {
                "objective": f"Find news, press releases, announcements, and company profiles mentioning {company_name}'s funding rounds, investment amounts, investors, accelerators, or incubators.",
                "search_queries": search_queries,
                "max_results": 8,  # Increased to find more sources
                "excerpts": {
                    "max_chars_per_result": 15000  # Increased to capture more content
                }
            }

            print(f"      🔍 DEBUG: Funding Search Request:")
            print(f"      → Endpoint: https://api.parallel.ai/v1beta/search")
            print(f"      → Queries: {len(search_queries)} queries")
            print(f"      → Max results: {search_payload['max_results']}")

            search_response = requests.post(
                "https://api.parallel.ai/v1beta/search",
                headers=self.parallel_headers,
                json=search_payload,
                timeout=60
            )

            print(f"      → Response status: {search_response.status_code}")

            # Handle error responses better
            if search_response.status_code == 422:
                print(f"      ⚠ 422 Error - Invalid request format")
                print(f"      → Response: {search_response.text[:500]}")
                return None

            search_response.raise_for_status()
            search_results = search_response.json()

            # DETAILED LOGGING: Show what URLs were found
            print(f"\n      📊 FUNDING SEARCH RESULTS FOR {company_name}:")
            if not search_results.get("results"):
                print(f"      ℹ No funding news found for {company_name}")
                return None

            print(f"      → Found {len(search_results['results'])} articles:")
            for idx, r in enumerate(search_results["results"][:5], 1):
                print(f"         {idx}. {r.get('url', 'N/A')}")
                print(f"            Title: {r.get('title', 'N/A')[:100]}")

            # Filter results to prioritize those mentioning the correct domain
            filtered_results = []
            other_results = []

            for r in search_results["results"]:
                url = r.get("url", "").lower()
                title = r.get("title", "").lower()
                snippet = r.get("snippet", "").lower()

                # Check if result mentions the correct domain (without www)
                if company_website:
                    domain_check = domain_for_search.lower()
                    if domain_check in url or domain_check in title or domain_check in snippet:
                        filtered_results.append(r)
                    else:
                        other_results.append(r)
                else:
                    filtered_results.append(r)

            # Prioritize domain-matching results, but include others as fallback
            prioritized_results = filtered_results + other_results

            if filtered_results:
                print(f"      → {len(filtered_results)} articles mention domain '{domain_for_search}'")
            else:
                print(f"      ⚠ No articles explicitly mention domain '{domain_for_search}' - using all results")

            # Extract funding info from top prioritized results
            article_urls = [r["url"] for r in prioritized_results[:3]]

            print(f"\n      → Extracting from {len(article_urls)} articles")

            extract_payload = {
                "urls": article_urls,
                "objective": f"Extract ALL funding and investment information for {company_name}: funding rounds (Seed, Series A/B/C), amounts raised, investor names, accelerator programs, incubator participation, grants, and dates. Include any mention of financial backing or support programs."
            }

            extract_response = requests.post(
                "https://api.parallel.ai/v1beta/extract",
                headers=self.parallel_headers,
                json=extract_payload,
                timeout=60
            )

            print(f"      → Extract response status: {extract_response.status_code}")

            # Handle 422 errors
            if extract_response.status_code == 422:
                print(f"      ⚠ 422 Error on extract - Invalid request format")
                print(f"      → Response: {extract_response.text[:500]}")
                return None

            extract_response.raise_for_status()
            extract_data = extract_response.json()

            # Combine extracted content
            combined_content = ""
            print(f"      📄 EXTRACTED CONTENT:")
            for idx, result in enumerate(extract_data.get("results", []), 1):
                content = (
                    result.get("content", "") or
                    result.get("extracted_content", "") or
                    str(result.get("excerpts", ""))
                )
                if content:
                    combined_content += content + "\n\n"
                    print(f"         Article {idx}: {len(content)} chars - Preview: {content[:200]}...")
                else:
                    print(f"         Article {idx}: No content extracted")

            if not combined_content.strip():
                print(f"      ℹ No funding content extracted for {company_name}")
                return None

            print(f"      → Total combined content: {len(combined_content)} characters\n")

            # Use Gemini to parse and structure the funding data
            prompt = f"""Extract ALL funding and investment information for the company: {company_name}

CONTENT FROM NEWS ARTICLES:
{combined_content[:15000]}

INSTRUCTIONS:
1. Extract information if you find ANY mentions of:
   - Funding rounds (Seed, Pre-Seed, Series A/B/C, etc.)
   - Investment amounts raised
   - Investor names (VCs, angels, corporate investors)
   - ACCELERATOR programs (e.g., "acelerada pela WOW", "participated in Y Combinator")
   - INCUBATOR participation
   - Grants or government funding
   - Any financial backing or support programs

2. CRITICAL: Only extract if the content CLEARLY mentions {company_name}.
   If content is about a DIFFERENT company with similar name, return null.

3. Return a JSON object:
{{
  "latest_round": "Round name (e.g., Seed, Accelerator, Series A) or program name" or null,
  "latest_amount": amount as integer (use 0 if amount not disclosed) or null,
  "total_funding": total amount raised as integer or null,
  "investors": ["Investor 1", "Accelerator Name", "Incubator Name"] or [],
  "funding_date": "YYYY-MM-DD" or null,
  "rounds": [
    {{"round": "Accelerator/WOW", "amount": 0, "date": "2023-01-15", "investors": ["WOW Aceleradora"]}},
    {{"round": "Seed", "amount": 1000000, "date": "2024-06-20", "investors": ["VC Firm"]}}
  ] or []
}}

4. If NO funding/investment/accelerator data is found for {company_name}, respond with: null{self.lang_instruction}

Respond ONLY with valid JSON (object or null), no markdown."""

            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Check if response is null
            if response_text.lower() == "null":
                print(f"      ℹ No verified funding data found for {company_name}")
                return None

            funding_data = json.loads(response_text)

            # Validate we got meaningful data
            if not funding_data or not funding_data.get("latest_round"):
                print(f"      ℹ No verified funding data found for {company_name}")
                return None

            # Ensure latest_amount is not None for formatting
            latest_amount = funding_data.get('latest_amount') or 0
            print(f"      ✓ Latest: {funding_data.get('latest_round')} - ${latest_amount:,}")
            return funding_data

        except Exception as e:
            print(f"      ⚠ Error fetching real funding data for {company_name}: {e}")
            return None

    def get_funding_data(self, company_name: str, company_website: Optional[str] = None) -> Optional[Dict]:
        """
        Get funding data for a company using real API search.

        Args:
            company_name: Name of the company
            company_website: Optional company website URL for disambiguation

        Returns:
            Dictionary with funding data or None if not found
        """
        return self._fetch_real_funding_data(company_name, company_website)


class FundingAnalyzer:
    """Analyzes funding data and generates insights."""

    def __init__(self, parallel_api_key: str, gemini_api_key: str, language: str = "en"):
        """
        Initialize Funding Analyzer.

        Args:
            parallel_api_key: Parallel AI API key for searching funding data
            gemini_api_key: Google Gemini API key for parsing data
            language: Language for analysis ("en" or "pt")
        """
        self.client = FundingClient(
            parallel_api_key=parallel_api_key,
            gemini_api_key=gemini_api_key,
            language=language
        )

        # Configure Gemini for analysis
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Language support
        self.language = language
        self.lang_instruction = ""
        if language == "pt":
            self.lang_instruction = "\n\nIMPORTANTE: Escreva TODO o conteúdo em PORTUGUÊS BRASILEIRO. Use terminologia de negócios em português."

    def analyze_funding(self, company_name: str, company_website: Optional[str] = None) -> Dict:
        """
        Analyze funding data for a company.

        Args:
            company_name: Name of the company
            company_website: Optional company website URL for disambiguation

        Returns:
            Dictionary with analyzed funding data
        """
        print(f"      → Fetching funding data for {company_name}")

        # Get raw funding data
        raw_data = self.client.get_funding_data(company_name, company_website)

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
            "latest_round": raw_data.get("latest_round", "Unknown"),
            "latest_round_amount": raw_data.get("latest_amount", 0),  # Gemini returns 'latest_amount'
            "total_funding": raw_data.get("total_funding", 0),
            "key_investors": raw_data.get("investors", []),  # Gemini returns 'investors'
            "date_of_latest_round": raw_data.get("funding_date", "Unknown"),  # Gemini returns 'funding_date'
            "previous_rounds": raw_data.get("rounds", []),
            "number_of_rounds": len(raw_data.get("rounds", [])) if raw_data.get("rounds") else 1,
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

Be specific and actionable. Focus on investment implications.{self.lang_instruction}
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
