"""Compute every metric used in the insights deck and write them to data.json.

Sales are estimated from stock drops of the same product at the same store
between consecutive 30-minute snapshots. Window: 6 Oct-1 Nov 2026 (IST).
"""
import csv, collections, datetime, gzip, json, random, re, statistics, os

SCR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(SCR, "..", "data")
HIST = os.path.join(DATA, "stock_snapshots.csv.gz")
D0, D1 = "2026-10-06", "2026-11-01"  # complete days only; 5 Oct is partial and excluded

rows = list(csv.DictReader(gzip.open(HIST, "rt", encoding="utf-8")))
info = {}
for x in rows:
    info[x["product_id"]] = (x["product_name"], x["brand"], x["variant"])
brand_of = {p: v[1] for p, v in info.items()}

snaps = sorted(set(x["snapshot_time"] for x in rows))
by = collections.defaultdict(dict)
for x in rows:
    by[x["snapshot_time"]][x["product_id"]] = x


def is_weight(v):
    """Pack size is stated by weight (g/kg); these have no defensible per-litre price."""
    return bool(re.search(r"\d\s*(g|kg)$", v.strip()))


def kilograms(v):
    m = re.match(r"(?:(\d+)\s*x\s*)?([\d.]+)\s*(g|kg)", v)
    return int(m.group(1) or 1) * float(m.group(2)) * (0.001 if m.group(3) == "g" else 1.0)


def litres(v):
    """Pack volume in litres; 0 for weight-labelled packs, which are kept out of all litre measures."""
    if is_weight(v):
        return 0.0
    m = re.match(r"(?:(\d+)\s*x\s*)?([\d.]+)\s*(ml|ltr)", v)
    return int(m.group(1) or 1) * float(m.group(2)) * (0.001 if m.group(3) == "ml" else 1.0)


# ---------------------------------------------------------------- completeness
runs = list(csv.DictReader(open(os.path.join(DATA, "snapshot_log.csv"))))
complete = {}
for r in runs:
    if not r["saved_at"]:
        continue
    t = datetime.datetime.strptime(r["saved_at"], "%Y%m%d_%H%M%S")
    tots = [int(v) for v in r["listing_totals"].split("|") if v]
    complete[t] = bool(tots) and int(r["saved"]) >= max(tots)


def is_complete(t):
    dt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    best = min(complete, key=lambda k: abs((k - dt).total_seconds()))
    return complete[best] if abs((best - dt).total_seconds()) < 120 else False


snap_ok = {t: is_complete(t) for t in snaps}

# ---------------------------------------------------------------- intervals
RESETS = []
LATE = []
OUTLIERS = []
CLOSING = []
IV = []  # (day, hour, {pid: units}, {pid: (inv_start, price)}, start_rows, end_rows)
for k in range(1, len(snaps)):
    t0, t1 = snaps[k - 1], snaps[k]
    if not (D0 <= t1[:10] <= D1):
        continue
    a, b = by[t0], by[t1]
    sale = {}
    for p in a:
        if p in b and a[p]["store_id"] == b[p]["store_id"] and float(a[p]["stock"]) > 0:
            sale[p] = max(0.0, float(a[p]["stock"]) - float(b[p]["stock"]))
    # Morning resets: between 04:00 and 06:00 stock is otherwise still, then the main store
    # sets many products to the same displayed value (usually 12). The timing drifts, and the
    # reset can split across two half-hours, so every drop in that window is removed.
    if t0[11:13] in ("04", "05"):
        for store in set(a[p]["store_id"] for p, q in sale.items() if q > 0):
            RESETS.append((t0, store, sum(q for p, q in sale.items() if a[p]["store_id"] == store)))
            for p in list(sale):
                if a[p]["store_id"] == store:
                    sale[p] = 0.0
    # Late resets: on some days the reset comes later, so 2+ products at one store each
    # falling 5+ units to exactly 12 in the same half-hour are removed too.
    for store in set(a[p]["store_id"] for p in sale):
        hit = [p for p, q in sale.items() if a[p]["store_id"] == store and q >= 5 and float(b[p]["stock"]) == 12]
        if len(hit) >= 2:
            LATE.append((t0, store, sum(sale[p] for p in hit)))
            for p in hit:
                sale[p] = 0.0
    # One-off corrections: a single product falling 30+ units in a half-hour (the next
    # largest real drop is 19) is a stock correction, not orders.
    for p, q in list(sale.items()):
        if q >= 30:
            OUTLIERS.append((t0, p, q))
            sale[p] = 0.0
    # Store B leaves the listing around 23:30; in the 23:00-23:30 interval its stock
    # falls across many products at once (avg ~25 units vs 2-4 in other evening slots).
    # These are closing-time adjustments, not orders, so that one interval is removed.
    if "23:00" <= t0[11:16] < "23:30":
        dropped = sum(q for p, q in sale.items() if a[p]["store_id"] == "B")
        if dropped:
            CLOSING.append((t0, dropped))
        for p in list(sale):
            if a[p]["store_id"] == "B":
                sale[p] = 0.0
    IV.append((t1[:10], int(t0[11:13]), sale, a, b))
