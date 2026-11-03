"""Extra analyses for the insights deck: lost sales, restocking, pack sizes, weekday vs weekend.
Reuses the cleaned intervals from analysis.py and writes data2.json."""
import collections, contextlib, datetime, io, json, os, re, statistics

with contextlib.redirect_stdout(io.StringIO()):
    import analysis as A

SCR = A.SCR
IV, info, by, snaps = A.IV, A.info, A.by, A.snaps
D0, D1 = A.D0, A.D1
brand_of, units_p, price = A.brand_of, A.units_p, A.price
dt = lambda t: datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")

# ---------------------------------------------------------------- 1. lost sales
# Expected sales in an out-of-stock half-hour = the product's average sales in
# in-stock half-hours at the same hour of day (only while it was listed).
rate_n = collections.defaultdict(lambda: collections.Counter())
rate_q = collections.defaultdict(lambda: collections.Counter())
oos_h = collections.defaultdict(lambda: collections.Counter())
for d, h, sale, a, b in IV:
    for p, x in a.items():
        if p in sale:
            rate_q[p][h] += sale[p]; rate_n[p][h] += 1
        elif float(x["stock"]) <= 0:
            oos_h[p][h] += 1
lost_u, lost_r = collections.Counter(), collections.Counter()
for p in oos_h:
    for h, n in oos_h[p].items():
        if rate_n[p][h] >= 3:
            q = n * rate_q[p][h] / rate_n[p][h]
            lost_u[p] += q; lost_r[p] += q * price.get(p, 0)
LU, LR = sum(lost_u.values()), sum(lost_r.values())
lost_brand = collections.Counter()
for p, v in lost_r.items():
    lost_brand[brand_of[p]] += v
lost_top = [dict(name=info[p][0], brand=brand_of[p], variant=info[p][2], lost_u=lost_u[p], lost_r=lost_r[p],
                 sold=units_p[p], share=lost_u[p] / (lost_u[p] + units_p[p]) if units_p[p] + lost_u[p] else 0)
            for p, _ in lost_r.most_common(10)]

# ---------------------------------------------------------------- 2. restocking
restock_h = collections.Counter(); restock_units_h = collections.Counter()
restock_store = collections.defaultdict(collections.Counter)
for d, h, sale, a, b in IV:
    for p in a:
        if p in b and a[p]["store_id"] == b[p]["store_id"]:
            up = float(b[p]["stock"]) - float(a[p]["stock"])
            if up >= 2:
                restock_h[h] += 1; restock_units_h[h] += up
                restock_store[a[p]["store_id"]][h] += 1
# stockout episodes: consecutive snapshots of a product at one store at 0 stock
win = [t for t in snaps if D0 <= t[:10] <= D1]
seq = collections.defaultdict(list)
for t in win:
    for p, x in by[t].items():
        seq[(p, x["store_id"])].append((dt(t), float(x["stock"])))
episodes = []  # (pid, store, start, hours, start_hour)
for (p, st), s in seq.items():
    start = None; prev_t = None
    for t, inv in s:
        if prev_t is not None and (t - prev_t).total_seconds() > 3600 * 1.5:
            start = None  # listing gap: we can't see what happened, drop the episode
        if inv <= 0 and start is None:
            start = t
        elif inv > 0 and start is not None:
            episodes.append((p, st, start, (t - start).total_seconds() / 3600, start.hour))
            start = None
        prev_t = t
day_eps = [e for e in episodes if 6 <= e[4] < 23]
buckets = [("< 1 h", 0, 1), ("1–3 h", 1, 3), ("3–6 h", 3, 6), ("6–12 h", 6, 12), ("12 h+", 12, 999)]
dur_b = [sum(1 for e in day_eps if lo <= e[3] < hi) for _, lo, hi in buckets]
top10 = [p for p, _ in units_p.most_common(10)]
dur_top = {}
for p in top10:
    hs = [e[3] for e in day_eps if e[0] == p]
    dur_top[p] = dict(name=info[p][0], variant=info[p][2], brand=brand_of[p], n=len(hs),
                      median=statistics.median(hs) if hs else None)

# ---------------------------------------------------------------- 3. pack sizes
def litres(v):
    return A.litres(v)


def size_band(v):
    if A.is_weight(v):
        return "By weight"
    l = litres(v)
    return "≤ 300 ml" if l <= 0.3 else "400–500 ml" if l <= 0.6 else "1 litre"


band_u = collections.Counter(); band_l = collections.Counter(); band_n = collections.Counter()
for p in price:
    b = size_band(info[p][2]); band_n[b] += 1
    band_u[b] += units_p[p]; band_l[b] += units_p[p] * litres(info[p][2])
