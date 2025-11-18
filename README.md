# VC Market Research Agent

> Automated market research and competitive analysis tool for venture capital due diligence

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

VC Market Research Agent is a comprehensive market analysis tool that automates the due diligence process for venture capital firms. It analyzes target startups, discovers competitors, identifies market opportunities, and generates investment-ready reports with visual insights.

### Key Features

- **🔍 Intelligent Market Discovery** - Automatically identifies competitors using advanced search capabilities
- **📊 Deep Competitive Analysis** - Extracts and analyzes competitor strengths, weaknesses, and positioning
- **💡 Opportunity Identification** - Discovers market whitespace and untapped opportunities
- **📈 Visual Market Maps** - Creates positioning maps and competitive matrices
- **📄 Investment Reports** - Generates comprehensive markdown reports with executive summaries

## How It Works

```
Startup URL → Analyze Company → Discover Competitors → Deep Analysis → Identify Gaps → Generate Report
```

### Analysis Pipeline

1. **Company Understanding** - Extracts business model, target market, and value proposition
2. **Competitor Discovery** - Finds relevant competitors through intelligent search and verification
3. **Competitive Analysis** - Performs deep dive into each competitor's offerings and positioning
4. **Whitespace Identification** - Analyzes market patterns to identify opportunities
5. **Report Generation** - Creates actionable reports with visualizations

## Installation

### Prerequisites

- Python 3.8 or higher
- Parallel AI API key
- Google Gemini API key

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/vcmarketsearch.git
cd vcmarketsearch
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
PARALLEL_AI_API_KEY=your_parallel_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
MAX_COMPETITORS=10
```

## Usage

### Basic Usage

```bash
python main.py https://example-startup.com
```

### Advanced Options

```bash
# Specify company name
python main.py https://example-startup.com --name "Example Inc"

# Analyze more competitors
python main.py https://example-startup.com --max-competitors 15

# Skip visualizations (faster)
python main.py https://example-startup.com --skip-viz
```

### Full Command Reference

```bash
python main.py [URL] [OPTIONS]

Arguments:
  URL                   Target startup website URL (required)

Options:
  --name NAME          Company name (optional, auto-detected if not provided)
  --max-competitors N  Maximum competitors to analyze (default: 10)
  --skip-viz           Skip creating visualizations (faster execution)
  -h, --help          Show help message
```

## Output

The tool generates several outputs:

### 1. Market Research Report
**Location:** `reports/company_name_TIMESTAMP.md`

Comprehensive markdown report including:
- Executive summary
- Target company analysis
- Market overview and trends
- Detailed competitor profiles
- Market opportunities and whitespace
- Strategic recommendations

### 2. Visualizations
**Location:** `reports/`

- **Market Map** - Positioning chart showing competitive landscape
- **Competitive Matrix** - Feature comparison heatmap

### 3. Intermediate Data
**Location:** `data/`

JSON files containing raw analysis data:
- `startup_info_TIMESTAMP.json` - Target company data
- `competitors_TIMESTAMP.json` - Discovered competitors
- `competitor_analysis_TIMESTAMP.json` - Detailed competitor insights
- `market_analysis_TIMESTAMP.json` - Market gaps and opportunities

## Project Structure

```
vcmarketsearch/
├── main.py                    # Main orchestrator
├── market_discovery.py        # Competitor discovery engine
├── competitor_analysis.py     # Competitive analysis module
├── report_generator.py        # Report generation
├── visualization.py           # Visual analytics
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── data/                     # Intermediate analysis data
└── reports/                  # Generated reports and visualizations
```

## Technology Stack

- **Python 3.8+** - Core language
- **Parallel AI API** - Web search and data extraction
- **Google Gemini** - Natural language processing and analysis
- **Matplotlib & Seaborn** - Data visualization
- **Pandas & NumPy** - Data processing

## Use Cases

### For Venture Capital Firms
- Accelerate due diligence process
- Identify market opportunities before investing
- Understand competitive dynamics
- Generate LP reports and investment memos

### For Startup Founders
- Analyze competitive landscape
- Identify market positioning opportunities
- Prepare for investor meetings
- Track competitor movements

### For Market Researchers
- Rapid market analysis
- Competitive intelligence gathering
- Trend identification
- Strategic planning support

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PARALLEL_AI_API_KEY` | Parallel AI API key | Yes | - |
| `GEMINI_API_KEY` | Google Gemini API key | Yes | - |
| `MAX_COMPETITORS` | Default max competitors | No | 10 |
| `SEARCH_MAX_RESULTS` | Max search results per query | No | 5 |

### API Keys

- **Parallel AI**: Sign up at [parallel.ai](https://parallel.ai)
- **Gemini**: Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Performance

Typical analysis time for 10 competitors: **5-8 minutes**

Breakdown:
- Target analysis: ~30 seconds
- Competitor discovery: ~1-2 minutes
- Competitor analysis: ~3-5 minutes (depends on number)
- Market analysis: ~30 seconds
- Report generation: ~20 seconds

## Best Practices

1. **URL Selection** - Use the main company homepage, not product pages
2. **Competitor Count** - Start with 8-10 for balanced depth vs breadth
3. **API Rate Limits** - The tool includes rate limiting to respect API quotas
4. **Result Review** - Always review generated reports for accuracy
5. **Customization** - Modify prompts in source files for domain-specific analysis

## Troubleshooting

### Common Issues

**"No competitors found"**
- Try broader keywords in the target company description
- Increase `MAX_COMPETITORS` in `.env`
- Verify the company category is specific enough

**"API rate limit exceeded"**
- Wait a few minutes and retry
- Consider upgrading API plan
- Reduce `max_competitors` parameter

**"Failed to extract data"**
- Check if website is accessible
- Some sites block automated access
- Try an alternative URL for the company

## Roadmap

- [ ] Support for additional data sources (Crunchbase, PitchBook)
- [ ] Multi-language support for international markets
- [ ] Real-time market tracking and alerts
- [ ] Integration with CRM systems
- [ ] Custom report templates
- [ ] API endpoint for programmatic access

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/vcmarketsearch.git
cd vcmarketsearch
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests (if available)
pytest

# Code style
black .
flake8 .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built with:
- [Parallel AI](https://parallel.ai) for intelligent web search and extraction
- [Google Gemini](https://deepmind.google/technologies/gemini/) for natural language understanding
- [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/) for visualizations

## Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

**Note:** This tool is designed for research and due diligence purposes. Always verify findings with additional research and human judgment before making investment decisions.
