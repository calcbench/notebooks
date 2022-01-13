#!/usr/bin/env python3

'''
The `get_filing_standardized` function will get called every time a new filing is published.

Calcbench pushes messages onto the queue when data is available, typically a few minutes after the SEC publishes the data.

Messages will remain in the queue for seven days, if the listening process goes down you will receive the messages when it is started again.

If the `handle_filing` function throws an error the message will be pushed back on the queue to re-try.

'''

import logging
import sys
from pathlib import Path

import calcbench as cb

SUBSCRIPTION_NAME = "andrew_test"

log_handler = logging.StreamHandler(sys.stdout)
calcbench_logger = logging.getLogger("calcbench")
calcbench_logger.setLevel(logging.INFO)
calcbench_logger.addHandler(log_handler)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# cb.set_credentials("andrew@calcbench.com", "not my real password")

columns = [
    "preliminary",
    "revision_number",
    "period_start",
    "period_end",
    "date_reported",
    "metric",
    "value",
    "calendar_year",
    "calendar_period",
    "fiscal_year",
    "fiscal_period",
    "ticker",
    "CIK",
    "filing_type",
]

output_file_name = Path.joinpath(Path.home(), "push_notification_data.csv")


def get_filing_standardized(filing: cb.Filing):
    if not filing.standardized_XBRL:
        # We only want filings which include XBRL Calcbench standardizes.  This excludes S-1s.
        return
    accession_id = filing.calcbench_id
    filing_data = cb.point_in_time(
        accession_id=accession_id, all_face=True, all_footnotes=True
    )

    logger.info(f"Found {filing_data.shape} for {filing.ticker}")
    if filing_data.shape[0] == 0:
        msg = f"Found no data for {filing.ticker} {accession_id}"
        logger.exception(msg)
        # If we didn't find any data there might be something holding up the process on Calcbench's side.  Throw an exception to try again later.
        raise Exception(msg)
    file_exists = Path(output_file_name).exists()
    filing_data[columns].to_csv(
        output_file_name,
        index=False,
        header=not file_exists,
        mode="a" if file_exists else "w",
    )


if __name__ == "__main__":
    logger.info("Starting to handle filings")

    cb.handle_filings(
        handler=get_filing_standardized,
        subscription_name=SUBSCRIPTION_NAME,
    )