days = sorted(set(i[0] for i in IV))
N_IV = collections.Counter(i[0] for i in IV)            # half-hour intervals observed per day
FULL_DAYS = [d for d in days if N_IV[d] >= 46]           # 48 possible; first and last days are partial
_win = [t for t in snaps if D0 <= t[:10] <= D1]
FIRST_SNAP, LAST_SNAP = _win[0], _win[-1]
ND = len(IV) / 48                                        # observed days of data (half-hours / 48)
HOUR_DAYS = collections.Counter(i[1] for i in IV)        # half-hours observed per clock hour

price = {}
for x in rows:
    if D0 <= x["snapshot_time"][:10] <= D1:
        price.setdefault(x["product_id"], []).append(float(x["listed_price"]))
price = {p: statistics.median(v) for p, v in price.items()}

units_p = collections.Counter(); rev_p = collections.Counter()
day_store = collections.defaultdict(collections.Counter); day_store_r = collections.defaultdict(collections.Counter)
day_units = collections.Counter(); day_rev = collections.Counter(); day_lit = collections.Counter()
day_brand = collections.defaultdict(collections.Counter)
hour_units = collections.Counter()
for d, h, sale, a, b in IV:
    for p, q in sale.items():
        if q <= 0:
            continue
        pr = float(a[p]["listed_price"])
        units_p[p] += q; rev_p[p] += q * pr
        day_units[d] += q; day_rev[d] += q * pr; day_lit[d] += q * litres(info[p][2])
        day_store[d][a[p]["store_id"]] += q; day_store_r[d][a[p]["store_id"]] += q * pr
        day_brand[d][brand_of[p]] += q
        hour_units[h] += q

TOT_U = sum(units_p.values()); TOT_R = sum(rev_p.values())
TOT_L = sum(units_p[p] * litres(info[p][2]) for p in units_p)

# coverage: usable comparisons per day
cov = collections.Counter()
for d, h, sale, a, b in IV:
    cov[d] += len(sale)

# ---------------------------------------------------------------- brands
brand_u = collections.Counter(); brand_r = collections.Counter(); brand_l = collections.Counter()
for p in units_p:
    brand_u[brand_of[p]] += units_p[p]; brand_r[brand_of[p]] += rev_p[p]
    brand_l[brand_of[p]] += units_p[p] * litres(info[p][2])
brands_by_rev = [b for b, _ in brand_r.most_common()]
brands_by_units = [b for b, _ in brand_u.most_common()]

# ---------------------------------------------------------------- segments
SEGS = ["Value", "Mainstream", "Premium", "Specialty", "Weight"]
SEG_LABEL = {"Value": "Value  (< ₹60/L)", "Mainstream": "Mainstream  (₹60–80/L)",
             "Premium": "Premium  (₹80–150/L)", "Specialty": "Specialty  (₹150+/L)",
             "Weight": "Sold by weight (priced per kg)"}


