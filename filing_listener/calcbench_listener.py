#!/usr/bin/env python3

import logging
import sys
from pathlib import Path

import calcbench as cb

subscription_name = "talk to Calcbench to get a subscription"

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
    file_exists = Path(output_file_name).exists()
    logger.info(f"Found {filing_data.shape} for {filing.ticker}")
    if filing_data.shape[0] == 0:
        msg = f"Found no data for {filing.ticker} {accession_id}"
        logger.exception(msg)
        # If we didn't find any data there might be something holding up the process on Calcbench's side.  Throw an exception to try again later.
        raise Exception(msg)
    filing_data[columns].to_csv(
    filing_data.to_csv(
        output_file_name,
        index=False,
        header=not file_exists,
        mode="a" if file_exists else "w",
    )


if __name__ == "__main__":
    logger.info("Starting to handle filings")

    cb.handle_filings(
        handler=get_filing_standardized,
        subscription_name=subscription_name,
    )
