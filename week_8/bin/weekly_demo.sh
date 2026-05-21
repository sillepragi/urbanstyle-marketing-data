#!/bin/sh

# A shell script to further demonstrate automatization possibilities of UrbanStyle sales data pipeline.
# In this particular example, we'll be running the pipeline with last week's Monday as start date
# and last week's Sunday as end date.

# Calculate date range (previous week):
day_of_week=$(date +%u)
monday_current_week=$(date -d "today - $(( day_of_week - 1 )) days" +%Y-%m-%d)
start_date=$(date -d "$monday_current_week - 7 days" +%Y-%m-%d)
end_date=$(date -d "$monday_current_week - 1 day" +%Y-%m-%d)

# The directory where we are at the moment.
current_dir=$(pwd)

# The directory this shell script is located in.
script_dir=$(dirname "$0")

# The project root directory is two directories up from the script directory.
parent_directory=$(dirname "$script_dir")
project_root_dir=$(dirname "$parent_directory")

# Regardless of the outcome, return back to where we started after this script terminates.
trap 'cd "$current_dir"' EXIT

# Go to project root directory:
cd "$project_root_dir" || exit 1

# Activate Python virtual environment.
# Unlike in bash, in sh `source` command does not work. Instead of `source`, we need to use a dot.
. .venv/bin/activate || exit 1

# Create a directory for log files, unless it already exists.
mkdir -p log

# Enables logging of further shell commands.
set -x

# Run pipeline:
python3 week_8/pipeline.py --start-date="$start_date" --end-date="$end_date" >> log/pipeline.log 2>&1
