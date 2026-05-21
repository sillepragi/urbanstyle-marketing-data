"""
UrbanStyle Sales Data ETL Pipeline.

This script extracts data from Supabase, transforms it into analytics-ready
formats, calculates KPIs, generates reports, and exports visual charts.

Simple command-line usage (in project root directory):
    python3 week_8/pipeline.py

Using custom sale_date range:
    python3 week_8/pipeline.py --start-date=2024-12-01 --end-date=2024-12-31
"""

import logging
import time
import argparse
from datetime import datetime

# Configure application-wide logging format
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

import data_fetcher
import transform
import visualize_export


def main():
    """
    Parse arguments, launch the ETL pipeline execution, track performance, 
    and handle top-level runtime exceptions.
    """
    try:
        logger.info("Parsing command line arguments")
        args = _parse_command_line_arguments()
        logger.info(f"Arguments parsed: {args}")

        start_time = time.time()
        logger.info("Launching pipeline process from main block")
        
        # Unpack argparse Namespace safely as keyword-only arguments
        run_pipeline(**vars(args))
        
        elapsed_seconds = round(time.time() - start_time, 2)
        logger.info(f"Pipeline process finished. Elapsed time: {elapsed_seconds} seconds.")
    except (argparse.ArgumentError, argparse.ArgumentTypeError) as e:
        logger.error(f"Invalid command line arguments: {e}")
    except Exception as e:
        logger.exception(f"Unexpected exception caught in the main block: {e}")


def run_pipeline(*, start_date, end_date):
    """
    Execute the full ETL sequence: Extract, Transform, and Load/Export.
    
    Args:
        start_date (datetime.date or None): Lower bound for sales date filtering.
        end_date (datetime.date or None): Upper bound for sales date filtering.
    """
    try:
        # --- EXTRACT STAGE ---
        _log_etl_stage_event("Starting", "EXTRACT")
        logger.info("Start fetching sales data")
        df_sales = data_fetcher.fetch_sales(start_date, end_date)
        logger.info(f"Finished fetching sales data: (rows, columns) = {df_sales.shape}")

        logger.info("Start fetching customers data")
        df_customers = data_fetcher.fetch_customers()
        logger.info(f"Finished fetching customers data: (rows, columns) = {df_customers.shape}")
        _log_etl_stage_event("Finished", "EXTRACT")

        # --- TRANSFORM STAGE ---
        _log_etl_stage_event("Starting", "TRANSFORM")
        df_sales_clean = transform.clean_data(df_sales)
        df_weekly = transform.calculate_weekly_aggregates(df_sales_clean)
        kpis = transform.calculate_kpis(df_sales_clean)
        merged_df = transform.merge_datasets(df_sales_clean, df_customers)
        _log_etl_stage_event("Finished", "TRANSFORM")

        # --- LOAD & EXPORT STAGE ---
        _log_etl_stage_event("Starting", "LOAD")
        weekly_fig = visualize_export.create_weekly_chart(df_weekly)
        kpi_fig = visualize_export.create_kpi_summary(kpis)

        saved_files = visualize_export.export_results(
            df=merged_df,
            output_dir="output",
            charts={
                "weekly_revenue": weekly_fig,
                "kpi_summary": kpi_fig
            }
        )

        visualize_export.send_success_notification(kpis, saved_files)
        _log_etl_stage_event("Finished", "LOAD")
        
    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")

def _parse_command_line_arguments():
    """
    Parse, configure, and validate command-line arguments.
    
    Returns:
        argparse.Namespace: Container holding start_date and end_date values.
    """
    # Adding usage examples to the help output via epilog
    epilog_examples = (
        "Examples:\n"
        "  Note: The examples below assume that the script is executed from the project root directory.\n\n"
        "  python3 week_8/pipeline.py\n"
        "  python3 week_8/pipeline.py --start-date=2024-12-01 --end-date=2024-12-31"
    )
    
    parser = argparse.ArgumentParser(
        description="UrbanStyle sales data processing pipeline.",
        epilog=epilog_examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        exit_on_error=False
    )
    
    parser.add_argument(
        "--start-date", 
        type=_normalize_date, 
        help="Earliest sale_date (YYYY-MM-DD). Not specified by default."
    )
    
    parser.add_argument(
        "--end-date", 
        type=_normalize_date, 
        help="Latest sale_date (YYYY-MM-DD). Not specified by default."
    )

    # parse_known_args() returns a tuple where only the first element represents the args we're looking for
    # Underscore (_) represents the rest of the tuple which we don't need.
    args, _ = parser.parse_known_args()
    return args

def _normalize_date(date_str):
    """
    Validate string format and cast into a datetime.date object.
    
    Args:
        date_str (str): Input date string from the command line.
        
    Returns:
        datetime.date or None: Normalized date object or None if the input was empty.
    """
    if not date_str or not date_str.strip():
        return None
        
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD.")
    
def _log_etl_stage_event(event, section_name):
    """Log an ETL stage boundary event with a synchronized 100-character banner."""
    msg = f"{'=' * 40} {event}: {section_name} "
    logger.info(msg.ljust(100, "="))

if __name__ == "__main__":
    main()