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
                    "objective": """Extract comprehensive company information from the website homepage:
                    - Exact company name (as shown on the website)
                    - Company tagline or slogan
                    - Core product/service offering (be very specific about what they actually sell)
                    - Target market and customer segments (B2B/B2C, company size, industries, geographic region)
                    - Key features, capabilities, and value propositions
                    - Industry category and market positioning
                    - Technology stack or approach (if mentioned)
                    - Pricing model (if available)
                    - Notable customers or case studies

                    IMPORTANT: Extract the ACTUAL company name from this specific website, not similar companies.""",
                    "excerpts": True,
                    "full_content": True
                },
                timeout=60
            )
            response.raise_for_status()
            extract_data = response.json()

            # DEBUG: Print raw API response
            print(f"\n  🔍 DEBUG: Raw Parallel AI Extract Response:")
            print(f"  → Response keys: {list(extract_data.keys())}")
            if extract_data.get("results"):
                print(f"  → Number of results: {len(extract_data['results'])}")
                result = extract_data["results"][0]
                print(f"  → Result keys: {list(result.keys())}")
            else:
                print(f"  → No results in response!")
            print(f"  → Full response (first 2000 chars):\n{json.dumps(extract_data, indent=2)[:2000]}\n")

            if not extract_data.get("results"):
                raise ValueError("No extraction results returned")

            # Try multiple field names for content
            result = extract_data["results"][0]
            content = (
                result.get("content", "") or
                result.get("extracted_content", "") or
                result.get("text", "") or
                result.get("data", "") or
                str(result.get("excerpts", ""))
            )

            # DEBUG: Print content details
            print(f"  🔍 DEBUG: Extracted Content:")
            print(f"  → Content length: {len(content)} characters")
            print(f"  → Content preview (first 500 chars):")
            print(f"     {content[:500]}")
            print(f"  → Content preview (last 300 chars):")
            print(f"     ...{content[-300:]}\n")

            if not content.strip():
                raise ValueError("Empty content extracted")

        except Exception as e:
            print(f"  ⚠ Warning: Could not extract from {url}: {e}")
            # Fallback: Try to infer from URL
            content = f"Company website: {url}\nPlease analyze based on the URL domain name."

        # Use Gemini to structure the information
        print("  → Structuring data with Gemini")

        # Truncate content for Gemini
        truncated_content = content[:8000]

        print(f"  🔍 DEBUG: Gemini Input:")
        print(f"  → Sending {len(truncated_content)} chars to Gemini")
        print(f"  → Domain from URL: {url.split('//')[1].split('/')[0]}\n")

        prompt = f"""Analyze this website content and extract company information.

WEBSITE URL: {url}
CONTENT:
{truncated_content}

Return a JSON object with these fields:
- name: THE EXACT company name from THIS website (look for logo text, header, title). NOT a similar company! (string)
- tagline: company tagline or slogan from the website (string)
- description: comprehensive 3-4 sentence description of what THISCOMPANY does, who they serve, their value proposition (string)
- category: specific market category, e.g., "AI-Powered Legal Automation", "Cloud Infrastructure Monitoring" (string)
- target_market: detailed description of target customers including GEOGRAPHIC REGION if mentioned (e.g., "Brazilian law firms", "US startups") (string)
- key_features: array of 5-8 main features or capabilities (array of strings)
- keywords: 8-12 highly specific keywords for finding competitors - include product type, technology, industry terms, COUNTRY/REGION if applicable (array of strings)
- pricing_model: pricing approach if mentioned, e.g., "Usage-based", "Per-seat SaaS" (string or "Unknown")
- market_position: their positioning, e.g., "Enterprise-focused", "Developer-first", "SMB-oriented" (string)

CRITICAL: Extract the company name from THIS specific website ({url}), not from any other source!

If content is insufficient, analyze the domain name: {url.split('//')[1].split('/')[0]}

Respond ONLY with valid JSON, no markdown formatting."""

        try:
            response = self.gemini_model.generate_content(prompt)

            # DEBUG: Print Gemini response
            print(f"  🔍 DEBUG: Gemini Raw Response:")
            print(f"  → Response text (first 1000 chars):")
            print(f"     {response.text[:1000]}\n")
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

            # DEBUG: Print final parsed result
            print(f"  🔍 DEBUG: Final Parsed Startup Info:")
            print(f"  → Company Name: {startup_info.get('name', 'N/A')}")
            print(f"  → Category: {startup_info.get('category', 'N/A')}")
            print(f"  → Description (first 200 chars): {str(startup_info.get('description', 'N/A'))[:200]}...\n")

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

    def _discover_with_findall(
        self,
        category: str,
        description: str,
        company_name: str,
        max_competitors: int
    ) -> List[Dict]:
        """
        Discover competitors using Parallel AI FindAll API.
        More reliable than search+extract approach.
        """
        # Detect geographic focus from description
        is_brazilian = any(term in description.lower() for term in ['brazil', 'brasil', 'brazilian', 'brasileiro'])
        is_latam = any(term in description.lower() for term in ['latin america', 'latam', 'américa latina'])

        geographic_filter = ""
        if is_brazilian:
            geographic_filter = "\n- Geographic focus: BRAZIL (Brazilian companies or companies operating in Brazil)"
        elif is_latam:
            geographic_filter = "\n- Geographic focus: Latin America"

        # Step 1: Create natural language query for FindAll
        findall_query = f"""Find companies that are direct competitors in the {category} space.

Target company description: {description}
Exclude: {company_name}

Requirements:
- Companies must offer {category} products or services
- Must be active, real companies (not concepts or ideas)
- Must have a public website{geographic_filter}
- Include company name, website URL, and brief description

Find approximately {max_competitors} companies."""

        print(f"  → Ingesting FindAll query...")

        # Step 2: Ingest query to create structured spec
        try:
            ingest_response = requests.post(
                f"{self.base_url}/v1beta/findall/ingest",
                headers=self.headers,
                json={"query": findall_query},
                timeout=30
            )
            ingest_response.raise_for_status()
            ingest_data = ingest_response.json()
            spec_id = ingest_data.get("spec_id") or ingest_data.get("id")

            if not spec_id:
                print(f"  ⚠ No spec_id returned from FindAll ingest")
                return []

            print(f"  → Running FindAll search (spec: {spec_id[:8]}...)")

        except Exception as e:
            print(f"  ⚠ FindAll ingest failed: {e}")
            return []

        # Step 3: Execute the FindAll run
        try:
            run_response = requests.post(
                f"{self.base_url}/v1beta/findall/runs",
                headers=self.headers,
                json={
                    "spec_id": spec_id,
                    "max_results": max_competitors * 2  # Get more than needed for filtering
                },
                timeout=120  # FindAll can take longer
            )
            run_response.raise_for_status()
            run_data = run_response.json()

            results = run_data.get("results", []) or run_data.get("entities", [])

            if not results:
                print(f"  ⚠ FindAll returned no results")
                return []

            print(f"  ✓ FindAll discovered {len(results)} potential competitors")

        except Exception as e:
            print(f"  ⚠ FindAll run failed: {e}")
            return []

        # Step 4: Parse and structure FindAll results
        competitors = []
        seen_names = set()

        for entity in results[:max_competitors * 2]:
            # Extract fields (FindAll format may vary)
            name = (
                entity.get("name") or
                entity.get("company_name") or
                entity.get("entity_name") or
                ""
            ).strip()

            website = (
                entity.get("website") or
                entity.get("url") or
                entity.get("homepage") or
                ""
            ).strip()

            desc = (
                entity.get("description") or
                entity.get("summary") or
                entity.get("about") or
                ""
            ).strip()

            # Skip if missing essential data or duplicate
            if not name or not website:
                continue

            if name.lower() in seen_names or name.lower() == company_name.lower():
                continue

            # Clean website URL
            if not website.startswith("http"):
                website = f"https://{website}"

            competitors.append({
                "name": name,
                "website": website,
                "description": desc or f"Company in {category} space"
            })

            seen_names.add(name.lower())

            if len(competitors) >= max_competitors:
                break

        print(f"  ✓ Filtered to {len(competitors)} validated competitors")
        return competitors

    def discover_competitors(
        self,
        category: str,
        description: str,
        keywords: List[str],
        company_name: str = "",
        max_competitors: int = 10
    ) -> List[Dict]:
        """
        Discover competitors in the market using Parallel AI FindAll API.

        Args:
            category: Market category
            description: Target company description
            keywords: Keywords for search
            company_name: Name of target company to exclude
            max_competitors: Maximum number of competitors to find

        Returns:
            List of competitor dictionaries with name, website, description
        """
        print(f"  → Using FindAll API to discover {category} competitors")

        # Try FindAll API first (better for this use case)
        try:
            competitors = self._discover_with_findall(
                category, description, company_name, max_competitors
            )
            if competitors:
                return competitors
            print("  ℹ FindAll returned no results, falling back to Search+Extract method")
        except Exception as e:
            print(f"  ℹ FindAll API not available ({e}), using Search+Extract method")

        # Fallback to original search+extract method
        print(f"  → Searching for {category} competitors with Search API")

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

        # Debug: Print API response structure
        print(f"  → Received {len(extract_data.get('results', []))} results from extract API")

        # Combine all extraction results
        combined_content = ""
        for idx, result in enumerate(extract_data.get("results", [])):
            # Try different possible field names
            content = (
                result.get("content", "") or
                result.get("extracted_content", "") or
                result.get("text", "") or
                result.get("data", "") or
                str(result.get("excerpts", ""))
            )
            if content:
                combined_content += content + "\n\n"
                print(f"    ✓ Extracted content from result {idx + 1}")

        if not combined_content.strip():
            print("  ⚠ No content extracted from articles")
            print(f"  → Debug: API returned keys: {list(extract_data.get('results', [{}])[0].keys()) if extract_data.get('results') else 'no results'}")
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
