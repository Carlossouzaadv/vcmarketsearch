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
from urllib.parse import urlparse


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
        # FindAll uses separate endpoint and doesn't need beta header
        self.findall_headers = {
            "x-api-key": parallel_api_key,
            "Content-Type": "application/json"
        }

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def _extract_with_jina_reader(self, url: str) -> str:
        """
        Fallback extraction using Jina AI Reader API.
        Free service that converts any URL to clean, LLM-friendly text.

        Args:
            url: Website URL to extract

        Returns:
            Extracted text content
        """
        try:
            # Jina Reader API: prepend r.jina.ai/ to any URL
            jina_url = f"https://r.jina.ai/{url}"
            print(f"  → Trying Jina AI Reader fallback...")

            response = requests.get(
                jina_url,
                headers={
                    "Accept": "text/plain",
                    "X-Timeout": "30"
                },
                timeout=45
            )
            response.raise_for_status()

            content = response.text.strip()
            if len(content) > 100:  # Reasonable minimum
                print(f"  ✓ Jina Reader extracted {len(content)} characters")
                return content
            else:
                print(f"  ⚠ Jina Reader returned insufficient content")
                return ""

        except Exception as e:
            print(f"  ⚠ Jina Reader failed: {e}")
            return ""

    def _extract_with_direct_fetch(self, url: str) -> str:
        """
        Direct HTTP fetch fallback.
        Simple GET request to extract basic text.

        Args:
            url: Website URL to extract

        Returns:
            Raw HTML or text content
        """
        try:
            print(f"  → Trying direct HTTP fetch fallback...")

            response = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; VCMarketResearch/1.0; +http://vcresearch.bot)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"
                },
                timeout=30,
                allow_redirects=True
            )
            response.raise_for_status()

            content = response.text.strip()
            if len(content) > 100:
                print(f"  ✓ Direct fetch got {len(content)} characters")
                return content
            else:
                print(f"  ⚠ Direct fetch returned insufficient content")
                return ""

        except Exception as e:
            print(f"  ⚠ Direct fetch failed: {e}")
            return ""

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

        # Try extraction with multiple fallback methods
        content = ""
        extraction_method = "None"

        # Method 1: Parallel AI Extract (primary)
        try:
            print(f"  → Method 1: Parallel AI Extract...")
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

            if extract_data.get("results"):
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

                # Check if content is sufficient (at least 200 chars of actual content)
                if len(content.strip()) >= 200:
                    extraction_method = "Parallel AI Extract"
                    print(f"  ✓ Parallel AI Extract successful")
                else:
                    print(f"  ⚠ Parallel AI content too short ({len(content)} chars), trying fallbacks...")
                    content = ""

        except Exception as e:
            print(f"  ⚠ Parallel AI Extract failed: {e}")

        # Method 2: Jina AI Reader (fallback 1)
        if not content:
            content = self._extract_with_jina_reader(url)
            if content:
                extraction_method = "Jina AI Reader"

        # Method 3: Direct HTTP fetch (fallback 2)
        if not content:
            content = self._extract_with_direct_fetch(url)
            if content:
                extraction_method = "Direct HTTP Fetch"

        # Method 4: URL-based inference (last resort)
        if not content:
            print(f"  ⚠ All extraction methods failed, using URL-based inference")
            domain = urlparse(url).netloc.replace("www.", "")
            content = f"""Company website: {url}
Domain: {domain}

This is a minimal fallback. Please make educated guesses based on the domain name."""
            extraction_method = "URL Inference (Fallback)"

        print(f"\n  ℹ Final extraction method used: {extraction_method}\n")

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
        max_competitors: int,
        geographic_focus: str = "Global"
    ) -> List[Dict]:
        """
        Discover competitors using Parallel AI FindAll API.
        More reliable than search+extract approach.
        """
        # Build geographic filter based on user selection
        geographic_filter = ""
        geographic_priority = ""
        if geographic_focus != "Global":
            # Determine specific language based on region
            if geographic_focus == "Brazil":
                geographic_filter = f"\n- CRITICAL: ONLY include companies headquartered in BRAZIL or companies that EXCLUSIVELY serve the Brazilian market"
                geographic_priority = f"\n- PRIORITIZE: Brazilian companies (companies with .br domains, Portuguese websites, or based in Brazilian cities like São Paulo, Rio de Janeiro, Brasília, etc.)"
            elif geographic_focus == "United States":
                geographic_filter = f"\n- CRITICAL: ONLY include companies headquartered in the UNITED STATES or companies that EXCLUSIVELY serve the US market"
                geographic_priority = f"\n- PRIORITIZE: US companies (companies with .com/.us domains or based in US cities)"
            elif geographic_focus in ["United Kingdom", "Germany", "France", "Spain", "Italy"]:
                geographic_filter = f"\n- CRITICAL: ONLY include companies headquartered in {geographic_focus.upper()} or companies that EXCLUSIVELY serve the {geographic_focus} market"
                geographic_priority = f"\n- PRIORITIZE: {geographic_focus} companies (local domains, local language websites, based in {geographic_focus} cities)"
            else:
                geographic_filter = f"\n- CRITICAL: ONLY include companies based in or primarily targeting {geographic_focus.upper()}"
                geographic_priority = f"\n- PRIORITIZE: {geographic_focus} companies over international/global companies"

        # Step 1: Create natural language query for FindAll
        findall_query = f"""Find companies that are direct competitors in the {category} space.

Target company description: {description}
Exclude: {company_name}

Requirements:
- Companies must offer {category} products or services
- Must be active, real companies (not concepts or ideas)
- Must have a public website{geographic_filter}{geographic_priority}
- Include company name, website URL, and brief description

Find approximately {max_competitors} companies."""

        print(f"  → Ingesting FindAll query...")

        # DEBUG: Print query being sent
        print(f"\n  🔍 DEBUG: FindAll Ingest Request:")
        print(f"  → Endpoint: {self.base_url}/v1beta/findall/ingest")
        print(f"  → Headers: {self.headers}")
        print(f"  → Query (first 500 chars): {findall_query[:500]}...\n")

        # Step 2: Ingest query to create structured spec
        try:
            ingest_response = requests.post(
                f"{self.base_url}/v1beta/findall/ingest",
                headers=self.findall_headers,
                json={"query": findall_query},
                timeout=30
            )

            # DEBUG: Print response details
            print(f"  🔍 DEBUG: FindAll Ingest Response:")
            print(f"  → Status Code: {ingest_response.status_code}")
            print(f"  → Response Headers: {dict(ingest_response.headers)}")

            ingest_response.raise_for_status()
            ingest_data = ingest_response.json()

            # DEBUG: Print full response
            print(f"  → Response JSON:")
            print(f"     {json.dumps(ingest_data, indent=2)[:2000]}")
            print(f"  → Response keys: {list(ingest_data.keys())}")

            # Try multiple possible field names for spec_id
            spec_id = (
                ingest_data.get("spec_id") or
                ingest_data.get("id") or
                ingest_data.get("specification_id") or
                ingest_data.get("spec", {}).get("id") if isinstance(ingest_data.get("spec"), dict) else None
            )

            if not spec_id:
                print(f"  ⚠ No spec_id returned from FindAll ingest")
                print(f"  → Available fields in response: {list(ingest_data.keys())}")
                print(f"  → Full response: {json.dumps(ingest_data, indent=2)}\n")
                # Check if schema was returned instead (common issue)
                if "schema" in ingest_data:
                    print(f"  ℹ API returned schema instead of spec_id - this suggests the API might need different headers or endpoint")
                return []

            print(f"  ✓ Got spec_id: {spec_id}")
            print(f"  → Running FindAll search (spec: {spec_id[:8] if len(str(spec_id)) > 8 else spec_id}...)\n")

        except requests.exceptions.HTTPError as e:
            print(f"  ⚠ FindAll ingest HTTP error: {e}")
            print(f"  → Response status: {ingest_response.status_code}")
            print(f"  → Response body: {ingest_response.text[:1000]}")
            return []
        except Exception as e:
            print(f"  ⚠ FindAll ingest failed: {e}")
            print(f"  → Error type: {type(e).__name__}")
            return []

        # Step 3: Execute the FindAll run
        try:
            print(f"  🔍 DEBUG: FindAll Run Request:")
            print(f"  → Endpoint: {self.base_url}/v1beta/findall/runs")
            print(f"  → spec_id: {spec_id}")
            print(f"  → max_results: {max_competitors * 2}\n")

            run_response = requests.post(
                f"{self.base_url}/v1beta/findall/runs",
                headers=self.findall_headers,
                json={
                    "spec_id": spec_id,
                    "max_results": max_competitors * 2  # Get more than needed for filtering
                },
                timeout=120  # FindAll can take longer
            )

            print(f"  🔍 DEBUG: FindAll Run Response:")
            print(f"  → Status Code: {run_response.status_code}")

            run_response.raise_for_status()
            run_data = run_response.json()

            print(f"  → Response keys: {list(run_data.keys())}")
            print(f"  → Response (first 1500 chars): {json.dumps(run_data, indent=2)[:1500]}...\n")

            results = run_data.get("results", []) or run_data.get("entities", [])

            if not results:
                print(f"  ⚠ FindAll returned no results")
                print(f"  → Available fields: {list(run_data.keys())}")
                return []

            print(f"  ✓ FindAll discovered {len(results)} potential competitors")

        except requests.exceptions.HTTPError as e:
            print(f"  ⚠ FindAll run HTTP error: {e}")
            print(f"  → Response status: {run_response.status_code}")
            print(f"  → Response body: {run_response.text[:1000]}")
            return []
        except Exception as e:
            print(f"  ⚠ FindAll run failed: {e}")
            print(f"  → Error type: {type(e).__name__}")
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
        max_competitors: int = 10,
        geographic_focus: str = "Global"
    ) -> List[Dict]:
        """
        Discover competitors in the market using Parallel AI FindAll API.

        Args:
            category: Market category
            description: Target company description
            keywords: Keywords for search
            company_name: Name of target company to exclude
            max_competitors: Maximum number of competitors to find
            geographic_focus: Geographic market focus (e.g., "Brazil", "United States", "Global")

        Returns:
            List of competitor dictionaries with name, website, description
        """
        # NOTE: FindAll API currently returns only schema without spec_id
        # Using Search+Extract which works reliably
        print(f"  → Discovering {category} competitors with Search+Extract API ({geographic_focus} focus)")

        # Build geographic context based on user selection
        geographic_context = ""
        geographic_search_terms = ""
        if geographic_focus != "Global":
            if geographic_focus == "Brazil":
                geographic_context = f" CRITICAL: Focus EXCLUSIVELY on companies operating in BRAZIL or serving Brazilian customers. Look for articles about Brazilian {category} companies, Portuguese-language sources, and Brazil-specific market analyses."
                geographic_search_terms = f" Include search terms: 'Brasil', 'Brazilian', 'português', '.br'"
            elif geographic_focus == "United States":
                geographic_context = f" CRITICAL: Focus EXCLUSIVELY on companies headquartered in the UNITED STATES. Exclude international and non-US companies."
                geographic_search_terms = f" Include search terms: 'USA', 'US-based', 'American'"
            else:
                geographic_context = f" CRITICAL: Focus EXCLUSIVELY on companies operating in {geographic_focus} or primarily targeting the {geographic_focus} market."
                geographic_search_terms = f" Include '{geographic_focus}' in search terms"

        # Step 1: Search for relevant articles using Parallel AI
        search_objective = f"""Find authoritative articles and blog posts about {category} products, platforms, and solutions.{geographic_context}{geographic_search_terms}

Priority sources:
- Product comparison and review articles
- "Best {category} tools" or "Top {category} platforms" lists
- Industry analysis and market landscape reports
- Product launch announcements and case studies

EXCLUDE: General industry news, opinion pieces, job postings, generic overviews without specific product mentions."""

        # Build better search queries based on geographic focus
        enhanced_keywords = list(keywords[:3])  # Start with first 3 keywords
        if geographic_focus == "Brazil":
            # Add Brazilian-specific search terms
            enhanced_keywords.extend([
                f"{category} Brasil",
                f"empresas {category.split()[0].lower()} brasileiras",
                f"startups {category.split()[0].lower()} Brasil"
            ])
        elif geographic_focus != "Global":
            enhanced_keywords.append(f"{category} {geographic_focus}")

        try:
            search_response = requests.post(
                f"{self.base_url}/v1beta/search",
                headers=self.headers,
                json={
                    "objective": search_objective,
                    "search_queries": enhanced_keywords[:7],  # Use enhanced queries
                    "max_results": 10,  # Increase to find more sources
                    "excerpts": {
                        "max_chars_per_result": 5000
                    }
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

        # Add geographic filtering to Gemini prompt
        geographic_filter_rule = ""
        if geographic_focus != "Global":
            if geographic_focus == "Brazil":
                geographic_filter_rule = f"\n7. GEOGRAPHIC REQUIREMENT: CRITICAL - ONLY include companies that are HEADQUARTERED in BRAZIL or EXCLUSIVELY serve Brazilian customers. REJECT all US, European, and other international companies. Look for .br domains, Portuguese language websites, Brazilian cities (São Paulo, Rio, etc)."
            elif geographic_focus == "United States":
                geographic_filter_rule = f"\n7. GEOGRAPHIC REQUIREMENT: CRITICAL - ONLY include companies HEADQUARTERED in the UNITED STATES. REJECT all non-US companies."
            else:
                geographic_filter_rule = f"\n7. GEOGRAPHIC REQUIREMENT: CRITICAL - ONLY include companies based in {geographic_focus} or exclusively targeting the {geographic_focus} market. REJECT companies from other regions."

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
6. Only include companies that are clearly described as product/platform providers{geographic_filter_rule}

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
                        "excerpts": {
                            "max_chars_per_result": 1000
                        }
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
