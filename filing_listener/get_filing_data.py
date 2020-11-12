from datetime import datetime
import logging
import sys
from logging import log
from pathlib import Path
import asyncio

import calcbench as cb
from calcbench.filing import Filing

connection_string = "Endpoint=sb://calcbench.servicebus.windows.net/;SharedAccessKeyName=public;SharedAccessKey=Cb7VhLR6eJxsurCSPtXQHOJvlkU84CCCx2oB+T/so6Q="
subscription_name = "andrew_test"

log_handler = logging.StreamHandler(sys.stdout)
calcbench_logger = logging.getLogger("calcbench")
calcbench_logger.setLevel(logging.INFO)
calcbench_logger.addHandler(log_handler)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)


cb.enable_backoff()


output_file = Path.joinpath(Path.home(), "push_notification_data.csv")


async def get_filing_standardized(filing: cb.Filing):
    starting_time = datetime.now()
    if filing["filing_type"] != "annualQuarterlyReport":
        return
    accession_id = filing["calcbench_id"]
    filing_data = cb.point_in_time(
        accession_id=accession_id, all_face=True, all_footnotes=True
    )
    file_exists = output_file.exists()
    logger.info(f"Found {filing_data.shape} for {filing.ticker}")
    filing_data.to_csv(
        output_file,
        index=False,
        header=not file_exists,
        mode="a" if file_exists else "w",
    )
    await asyncio.sleep(60)
    done_sleeping = datetime.now()
    one_minute_later = cb.point_in_time(
        accession_id=accession_id, all_face=True, all_footnotes=True
    )
    if not filing_data.equals(one_minute_later):
        logger.error(
            f"difference for {filing.ticker} one minute later {one_minute_later.shape}"
        )
    else:
        logger.info(f"data matches for {filing.ticker}")


async def producer(put_on_queue):
    await cb.listener.handle_filings_async(
        handler=put_on_queue,
        connection_string=connection_string,
        subscription_name=subscription_name,
    )


async def worker(queue: asyncio.Queue):
    while True:
        filing = await queue.get()
        await get_filing_standardized(filing)
        queue.task_done()


async def main():
    queue = asyncio.Queue()

    def put_on_queue(filing: Filing):
        queue.put_nowait(filing)

    tasks = [
        *[asyncio.create_task(worker(queue=queue)) for _ in range(3)],
        asyncio.create_task(producer(put_on_queue)),
    ]

    await queue.join()
    await asyncio.gather(*tasks)


asyncio.run(main())
