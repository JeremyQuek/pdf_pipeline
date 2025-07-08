import asyncio
import os
import logging
import asyncio
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 100))
TIMEOUT = float(os.getenv("TIMEOUT", 60))

async def describe_image_task(client: AsyncOpenAI, job_id: str, image_uri: str, image_id: int) -> tuple[int, str, str]:
    """Core image description function without timeout handling"""
    logging.info(f"Starting OpenAI request ID {job_id}:{image_id}...")

    resp = await client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": """You are a pdf extraction machine for slide decks, pitch decks and annual reports for a VC firm
                        For graphs/charts,transform the information in the text into in LLM readable form.
                        For flowcharts, transform the informationn to a way that allows the diagram to be recreated.
                        USE STRICLTLY THE FORMAT
                        [IMAGE TEXT] <actual text> [END TEXT]
                        """
                    },
                    {"type": "input_image", "image_url": image_uri},
                ],
            }
        ],
    )
    logging.info(f"OpenAI request task successfully {job_id}:{image_id}")
    return (image_id, "success", resp.output_text)


async def describe_image_task_handler(client: AsyncOpenAI, job_id: str, image_uri: str, image_id: int, timeout: float = TIMEOUT) -> tuple[int, str, str]:
    """Wrapper that adds timeout and error handling"""
    try:
        return await asyncio.wait_for(
            describe_image_task(client, job_id, image_uri, image_id),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logging.warning(f"Timeout on OpenAI request {job_id}:{image_id}")
        return (image_id, "timeout", "")
    except Exception as e:
        logging.error(f"Error on OpenAI request {job_id}:{image_id}: {e}")
        return (image_id, "failed", "")


async def main_tasks_handler(job_id: str, image_uris: list[tuple[int, str]], concurrency: int = RATE_LIMIT) -> list[tuple[int, str, str]]:
    """Process images in batches with timeout"""
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

    success_count = sum(1 for item in results if item[1] == "success")
    logging.info(f"Executed {success_count}/{len(image_uris)} image tasks successfully")
    return results
