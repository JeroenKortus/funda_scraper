# Funda Scraper

A simple Funda property scraper using Selenium to monitor new apartment listings in Den Bosch, Netherlands. The scraper automatically opens new listings in your browser and tracks them in a local database.

## Features

- 🔍 **Smart Scraping**: Uses Selenium with JavaScript support to handle modern Funda website
- 🏠 **Property Tracking**: Monitors apartments in Den Bosch under €400k with 65m²+ floor area
- 📊 **Local Database**: Saves listings with timestamps to avoid duplicates
- 🌐 **Auto Browser**: Opens new listings automatically in your default browser
- 📝 **Notion Integration**: Automatically adds new listings to your Notion database
- ⏰ **Scheduling**: Can run continuously with configurable intervals

## Installation

### Prerequisites
- Python 3.9+
- Google Chrome browser
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/JeroenKortus/funda_scraper.git
cd funda_scraper
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Notion Setup (Optional)

To automatically add new listings to Notion:

1. **Create Notion Integration**:
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Name: "Funda Scraper"
   - Copy the "Internal Integration Token"

2. **Create Notion Database**:
   - Create a new page in Notion
   - Add a database with columns:
     - **Street Name** (Title)
     - **URL** (URL)
     - **Found Date** (Date)
     - **Status** (Select) - options: "New", "Viewed", "Interested", "Not Interested"

3. **Share Database**:
   - Click "Share" on the database
   - Invite your integration with "Full access"

4. **Configure Scraper**:
   - Edit `config.py`
   - Add your Notion token and database ID

## Usage

### Single Run
```bash
python run_funda_scraper.py
```

### Continuous Monitoring
Edit the script to change `one_loop = False` for automatic monitoring every 15 minutes.

## Configuration

The scraper is pre-configured for:
- **Location**: Den Bosch (all neighborhoods)
- **Price Range**: €0 - €400,000
- **Property Type**: Apartments
- **Minimum Size**: 65m²
- **Availability**: Available properties only

To modify search criteria, update the `url_list` variable in the script with your own Funda search URL.

## How It Works

1. **Selenium Browser**: Launches headless Chrome to access Funda
2. **JavaScript Rendering**: Waits for page content to load completely
3. **JSON Extraction**: Extracts listing data from Nuxt.js JSON payload
4. **Data Processing**: Parses addresses and URLs
5. **Duplicate Detection**: Compares against local database
6. **Browser Integration**: Opens new listings automatically

## Database

Listings are stored in `listing_database.jsonl` with the following format:
```json
{
  "street_name": "Maassingel 258",
  "url": "/detail/koop/den-bosch/appartement-maassingel-258/43065340/",
  "found_date": "2024-06-18 14:38:20"
}
```

## License
[MIT](https://choosealicense.com/licenses/mit/)