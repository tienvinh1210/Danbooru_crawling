# Daily ETL Script for Danbooru Data

This script fetches new posts from the Danbooru API and loads them into MongoDB, only processing posts that have been created since the last run.

## Features

- **Incremental Loading**: Only fetches new posts since the last run
- **Automatic Deduplication**: Uses MongoDB upsert to prevent duplicates
- **State Tracking**: Tracks last run timestamp in `.etl_state.json`
- **Error Handling**: Comprehensive logging and error handling
- **Rate Limiting**: Respects API rate limits with delays

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make the script executable (optional):
```bash
chmod +x daily_etl.py
```

3. Test the script:
```bash
python daily_etl.py
```

## Configuration

Configuration is now handled via environment variables (to avoid committing
secrets such as API keys and database credentials to source control).

Set the following environment variables before running the script:

- `DANBOORU_USERNAME`: Your Danbooru username 
- `DANBOORU_API_KEY`: Your Danbooru API key 
- `MONGO_URI`: MongoDB connection string, including credentials 

The following values are configured directly in `ETL.py` (near the top of the file)
and can be edited there to suit your use case:

- `TAG_QUERY`: Tag to search for, for instance `bang_dream!_it's_mygo!!!!!`
- `DB_NAME`: MongoDB database name (default: `Danbooru`)
- `COLLECTION_NAME`: MongoDB collection name (default: `AveMyGO`)

## Running Daily

Add to your crontab to run daily at a certain hour, for example 2 AM:
```bash
crontab -e
```

Add this line (replace 2 with whatever time you feel comfortable with):
```
0 2 * * * cd /path/to/danbooru_crawling && /usr/bin/python3 daily_etl.py >> etl.log 2>&1
```


## How It Works

1. **State Tracking**: The script reads `.etl_state.json` to find the last run timestamp
2. **Fetching**: Queries Danbooru API for posts created after the last run
3. **Processing**: Splits tag strings into arrays and removes unnecessary fields
4. **Upserting**: Uses MongoDB bulk upsert to insert new posts or update existing ones
5. **State Update**: Saves the current run timestamp for the next execution

## Logging

The script logs to:
- Console (stdout)
- `etl.log` file

Check logs for:
- Number of posts fetched
- Upsert statistics
- Any errors or warnings

## First Run

On the first run (when `.etl_state.json` doesn't exist), the script will:
- Fetch posts from the last 24 hours
- Create the state file after successful completion

## Troubleshooting

- **No new posts**: This is normal if no new posts were created since last run
- **API errors**: Check your API key and network connection
- **MongoDB errors**: Verify your MongoDB connection string and credentials
- **State file issues**: Delete `.etl_state.json` to reset (will fetch last 24 hours)
