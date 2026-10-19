"""Weekly snapshot of Harley-Davidson new-motorcycle dealer inventory (US).

Source: the public search endpoint behind harley-davidson.com/us/en/motorcycles/dealer-inventory
(the same requests the site's own inventory page makes). Run once a week from your own machine:

    python hog_dealer_inventory_scraper.py            # writes hog_inventory_<date>.csv and appends hog_inventory_summary.csv

Be polite: one full pass is ~95 requests of 200 rows; the script sleeps between pages.
If the site changes its parameters, open the inventory page in a browser, select a dealer, and copy the
/br/search/ request from the browser's network tab.
"""
import csv, datetime as dt, time, collections
import requests

BASE = "https://www.harley-davidson.com/br/search/"
PARAMS = {
    "request_type": "search", "search_type": "keyword", "domain_key": "harley_davidson_en_new_online",
    "view_id": "en_us", "q": "*", "url": "https://www.harley-davidson.com/us/en/motorcycles/dealer-inventory",
    "fl": "pid,price,year,modelCode,dealerId,dealerName,dealerState,dealerCity,categoryName,vin",
    "sort": "price asc", "rows": 200,
}
HEADERS = {"User-Agent": "Mozilla/5.0 (research; weekly inventory tracker)"}

def fetch_all():
    docs, start = [], 0
    while True:
        p = dict(PARAMS, start=start)
        r = requests.get(BASE, params=p, headers=HEADERS, timeout=30)
        r.raise_for_status()
        j = r.json()
        page = j["response"]["docs"]
        docs.extend(page)
        start += len(page)
        if not page or start >= j["response"]["numFound"]:
            return docs
        time.sleep(1.0)

def main():
    today = dt.date.today().isoformat()
    docs = fetch_all()
    seen, rows = set(), []
    for d in docs:
        if d.get("vin") in seen:
            continue
        seen.add(d.get("vin"))
        rows.append(d)
    with open(f"hog_inventory_{today}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["vin", "year", "modelCode", "categoryName", "dealerId", "dealerName", "dealerState", "dealerCity", "price"], extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    by_state = collections.Counter(r.get("dealerState") for r in rows)
    dealers = len({r.get("dealerId") for r in rows})
    leftovers = sum(1 for r in rows if str(r.get("year")) < str(dt.date.today().year))
    summ = {"date": today, "units": len(rows), "dealers": dealers, "units_per_dealer": round(len(rows) / max(dealers, 1), 1),
            "prior_model_year_units": leftovers, "FL": by_state.get("FL", 0), "TX": by_state.get("TX", 0),
            "CA": by_state.get("CA", 0), "PA": by_state.get("PA", 0), "OH": by_state.get("OH", 0), "WI": by_state.get("WI", 0)}
    new = False
    try:
        open("hog_inventory_summary.csv").close()
    except FileNotFoundError:
        new = True
    with open("hog_inventory_summary.csv", "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summ)); 
        if new: w.writeheader()
        w.writerow(summ)
    print(summ)

if __name__ == "__main__":
    main()
