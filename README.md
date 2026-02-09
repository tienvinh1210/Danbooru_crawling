# Danbooru Data Pipeline

A Python project for scraping, storing, and displaying images from the Danbooru API. This project includes ETL scripts for incremental data loading and a visualization tool for browsing collected images.

## Project Overview

This project consists of two main components:

1. **ETL Pipeline** (`ETL.py`) - Incrementally fetches new posts from Danbooru API and stores them in MongoDB
2. **Image Display Tool** (`display.py`) - Queries MongoDB and generates an HTML gallery of images

## Components

### 1. ETL Pipeline (`ETL.py`)

An automated ETL (Extract, Transform, Load) script that fetches new posts from the Danbooru API and stores them in MongoDB.

**Features:**
- Incremental loading (only fetches new posts since last run)
- Automatic deduplication using MongoDB upserts
- State tracking via `.etl_state.json`
- Comprehensive error handling and logging
- Rate limiting to respect API constraints

**See [ETL_README.md](ETL_README.md) for detailed documentation.**

### 2. Image Display Tool (`display.py`)

A utility script that queries MongoDB collections and generates an HTML gallery of images based on specified criteria.

#### Functionality

The `display.py` script:

1. **Connects to MongoDB** - Uses the MongoDB connection string from the `MONGO_URI` environment variable and the database name configured at the top of `display.py`
2. **Queries Collection** - Searches for posts matching specified criteria
3. **Fetches Images** - Downloads images from the `file_url` field of each post
4. **Generates HTML Gallery** - Creates an `images.html` file with base64-encoded images displayed in a responsive flexbox grid

#### Usage

```python
from display import displayall

# Display all posts with specific tags and rating from a given collection
displayall('UmiTaki', {
    'tag_string_general': 'holding_hands',
    'rating': 'g',
})
```

#### Function Signature

```python
def displayall(collection: str, query: dict) -> None
```

**Parameters:**
- `collection` (str): Name of the MongoDB collection to query
- `query` (dict): MongoDB query filter (e.g., `{'tag_string_general': 'holding_hands', 'rating': 'g'}`)

**Output:**
- Creates/overwrites `images.html` in the current directory
- HTML file contains a flexbox grid of images (150px height, 5px margin)

#### Example Queries

```python
# Find all posts with "holding_hands" tag and general rating
displayall('AveMyGO', {
    'tag_string_general': 'holding_hands',
    'rating': 'g'
})

# Find posts with specific character
displayall('AveMyGO', {
    'tag_string_character': 'shiina_taki',
    'rating': 'g'
})

# Find posts with multiple criteria
displayall('AveMyGO', {
    'tag_string_general': {'$in': ['solo', '1girl']},
    'rating': 'g',
    'score': {'$gt': 5}  # Posts with score > 5
})
```

#### How It Works

1. **Query Execution**: Executes MongoDB `find()` query on specified collection
2. **Image Download**: For each matching post:
   - Fetches image from `post['file_url']`
   - Converts image to base64 encoding
   - Handles errors gracefully (skips failed downloads)
3. **HTML Generation**: Creates HTML with:
   - Flexbox layout for responsive grid
   - Base64-encoded images embedded directly
   - Each image: 150px height, 5px margin
4. **File Output**: Writes to `images.html` in current directory

#### Notes

- **Network Dependent**: Requires internet connection to fetch images
- **Memory Usage**: Large collections may consume significant memory (all images loaded into HTML)
- **Error Handling**: Silently skips posts with invalid/missing `file_url` or network errors
- **IPython Integration**: Includes IPython display imports (useful for Jupyter notebooks)
- **Timeout**: 30-second timeout per image request

#### Opening the Gallery

After running the script, open `images.html` in any web browser:

```bash
# On Mac/Linux
open images.html

# On Windows
start images.html

# Or just double-click the file
```

## Setup

### Prerequisites

- Python 3.7+
- MongoDB database (local or cloud)
- Danbooru API credentials

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables for MongoDB and Danbooru credentials:

   Set the following environment variables (e.g. in your shell profile, `.env` file, or process manager):

   - `MONGO_URI`: MongoDB connection string (including credentials)
   - `DANBOORU_USERNAME`: Your Danbooru username
   - `DANBOORU_API_KEY`: Your Danbooru API key

   The following values are configured directly in the scripts and can be edited at
   the top of `ETL.py` / `display.py`:

   - `TAG_QUERY`: Tag query for ETL (default: `bang_dream!_it's_mygo!!!!!`)
   - `DB_NAME`: MongoDB database name (default: `Danbooru`)
   - `COLLECTION_NAME`: MongoDB collection name used by ETL and sample `display.py` queries (e.g. `AveMyGO`, `UmiTaki`)

## Project Structure

```
danbooru_crawling/
├── ETL.py              # Main ETL pipeline script
├── display.py          # Image gallery generator
├── fullscrap.ipynb     # Initial scraping notebook
├── requirements.txt    # Python dependencies
├── ETL_README.md      # Detailed ETL documentation
├── README.md          # This file
├── .etl_state.json    # ETL state tracking (auto-generated)
├── etl.log            # ETL execution logs
└── images.html        # Generated image gallery (auto-generated)
```

## Workflow

1. **Initial Data Load**: Run `fullscrap.ipynb` to do a full scrape (one-time)
2. **Daily Updates**: Schedule `ETL.py` to run daily (see ETL_README.md)
3. **Browse Images**: Use `display.py` to generate HTML galleries for viewing

## Dependencies

See `requirements.txt` for full list:
- `requests` - HTTP requests for API and image fetching
- `pymongo` - MongoDB driver
- `IPython` - Optional, for Jupyter notebook integration

## Notes

- The `images.html` file can become very large if many images are included
- Base64 encoding increases file size by ~33% compared to external URLs
- For large collections, consider pagination or filtering before display
- The HTML file is overwritten each time `displayall()` is called

## License

[Add your license here]
