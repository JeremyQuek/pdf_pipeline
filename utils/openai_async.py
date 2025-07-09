import asyncio
import os
import logging
import asyncio
from openai import AsyncOpenAI

PROMPT = """
You are a VLM as part of a PDF parsing pipeline for extracting text and tables and summarising images for RAG and LLM readable formats

1)  For text bodies, extract the text into a markdown format that is readable for LLM and humans.    
                      
2)  For tables, recreate the table structure in markdown using lines and words in a way that is llm readable
    Such as the format below:
        CATEGORY       | BUDGET BREAKDOWN | IMPACT ON BUSINESS  
        -------------- | ---------------- | -------------------  
        MANUFACTURING  | 40%              | Increase production to meet OEM demand  
        SALES         | 27%              | Grow OEM adoption  
        R&D           | 20%              | Expand into multilayer PCB market  
        HIRING        | 13%              | Strengthen sales & financial planning  

3)  For graphs with readable data points, extract the data points into a presentable way.
    Such as the format below:
        Timeline with customer numbers:
        - 2025: 50 customers
        - 2026: 65 customers
        - 2027: 80 customers
        - 2028: 100 customers
        - 2029: 120 customers
        - 2030: 140 customers

4)  For graphs with no data values, or flowcharts with no data values, you must describe in a RAG optimized way 
    Such as the format below:
        TITLE: Bankruptcies by firm size
        TIMEFRAME: CY19-CY25 (projected)
        UNIT: Hundred cases

        DATA_CATEGORIES:
        - Self-employed: Light blue baseline
        - Capital <10M yen: White bars  
        - Capital 10-50M yen: Dark blue bars
        - Capital ≥50M yen: Orange striped bars
        - Total: Green trend line

        KEY_VALUES:
        - CY19: ~7.2 hundred cases total
        - CY21-22: Minimum ~5.0 hundred cases  
        - CY25: Peak ~8.8 hundred cases

        TRENDS:
        - V-shaped recovery pattern CY21-25
        - Mid-sized firms (10-50M yen) drive majority of increase post-CY22
        - Self-employed bankruptcies remain stable
        - Large firm bankruptcies (≥50M yen) minimal throughout

        INTERPRETATION: Japanese bankruptcies declined during CY21-22, then surged 76% by CY25, primarily driven by mid-sized companies.
        This format is better for RAG because it:

WRAP YOUR ENTIRE RESPONSE STRICTLY IN THE FORMAT:
[Page Text] <actual extracted content> [End Page]
"""

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 250))
TIMEOUT = int(os.getenv("TIMEOUT", 60))

async def describe_image_task(client: AsyncOpenAI, job_id: str, image_uri: str, image_id: int) -> tuple[int, str, str]:
    logging.info(f"Starting OpenAI request ID {job_id}:{image_id}...")

    resp = await client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT
                    },
                    {"type": "input_image", "image_url": image_uri},
                ],
            }
        ],
    )
    logging.info(f"OpenAI request task successfully {job_id}:{image_id}")
    return (image_id, "success", resp.output_text, resp.usage)


async def describe_image_task_handler(client: AsyncOpenAI, job_id: str, image_uri: str, image_id: int, timeout: float = TIMEOUT) -> tuple[int, str, str]:
    try:
        return await asyncio.wait_for(
            describe_image_task(client, job_id, image_uri, image_id),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logging.warning(f"Timeout on OpenAI request {job_id}:{image_id}")
        return (image_id, "timeout", "", None)
    except Exception as e:
        logging.error(f"Error on OpenAI request {job_id}:{image_id}: {e}")
        return (image_id, "failed", "", None)


async def main_tasks_handler(job_id: str, image_uris: list[tuple[int, str]], concurrency: int = RATE_LIMIT) -> list[tuple[int, str, str]]:
    results = []
    for i in range(0, len(image_uris), concurrency):
        batch = image_uris[i:min(i + concurrency, len(image_uris))]

        async with AsyncOpenAI(api_key=OPENAI_API_KEY) as client:
            tasks = [
                describe_image_task_handler(client, job_id, image_uri, image_id)
                for (image_id, image_uri) in batch
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

    cost=0
    for res in results:
        if res[3]:
            cost += float(res[3].input_tokens) * 2.00 / 1000000
            cost += float(res[3].output_tokens) * 8.00 / 1000000
    logging.info(f"Total cost: {cost}")

    success_count = sum(1 for item in results if item[1] == "success")
    logging.info(f"Executed {success_count}/{len(image_uris)} image tasks successfully")
    return results


















PROMPT2 = """You are a pdf extraction machine for slide decks, pitch decks and annual reports for a VC firm
                        For graphs/charts,transform the information in the text into in LLM readable form.
                        For flowcharts, transform the informationn to a way that allows the diagram to be recreated.
                        USE STRICLTLY THE FORMAT
                        [IMAGE TEXT] <actual text> [END TEXT]
                        """