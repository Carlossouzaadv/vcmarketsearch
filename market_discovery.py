"""
Market Discovery Module
Discovers competitors and analyzes target startup using Parallel AI Search and Gemini.
"""

import os
import json
import time
import requests
import google.generativeai as genai
from typing import Dict, List, Optional


class MarketDiscovery:
    """Discovers market competitors and analyzes target startup."""

    def __init__(self, parallel_api_key: str, gemini_api_key: str):
        """
        Initialize Market Discovery with API keys.

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

    def analyze_startup(self, url: str, name: Optional[str] = None) -> Dict:
        """
        Analyze target startup to understand their business.

        Args:
            url: Startup website URL
            name: Optional company name

        Returns:
            Dictionary with structured startup information
        """
        print(f"  → Extracting information from {url}")

        # Use Parallel AI Extract to get website content
        try:
            response = requests.post(
                f"{self.base_url}/v1beta/extract",
                headers=self.headers,
                json={
                    "urls": [url],
                    "objective": """Extract comprehensive company information:
                    - Company name and tagline
                    - Core product/service offering (be specific about what they actually sell)
                    - Target market and customer segments (B2B/B2C, company size, industries)
                    - Key features, capabilities, and value propositions
                    - Industry category and market positioning
                    - Technology stack or approach (if mentioned)
                    - Pricing model (if available)
                    - Notable customers or case studies""",
                    "excerpts": True,
                    "full_content": True
                },
                timeout=60
            )
            response.raise_for_status()
            extract_data = response.json()

            if not extract_data.get("results"):
                raise ValueError("No extraction results returned")

            content = extract_data["results"][0].get("content", "")

        except Exception as e:
            print(f"  ⚠ Warning: Could not extract from {url}: {e}")
            content = f"Company website: {url}"

        # Use Gemini to structure the information
        print("  → Structuring data with Gemini")

        prompt = f"""Extract and structure information from this website content:

{content[:8000]}

Return a JSON object with these fields:
- name: company name (string)
- tagline: company tagline or one-line description (string)
- description: comprehensive 3-4 sentence description of what they do, who they serve, and their value proposition (string)
- category: specific market category, e.g., "AI-Powered Sales Intelligence", "Cloud Infrastructure Monitoring" (string)
- target_market: detailed description of target customers (string)
- key_features: array of 5-8 main features or capabilities (array of strings)
- keywords: 8-12 highly specific keywords for finding competitors - include product type, technology, industry terms (array of strings)
- pricing_model: pricing approach if mentioned, e.g., "Usage-based", "Per-seat SaaS" (string or "Unknown")
- market_position: their positioning, e.g., "Enterprise-focused", "Developer-first", "SMB-oriented" (string)

Be precise and specific. Focus on actionable details.
Respond ONLY with valid JSON, no markdown formatting."""

        try:
            response = self.gemini_model.generate_content(prompt)
            # Clean response - remove markdown code blocks if present
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            startup_info = json.loads(response_text)

            # Add URL and override name if provided
            startup_info["url"] = url
            if name:
                startup_info["name"] = name

            return startup_info

        except Exception as e:
            print(f"  ⚠ Warning: Could not parse Gemini response: {e}")
            # Return minimal structure
            return {
                "name": name or "Unknown Company",
                "url": url,
                "description": "Company information could not be extracted",
                "category": "Unknown",
                "target_market": "Unknown",
                "key_features": [],
                "keywords": [],
                "pricing_model": "Unknown",
                "market_position": "Unknown"
            }

    def discover_competitors(
        self,
        category: str,
        description: str,
        keywords: List[str],
        company_name: str = "",
        max_competitors: int = 10
    ) -> List[Dict]:
        """
        Discover competitors in the market.

        Args:
            category: Market category
            description: Target company description
            keywords: Keywords for search
            company_name: Name of target company to exclude
            max_competitors: Maximum number of competitors to find

        Returns:
            List of competitor dictionaries with name, website, description
        """
        print(f"  → Searching for {category} competitors")

        # Step 1: Search for relevant articles using Parallel AI
        search_objective = f"""Find authoritative articles and blog posts about {category} products, platforms, and solutions.

Priority sources:
- Product comparison and review articles
- "Best {category} tools" or "Top {category} platforms" lists
- Industry analysis and market landscape reports
- Product launch announcements and case studies

