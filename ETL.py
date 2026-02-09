import requests
import time
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient, UpdateOne
from typing import List, Dict, Optional
import os
from pathlib import Path

USERNAME = os.getenv("DANBOORU_USERNAME")
API_KEY = os.getenv("DANBOORU_API_KEY")
BASE_URL = "https://danbooru.donmai.us" 
TAG_QUERY = 'bang_dream!_it\'s_mygo!!!!!' #Replace it with your own tag to query
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'Danbooru' #Replace it with your own database name
COLLECTION_NAME = 'AveMyGO' #Replace it with your own collection name

if not USERNAME or not API_KEY:
    raise RuntimeError(
        "DANBOORU_USERNAME and DANBOORU_API_KEY environment variables must be set."
    )

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI environment variable must be set with your MongoDB connection string."
    )

STATE_FILE = Path(__file__).parent / ".etl_state.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
def get_last_run_timestamp():
    if STATE_FILE.exists():
        try:
            import json
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                return datetime.fromisoformat(state['last_run'])
        except Exception as e:
            logger.warning(f"Error reading state file: {e}")
    return None
    
def save_last_run_timestamp(timestamp: datetime):
    try:
        import json
        state = {'last_run': timestamp.isoformat()}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        logger.info(f"Saved last run timestamp: {timestamp.isoformat()}")
    except Exception as e:
        logger.error(f"Error saving state file: {e}")


def fetch_posts(tags: str, page: Optional[str] = None, limit: int = 200, created_after: Optional[datetime] = None):
    params = {
        "tags": tags,
        "limit": limit
    }
    
    if page:
        params["page"] = page
    
    # Add date filter if provided
    if created_after:
        params["date"] = f">{created_after.strftime('%Y-%m-%d')}"
    
    try:
        response = requests.get(
            f"{BASE_URL}/posts.json",
            params=params,
            auth=(USERNAME, API_KEY),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching posts: {e}")
        raise
        
def fetch_new_posts(tags: str, last_run: Optional[datetime] = None, max_pages: int = 100): #Fetch all new posts since last run
    # If no last_run, default to 24 hours ago
    if last_run is None:
        last_run = datetime.utcnow() - timedelta(days=1)
        logger.info(f"No previous run found, fetching posts from last 24 hours")
    else:
        logger.info(f"Fetching posts created after: {last_run.isoformat()}")
    
    all_posts = []
    page = None
    page_count = 0
    
    while page_count < max_pages:
        try:
            posts = fetch_posts(tags, page=page, created_after=last_run)
            
            if not posts:
                logger.info("No more posts to fetch")
                break
                
            filtered_posts = []
            last_run_naive = last_run.replace(tzinfo=None) if last_run.tzinfo else last_run
            
            for post in posts:
                try:
                    post_created_str = post['created_at'].replace('Z', '+00:00')
                    post_created = datetime.fromisoformat(post_created_str)
                    # Convert to timezone-naive UTC for comparison
                    if post_created.tzinfo:
                        post_created = post_created.replace(tzinfo=None)
                    
                    if post_created > last_run_naive:
                        filtered_posts.append(post)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error parsing post timestamp: {e}")
                    filtered_posts.append(post)
            
            if not filtered_posts:
                logger.info("No new posts in this page, stopping")
                break
            
            all_posts.extend(filtered_posts)
            logger.info(f"Fetched {len(filtered_posts)} new posts (page {page_count + 1})")
            min_id = min(post["id"] for post in posts)
            page = f"b{min_id}"
            page_count += 1
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error fetching page {page_count + 1}: {e}")
            break
    
    logger.info(f"Total new posts fetched: {len(all_posts)}")
    return all_posts


def process_posts(posts: List[Dict]):
    tags_to_split = ['tag_string_general', 'tag_string_character', 'tag_string_copyright', 'tag_string_meta']
    processed = []
    for post in posts:
        try:
            post_copy = post.copy()
            post_copy.pop('tag_string', None)
            
            for tag_field in tags_to_split:
                if tag_field in post_copy and isinstance(post_copy[tag_field], str):
                    # Split by space, filter out empty strings
                    post_copy[tag_field] = [t for t in post_copy[tag_field].split(" ") if t]
            processed.append(post_copy)
        except Exception as e:
            logger.warning(f"Error processing post {post.get('id', 'unknown')}: {e}")
            # Include unprocessed post anyway
            processed.append(post)
    return processed

def normalize_post(post: Dict) -> Dict:
    doc = post.copy()
    doc["_id"] = doc.pop("id")
    return doc
def upsert_posts(posts: List[Dict], collection):
    if not posts:
        logger.info("No posts to upsert")
        return
    operations = []
    for post in posts:
        try:
            doc = normalize_post(post)
            operations.append(
                UpdateOne(
                    {"_id": doc["_id"]},
                    {"$set": doc},
                    upsert=True
                )
            )
        except Exception as e:
            logger.warning(f"Error normalizing post {post.get('id', 'unknown')}: {e}")
    
    if operations:
        try:
            result = collection.bulk_write(operations, ordered=False)
            logger.info(
                f"Upserted {result.upserted_count} new posts, "
                f"updated {result.modified_count} existing posts"
            )
        except Exception as e:
            logger.error(f"Error during bulk write: {e}")
            raise
def run_etl():
    start_time = datetime.utcnow()
    logger.info("Starting daily ETL run")
    try:
        last_run = get_last_run_timestamp()
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        new_posts = fetch_new_posts(TAG_QUERY, last_run=last_run)
        
        if not new_posts:
            logger.info("No new posts found")
            save_last_run_timestamp(start_time)
            return
        
        logger.info("Processing posts...")
        processed_posts = process_posts(new_posts)
        logger.info("Upserting posts to MongoDB...")
        upsert_posts(processed_posts, collection)
        save_last_run_timestamp(start_time)
        logger.info(f"Processed {len(processed_posts)} posts")
        
    except Exception as e:
        logger.error(f"ETL run failed: {e}", exc_info=True)
        raise
    finally:
        try:
            client.close()
        except:
            pass


if __name__ == "__main__":
    run_etl()
