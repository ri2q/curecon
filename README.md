Cisco Umbrella passive DNS subdomain extractor.

## Install
pip install -r requirements.txt

## Usage
python ingest.py                              # today, all subdomains
python ingest.py --target example.com         # today, target only
python ingest.py --date 2024-03-15            # specific date, all
python ingest.py --date 2024-03-15 --target example.com