EXCLUDE: General industry news, opinion pieces, job postings, generic overviews without specific product mentions."""

        try:
            search_response = requests.post(
                f"{self.base_url}/v1beta/search",
                headers=self.headers,
                json={
                    "objective": search_objective,
                    "search_queries": keywords[:5],  # Limit queries
                    "max_results": 5,
                    "mode": "one-shot"
                },
                timeout=90
            )
            search_response.raise_for_status()
            search_results = search_response.json()

        except Exception as e:
            print(f"  ⚠ Warning: Search failed: {e}")
            return []

        article_urls = [result["url"] for result in search_results.get("results", [])]

        if not article_urls:
            print("  ⚠ No articles found")
            return []

        print(f"  → Found {len(article_urls)} relevant articles")

        # Step 2: Extract company mentions from articles
        print("  → Extracting competitor names from articles")

        try:
            extract_response = requests.post(
                f"{self.base_url}/v1beta/extract",
                headers=self.headers,
                json={
                    "urls": article_urls,
                    "objective": f"""Extract company names mentioned as products, platforms, or solutions in the {category} space.

For each company found:
- name: exact company name
- description: one-sentence description of what they offer
- website: website URL if explicitly mentioned in the article

Focus on:
- Actual companies offering products/services (not consultancies or agencies)
- Direct competitors in the {category} market
- Companies with clear product offerings

Exclude:
- Blog authors or publishers
- Generic technology mentions (e.g., "Python", "AWS")
- Investors or analysts""",
                    "excerpts": True
                },
                timeout=90
            )
            extract_response.raise_for_status()
            extract_data = extract_response.json()

        except Exception as e:
            print(f"  ⚠ Warning: Extraction failed: {e}")
            return []

        # Combine all extraction results
        combined_content = ""
        for result in extract_data.get("results", []):
            combined_content += result.get("content", "") + "\n\n"

        if not combined_content.strip():
            print("  ⚠ No content extracted from articles")
            return []

        # Step 3: Use Gemini to parse and filter competitors
        print("  → Filtering direct competitors with Gemini")

        prompt = f"""Extract ONLY direct competitors to this company: {description}

ARTICLE CONTENT:
{combined_content[:12000]}

Return a JSON array of competitors. Each competitor should have:
- name: company name (string)
- description: what they do - be specific about their product (string)
- likely_domain: likely website domain, e.g., "example.com" (string, make educated guess based on company name)

STRICT FILTERING RULES:
1. Only include companies with THE SAME product category as: {category}
2. They must be DIRECT competitors (same target market and solution type)
3. Exclude tangentially related companies, infrastructure providers, or general tech platforms
4. Exclude the target company itself: {company_name}
5. Limit to the {max_competitors} most directly competitive companies
6. Only include companies that are clearly described as product/platform providers

Respond ONLY with a valid JSON array, no markdown formatting."""

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

            company_list = json.loads(response_text)

        except Exception as e:
            print(f"  ⚠ Warning: Could not parse competitors: {e}")
            return []

        # Step 4: Verify each competitor has a real website
        print(f"  → Verifying websites for {len(company_list)} potential competitors")

        competitors = []
        seen_domains = set()

        for company in company_list[:max_competitors * 2]:  # Search more than needed
            if len(competitors) >= max_competitors:
                break

            company_name = company.get("name", "")
            likely_domain = company.get("likely_domain", "")

            print(f"    • Checking {company_name}")

            # Search for official website
            search_query = f"{company_name} {likely_domain} official website"

            try:
                website_search = requests.post(
                    f"{self.base_url}/v1beta/search",
                    headers=self.headers,
                    json={
                        "search_queries": [search_query],
                        "max_results": 3,
                        "mode": "agentic"
                    },
                    timeout=30
                )
                website_search.raise_for_status()

                # Find first valid company website
                for result in website_search.json().get("results", []):
                    url = result.get("url", "")
                    domain = url.split("//")[-1].split("/")[0].replace("www.", "")

                    # Skip non-company sites
                    skip_domains = ["linkedin", "crunchbase", "wikipedia", "facebook",
                                  "twitter", "youtube", "github", "producthunt"]
                    if any(skip in domain.lower() for skip in skip_domains):
                        continue

                    if domain not in seen_domains:
                        seen_domains.add(domain)
                        competitors.append({
                            "name": company_name,
                            "website": url,
                            "description": company.get("description", "")
                        })
                        print(f"      ✓ Found: {url}")
                        break

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"      ⚠ Could not verify {company_name}: {e}")
                continue

        print(f"  ✓ Verified {len(competitors)} competitors with real websites")
        return competitors