# same milk sold as 500 ml and 1 litre (names differ slightly between sizes)
PAIRS = [("Nandini Shubham", "Nandini Shubham", "Nandini Shubham Toned"),
         ("Nandini Toned Milk", "Nandini Toned Milk", "Nandini Toned"),
         ("Amul Taaza Toned Milk", "Amul Taaza Homogenised Toned Milk", "Amul Taaza Toned"),
         ("Amul Gold Full Cream Milk", "Amul Gold Milk", "Amul Gold")]


def find(sub, lo, hi):
    c = [p for p in price if info[p][0].startswith(sub) and lo <= litres(info[p][2]) <= hi]
    return max(c, key=lambda p: units_p[p]) if c else None


pairs = []
for s_name, l_name, label in PAIRS:
    sp, lp = find(s_name, 0.45, 0.5), find(l_name, 1.0, 1.0)
    if sp and lp:
        pairs.append(dict(name=label, brand=brand_of[sp], small_l=units_p[sp] * litres(info[sp][2]),
                          large_l=units_p[lp] * litres(info[lp][2]), small_u=units_p[sp], large_u=units_p[lp],
                          ppl_small=price[sp] / litres(info[sp][2]), ppl_large=price[lp] / litres(info[lp][2])))

# ---------------------------------------------------------------- 4. weekday vs weekend
# 11 Oct onwards only: both stores were visible on similar terms (earlier days are not comparable)
wk = collections.defaultdict(lambda: collections.Counter()); wdays = collections.defaultdict(set)
for d, h, sale, a, b in IV:
    if d < "2026-10-11" or d not in A.FULL_DAYS:
        continue
    kind = "Weekend" if datetime.date.fromisoformat(d).weekday() >= 5 else "Weekday"
    wdays[kind].add(d)
    wk[kind][h] += sum(sale.values())
wk_hour = {k: [wk[k][h] / len(wdays[k]) for h in range(24)] for k in wk}
wk_day = {k: sum(wk[k].values()) / len(wdays[k]) for k in wk}
wk_brand = collections.defaultdict(collections.Counter)
for d, h, sale, a, b in IV:
    if d < "2026-10-11" or d not in A.FULL_DAYS:
        continue
    kind = "Weekend" if datetime.date.fromisoformat(d).weekday() >= 5 else "Weekday"
    for p, q in sale.items():
        wk_brand[kind][brand_of[p]] += q / len(wdays[kind])

out = dict(LU=LU, LR=LR, SOLD_U=A.TOT_U, SOLD_R=A.TOT_R, lost_top=lost_top, lost_brand=dict(lost_brand),
           restock_h=[restock_h[h] for h in range(24)], restock_units_h=[restock_units_h[h] for h in range(24)],
           restock_store={s: [c[h] for h in range(24)] for s, c in restock_store.items()},
           dur_buckets=[b[0] for b in buckets], dur_b=dur_b, n_eps=len(day_eps),
           dur_median=statistics.median([e[3] for e in day_eps]) if day_eps else None,
           dur_top=list(dur_top.values()),
           band_order=["≤ 300 ml", "400–500 ml", "1 litre", "By weight"], band_u=dict(band_u), band_l=dict(band_l), band_n=dict(band_n),
           pairs=pairs, wk_hour=wk_hour, wk_day=wk_day, wk_ndays={k: len(v) for k, v in wdays.items()},
           wk_days={k: sorted(v) for k, v in wdays.items()}, wk_brand={k: dict(v) for k, v in wk_brand.items()})
json.dump(out, open(os.path.join(SCR, "data2.json"), "w"), ensure_ascii=False, default=float)

print("lost packs", round(LU), "lost rev", round(LR), "| sold", round(A.TOT_U), round(A.TOT_R),
      "| lost share of demand %.1f%%" % (100 * LU / (LU + A.TOT_U)))
for z in lost_top: print("  lost", round(z["lost_u"]), round(z["lost_r"]), z["name"][:35], z["variant"], "sold", round(z["sold"]))
print("restocks by hour", [restock_h[h] for h in range(24)])
print("restock by store", {s: sum(c.values()) for s, c in restock_store.items()})
print("daytime stockout episodes", len(day_eps), "median h", out["dur_median"], "buckets", dur_b)
for v in dur_top.values(): print("  ", v["name"][:30], v["variant"], v["n"], v["median"])
print("bands units", dict(band_u), "litres", {k: round(v) for k, v in band_l.items()}, "n", dict(band_n))
for z in pairs: print("  pair", z["name"], round(z["small_l"]), round(z["large_l"]), round(z["ppl_small"]), round(z["ppl_large"]))
print("weekday/weekend per day", {k: round(v) for k, v in wk_day.items()}, out["wk_ndays"], out["wk_days"])