def seg_of(p):
    if is_weight(info[p][2]):
        return "Weight"
    ppl = price[p] / litres(info[p][2])
    return "Value" if ppl < 60 else "Mainstream" if ppl < 80 else "Premium" if ppl < 150 else "Specialty"


seg = {s: dict(n=0, u=0.0, l=0.0, r=0.0) for s in SEGS}
for p in price:
    s = seg_of(p); seg[s]["n"] += 1
    seg[s]["u"] += units_p[p]; seg[s]["r"] += rev_p[p]; seg[s]["l"] += units_p[p] * litres(info[p][2])
scatter = [dict(ppl=round(price[p] / litres(info[p][2]), 1), lit=round(units_p[p] * litres(info[p][2]), 1),
                name=info[p][0], variant=info[p][2], brand=info[p][1], seg=seg_of(p))
           for p in price if units_p[p] > 0 and not is_weight(info[p][2])]

# ---------------------------------------------------------------- fill rate
# share of listed product-snapshots that were in stock, complete snapshots only
fr_b = collections.defaultdict(lambda: [0, 0]); fr_h = collections.defaultdict(lambda: [0, 0])
fr_p = collections.defaultdict(lambda: [0, 0]); fr_day = collections.defaultdict(lambda: [0, 0])
fr_hw = collections.defaultdict(lambda: [0.0, 0.0])
n_complete = 0
for t in snaps:
    if not (D0 <= t[:10] <= D1) or not snap_ok[t]:
        continue
    n_complete += 1
    h = int(t[11:13])
    for p, x in by[t].items():
        ins = float(x["stock"]) > 0
        for dct, key in ((fr_b, brand_of[p]), (fr_h, h), (fr_p, p), (fr_day, t[:10])):
            dct[key][0] += ins; dct[key][1] += 1
        w = units_p.get(p, 0) + 1  # sales-weighted
        fr_hw[h][0] += w * ins; fr_hw[h][1] += w
fill_overall = sum(v[0] for v in fr_b.values()) / sum(v[1] for v in fr_b.values())
fill_overall_w = sum(v[0] for v in fr_hw.values()) / sum(v[1] for v in fr_hw.values())

# ---------------------------------------------------------------- substitution
random.seed(7)


def day_factors(store_sel, excl):
    tot = collections.Counter()
    for d, h, sale, a, b in IV:
        for p, q in sale.items():
            if p not in excl and store_sel(a[p]["store_id"]):
                tot[d] += q
    # per-interval rate, so partial days are not mistaken for slow days
    rate = {d: tot[d] / N_IV[d] for d in days}
    m = sum(tot.values()) / sum(N_IV[d] for d in days)
    return {d: (rate[d] / m if m else 1) for d in days}


top10 = [p for p, _ in units_p.most_common(10)]


def prod_lift(A, B, ds, F):
    ins = collections.defaultdict(lambda: [0.0, 0.0]); obs = 0.0; ex = []; n = 0
    for d, h, sale, a, b in IV:
        if A not in a or B not in sale:
            continue
        w = ds.count(d)
        if not w:
            continue
        f = F[d]
        if float(a[A]["stock"]) <= 0:
            obs += w * sale[B]; ex.append((h, f, w)); n += w
        else:
            ins[h][0] += w * sale[B]; ins[h][1] += w * f
    e = sum(w * f * ins[h][0] / ins[h][1] for h, f, w in ex if ins[h][1] > 0)
    return obs, e, n


def boot(fn, *args):
    o, e, n = fn(*args, days)
    if e < 5 or n < 10:
        return [round(o, 1), round(e, 1), n, None, None]
    bt = []
    for _ in range(300):
        bo, be, bn = fn(*args, [random.choice(days) for _ in days])
        if be > 0:
            bt.append(bo / be - 1)
    bt.sort()
    return [round(o, 1), round(e, 1), n, round(100 * bt[int(.05 * len(bt))]), round(100 * bt[int(.95 * len(bt)) - 1])]


