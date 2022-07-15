#!/usr/bin/env python3

"""
The `get_filing_standardized` function will get called every time a new filing is published.

Calcbench pushes messages onto the queue when data is available, typically a few minutes after the SEC publishes the data.

Messages will remain in the queue for seven days, if the listening process goes down you will receive the messages when it is started again.

If the `handle_filing` function throws an error the message will be pushed back on the queue to re-try.

"""

from datetime import datetime
from pathlib import Path


import calcbench as cb


logger = cb.turn_on_logging()

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
    "fiscal_period",
    "ticker",
    "CIK",
    "filing_type",
    "date_downloaded",
]

output_file_name = Path.joinpath(Path.home(), "push_notification_data.csv")


def get_filing_standardized(filing: cb.Filing):
    if not filing.has_standardized_data:
        return
    filing_id = filing.filing_id
    filing_data = cb.standardized(filing_id=filing_id, point_in_time=True)

    if filing_data.empty:
        msg = f"Found no data for {filing.ticker} {filing_id}"
        logger.exception(msg)
        # If we didn't find any data there might be something holding up the process on Calcbench's side.  Throw an exception to try again later.
        raise Exception(msg)
    logger.info(f"Found {filing_data.shape} for {filing.ticker}")
    file_exists = Path(output_file_name).exists()
    filing_data.reset_index()[columns].to_csv(
        output_file_name,
        index=False,
        header=not file_exists,
        mode="a" if file_exists else "w",
    )


if __name__ == "__main__":

    azure_service_bus_subscription = "not a real subscription"
    # talk to Calcbench to get a subscription
    logger.info("Starting to handle filings")

    cb.handle_filings(
        handler=get_filing_standardized,
        subscription_name=azure_service_bus_subscription,
    )