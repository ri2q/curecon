import argparse
import csv
import io
import sys
import zipfile
from datetime import date
from pathlib import Path
 
import requests

# config 
BASE_URL = "https://s3-us-west-1.amazonaws.com/umbrella-static"
#BASE_URL = "https://localhost/umbrella-static"
CURRENT_URL = f"{BASE_URL}/top-1m.csv.zip"
DATED_URL = f"{BASE_URL}/top-1m-{{date}}.csv.zip"


# Download and Parse
def download(date_str: str | None = None) -> list[tuple]:
    """Download the CSV zip and return list of (rank, fqdn) tuples."""
    if date_str:
        url = DATED_URL.format(date=date_str)
    else:
        url = CURRENT_URL
        date_str = str(date.today())

    try:
        resp = requests.get(url, timeout=60)
        # Check for HTTP errors like 404 or 500
        resp.raise_for_status() 
    except requests.exceptions.ConnectionError:
        print("Connection Failed: The server is down or the URL is incorrect.")
        exit(1)
    except requests.exceptions.Timeout:
        print("The request timed out.")
        exit(1)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        exit(1)
        # return

    print(f"[~] Downloading {url} ...")

    if resp.status_code == 403:
        print(f"[!] 403 – date {date_str} not available (Umbrella keeps ~30 days)")
        return []
    resp.raise_for_status()
 
    fqdns = []
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        with zf.open(zf.namelist()[0]) as f:
            reader = csv.reader(io.TextIOWrapper(f, "utf-8", errors="replace"))
            for row in reader:
                if len(row) >= 2:
                    fqdn = row[1].strip().lower()
                    # only keep actual subdomains (must contain at least one dot)
                    if fqdn and "." in fqdn:
                        fqdns.append(fqdn)
 
    print(f"[+] Parsed {len(fqdns):,} FQDNs")
    return fqdns
 
 
# ── Filter 
 
def filter_by_target(fqdns: list[str], target: str) -> list[str]:
    target = target.lower().strip()
    return [f for f in fqdns if f == target or f.endswith("." + target)]
 
 
# ── Save 
 
def save(path: Path, lines: list[str]):
    unique = sorted(set(lines))
    path.write_text("\n".join(unique) + "\n", encoding="utf-8")
    print(f"[+] Saved {len(unique):,} entries → {path}")
 
 
 
def main():
    parser = argparse.ArgumentParser(
        description="Umbrella Passive DNS – FQDN extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--target", metavar="DOMAIN", help="Filter by root domain")
    parser.add_argument("--date",   metavar="YYYY-MM-DD", help="Use a specific date (default: today)")
    args = parser.parse_args()
 
    date_str = args.date or str(date.today())
 
    # download
    fqdns = download(date_str)
 
    if args.target:
        # filter to target subdomains only
        matches = filter_by_target(fqdns, args.target)
        if not matches:
            print(f"[!] No subdomains found for {args.target}")
            sys.exit(0)
        out = Path(f"cu-{args.target}-{date_str}.txt")
        save(out, matches)
    else:
        # save everything
        out = Path(f"cu-all-{date_str}.txt")
        save(out, fqdns)
 
    print("[✓] Done.")
 
 
if __name__ == "__main__":
    main()