prod_store = {}
for x in rows:
    prod_store.setdefault(x["product_id"], collections.Counter())[x["store_id"]] += 1
psub = []
for A in top10:
    row = []
    for B in top10:
        if A == B:
            row.append(None); continue
        st = prod_store[B].most_common(1)[0][0]
        F = day_factors(lambda m, st=st: m == st, {A, B})
        row.append(boot(lambda a_, b_, ds, F=F: prod_lift(a_, b_, ds, F), A, B))
    psub.append(row)

# brand substitution, availability adjusted
W = {p: max(1.0, units_p.get(p, 0)) for p in info}
Wb = collections.Counter()
for p in info:
    Wb[brand_of[p]] += W[p]
top_brands = brands_by_units[:10]
BIV = []
for d, h, sale, a, b in IV:
    bs = collections.Counter(); short = {}; av = {}
    for p, q in sale.items():
        bs[brand_of[p]] += q
    for B in top_brands:
        ps = [p for p in a if brand_of[p] == B]
        if ps:
            tw = sum(W[p] for p in ps)
            short[B] = sum(W[p] for p in ps if float(a[p]["stock"]) <= 0) / tw
        av[B] = sum(W[p] for p in sale if brand_of[p] == B) / Wb[B]
    BIV.append((d, h, bs, short, av))
DT = collections.Counter()
for d, h, bs, short, av in BIV:
    for B, v in bs.items():
        DT[(d, B)] += v


def bfac(excl):
    tot = {d: sum(v for (dd, B), v in DT.items() if dd == d and B not in excl) for d in days}
    m = sum(tot.values()) / sum(N_IV[d] for d in days)
    return {d: (tot[d] / N_IV[d]) / m for d in days}


def brand_lift(A, B, ds, F):
    ins = collections.defaultdict(lambda: [0.0, 0.0]); obs = 0.0; ex = []; n = 0
    for d, h, bs, short, av in BIV:
        if A not in short or av[B] <= 0:
            continue
        w = ds.count(d)
        if not w:
            continue
        if short[A] >= 0.3:
            obs += w * bs[B]; ex.append((h, F[d] * av[B], w)); n += w
        else:
            ins[h][0] += w * bs[B]; ins[h][1] += w * F[d] * av[B]
    e = sum(w * f * ins[h][0] / ins[h][1] for h, f, w in ex if ins[h][1] > 0)
    return obs, e, n


bsub = []
for A in top_brands:
    row = []
    for B in top_brands:
        if A == B:
            row.append(None); continue
        F = bfac({A, B})
        row.append(boot(lambda a_, b_, ds, F=F: brand_lift(a_, b_, ds, F), A, B))
    bsub.append(row)
brand_short_hours = {}
for A in top_brands:
    hs = collections.Counter(h for d, h, bs, short, av in BIV if short.get(A, 0) >= 0.3)
    n = sum(hs.values())
    brand_short_hours[A] = round(sum(v for h, v in hs.items() if h < 6) / n, 2) if n else None

