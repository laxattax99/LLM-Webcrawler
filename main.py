import os
import json
import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
from typing import Dict

# Define the schema for the data you want to extract


class NBAGame(BaseModel):
    away_team: str = Field(..., description="Name of the away team")
    home_team: str = Field(..., description="name of the home team")
    # name: str = Field(..., description="name of the team.")
    # location: str = Field(..., description="Location of the game.")

async def extract_structured_data_using_llm(
    provider: str, api_token: str = None, extra_headers: Dict[str, str] = None
):
    print(f"\n--- Extracting Structured Data with {provider} ---")

    # Configure the browser for crawling
    browser_config = BrowserConfig(headless=True)
    simple_run = CrawlerRunConfig(cache_mode=CacheMode.ENABLED,
                                  word_count_threshold=1,
                                  page_timeout=80000,
                                  verbose=True)

    # Additional arguments for the LLM
    extra_args = {"temperature": 0, "max_tokens": 2000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers
    

    llm_strat = LLMExtractionStrategy(
            provider=provider,
            api_token=api_token,  # No token needed for Ollama
            schema=NBAGame.model_json_schema(),
            extraction_type="schema",
            instruction="""Extract the NBA games from the page. The data should include the away team and the home team.""",
            extra_args=extra_args,
            chunk_token_threshold=800,
            apply_chunking=True,
            input_format="html",
        )

    # Configure the crawler with LLM extraction strategy
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        process_iframes=False,
        word_count_threshold=1,
        page_timeout=80000,
        extraction_strategy=llm_strat,
        remove_overlay_elements=True,
        excluded_tags=["form", "header", "footer", "nav"],
    )
    
    schema = {
        "name" : "NBA Game",
        "baseSelector": "tr.Table__TR",
        "fields": [
            {"name": "team1", "selector": 'a', "type": "text"},
            {"name": "team2", "selector": 'a', "type": "text"},
        ]
    }
    
    extraction = JsonCssExtractionStrategy(schema)
    
    no_llm_config = CrawlerRunConfig(
        extraction_strategy=extraction,
        cache_mode=CacheMode.BYPASS,
        process_iframes=False,
    )
        


    # Run the crawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.espn.com/nba/schedule", config=no_llm_config
        )
        print(result.extracted_content)
        # write the result to a file
        # with open("output.txt", "w") as f:
        #     f.write(result.html)


    # async with AsyncWebCrawler(verbose=True) as crawler:
    #     # 4. Run the crawl and extraction
    #     result = await crawler.arun(
    #         url="https://www.cbssports.com/nba/schedule/",

    #         config=config
    #     )

    #     if not result.success:
    #         print("Crawl failed:", result.error_message)
    #         return

    #     # 5. Parse the extracted JSON
    #     data = json.loads(result.extracted_content)
    #     print(f"Extracted {len(data)} coin entries")
    #     print(json.dumps(data[0], indent=2) if data else "No data found")

if __name__ == "__main__":
    # Use Ollama with DeepSeek
    asyncio.run(
        extract_structured_data_using_llm(
            provider="ollama/deepseek-r1:14b", api_token="no-token"
        )
    )