prot_ids = [p for p in price if "protein" in info[p][0].lower()]
PROTEIN = dict(n=len(prot_ids), u=sum(units_p[p] for p in prot_ids), r=sum(rev_p[p] for p in prot_ids))
P500 = sum(units_p[p] for p in price if info[p][2] == "500 ml")
out = dict(
    protein=PROTEIN, p500=P500,
    days=days, ND=ND, n_snaps=sum(1 for t in snaps if D0 <= t[:10] <= D1), n_complete=n_complete,
    n_products=len(price), n_brands=len(set(brand_of[p] for p in price)),
    TOT_U=TOT_U, TOT_R=TOT_R, TOT_L=TOT_L,
    day_store={d: dict(day_store[d]) for d in days}, day_store_r={d: dict(day_store_r[d]) for d in days},
    day_units=[day_units[d] for d in days], day_rev=[day_rev[d] for d in days], day_lit=[day_lit[d] for d in days],
    cov=[cov[d] for d in days],
    hour_units=[hour_units[h] / (HOUR_DAYS[h] / 2) if HOUR_DAYS[h] else 0 for h in range(24)],
    full_days=FULL_DAYS, n_iv={d: N_IV[d] for d in days}, first_snap=FIRST_SNAP, last_snap=LAST_SNAP,
    brand_u=brand_u, brand_r=brand_r, brand_l=brand_l, brands_by_rev=brands_by_rev, brands_by_units=brands_by_units,
    day_brand={d: dict(day_brand[d]) for d in days},
    seg=seg, SEGS=SEGS, SEG_LABEL=SEG_LABEL, scatter=scatter,
    top_products=[dict(pid=p, name=info[p][0], brand=info[p][1], variant=info[p][2], units=units_p[p],
                       rev=rev_p[p], price=price[p],
                       ppl=None if is_weight(info[p][2]) else round(price[p] / litres(info[p][2]), 1),
                       ppk=round(price[p] / kilograms(info[p][2]), 1) if is_weight(info[p][2]) else None,
                       fill=round(fr_p[p][0] / fr_p[p][1], 3) if fr_p[p][1] else None) for p in top10],
    fill_overall=fill_overall, fill_overall_w=fill_overall_w,
    fill_brand={b: [v[0], v[1]] for b, v in fr_b.items()},
    fill_hour=[fr_h[h][0] / fr_h[h][1] if fr_h[h][1] else None for h in range(24)],
    fill_hour_w=[fr_hw[h][0] / fr_hw[h][1] if fr_hw[h][1] else None for h in range(24)],
    closing_units=sum(c[1] for c in CLOSING),
    resets=len(RESETS), reset_units=sum(r[2] for r in RESETS), late_units=sum(r[2] for r in LATE),
    outlier_units=sum(o[2] for o in OUTLIERS),
    psub=psub, bsub=bsub, top_brands=top_brands, brand_short_night=brand_short_hours,
)
# ---------------------------------------------------------------- result tables
RES = os.path.join(SCR, "..", "results")
with open(os.path.join(RES, "estimated_sales_by_product.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["product_id", "product_name", "brand", "variant", "est_packs_sold", "est_sales_value_inr"])
    for p, q in units_p.most_common():
        w.writerow([p, info[p][0], info[p][1], info[p][2], round(q), round(rev_p[p])])
with open(os.path.join(RES, "price_segments.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["product_id", "product_name", "brand", "variant", "listed_price_inr", "price_per_litre", "price_per_kg",
                "segment", "est_packs_sold", "est_litres_sold", "est_sales_value_inr"])
    for p in sorted(price, key=lambda p: (SEGS.index(seg_of(p)), -units_p[p])):
        wt = is_weight(info[p][2])
        w.writerow([p, info[p][0], info[p][1], info[p][2], price[p], "" if wt else round(price[p] / litres(info[p][2]), 1),
                    round(price[p] / kilograms(info[p][2]), 1) if wt else "", seg_of(p), round(units_p[p]),
                    round(units_p[p] * litres(info[p][2]), 2), round(rev_p[p])])

json.dump(out, open(os.path.join(SCR, "data.json"), "w"), ensure_ascii=False, default=float)
print("closing drops removed:", len(CLOSING), round(sum(c[1] for c in CLOSING)))
print("resets removed:", len(RESETS), [(r[0][5:16], r[1], r[2]) for r in RESETS], "outliers:", OUTLIERS)
print("late resets removed:", LATE)
print("units", round(TOT_U), "rev", round(TOT_R), "litres", round(TOT_L), "days", ND)
print("complete snapshots", n_complete, "of", out["n_snaps"], "| fill", round(fill_overall, 3), "weighted", round(fill_overall_w, 3))
print("top brands by units", top_brands)
print("brand short share at night", brand_short_hours)
print("fill by brand", {b: round(fr_b[b][0] / fr_b[b][1], 2) for b in top_brands})
