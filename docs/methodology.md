# Milk on quick commerce: analysis and methodology

**Scope:** packaged milk listings on a leading quick-commerce platform, for one delivery address in HSR Layout, Bengaluru

**Final window:** 6 October–1 November 2026, 27 full days, across all three stores serving that address

## 1. Data

- **Collection:** one snapshot of the milk category listing every 30 minutes. Each row is one product at one store at one time.
- **Excluded:** 5 October, which starts at 22:30, so it is a partial day.
- **Snapshots:** 1,294 in the window, of which 1,117 are complete (products saved ≥ the listing total the platform reports). The other 177 (13.7%) are partial.
- **Health:** a steady 30-minute gap, with two one-hour gaps (27 and 29 October). No duplicate rows and no missing stock or prices.
- **Products:** 105 products from 22 brands were listed at least once.

| Store | Role | Packs |
|---|---|---|
| Store A | Main daytime store | 4,885 |
| Store B | Second daytime store; often hidden from 9 Oct onwards | 1,522 |
| Store C | Listed only at night, until 10 Oct; its stock never changed | 0 |

Only one address was tracked, so results describe what that address could buy, not the whole pincode. A store can serve several pincodes, so its stock changes include orders from elsewhere.

## 2. Estimating sales

The platform does not publish sales, so sales are inferred from stock:

> **Estimated packs sold** in an interval = the fall in listed stock for the same product at the same store between two consecutive snapshots.

- Stock rises are restocks and never count as sales.
- **Estimated sales value** = packs × the listed price at the start of the interval. It is gross value at listed prices, not revenue.
- Intervals where the product is missing from either snapshot are skipped.

### Artifacts removed

| Artifact | Detection rule | Packs removed |
|---|---|---|
| Morning reset | Stock is otherwise still overnight. Between 04:00 and 06:00 the main store sets many products to one value, usually 12. Timing drifts through late October and can split across two half-hours, so every drop in that window is removed. | 3,455 |
| Late reset | On some days the reset comes later, so 2+ products at one store each falling 5+ units to exactly 12 in the same half-hour are removed. Across the window this only happens on 1 November. | 178 |
| Closing adjustment | Store B, 23:00–23:30: many products fall at once just before it leaves the listing | 408 |
| One-off correction | A single product falling 30+ units in a half-hour. There was one case (50 to 0); the next largest drop is 19. | 50 |

Together these remove 4,091 packs. Evening restocks need no rule, because rises are never counted.

**Display cap:** after a reset, best sellers sit at exactly 12 for hours. That figure looks capped rather than real, so morning sales of those products are probably under-counted.

## 3. Results

### Totals

| Metric | Value |
|---|---|
| Estimated packs | **6,407**, or 238 a day |
| Estimated sales value | **₹4,02,405**, or ₹14,927 a day |
| Litres (volume-labelled products only) | 3,246 L, or 120 L a day |
| Average value per pack | ₹63 |

**Daily packs, 6 Oct–1 Nov:** 449 369 320 243 172 178 113 259 251 208 220 202 263 193 165 189 207 223 287 318 265 214 208 229 203 243 216

The average fell from 311 packs a day on 6–10 Oct to 221 from 11 Oct. That follows Store B dropping out of the listings, from 108 packs a day to 45. It is **not** evidence that demand fell.

### Timing

- The peak is the 9 am hour, at 24.6 packs a day, followed by 10 am (19.8) and 11 am (19.0), with a smaller evening rise around 8 pm (16.5).
- From 11 Oct, so that store coverage is comparable, weekends average 244 packs a day against 210 on weekdays, about 16% higher. The gap is largest in the morning, and there are only seven weekend days.
- **Weekly cycle:** the same weekday only weakly repeats from one week to the next. The repeat score (1 = identical pattern, 0 = no link) is 0.12 across all stores and 0.32 for Store A, so this isn't a reliable cycle yet.

### Brands

| Brand | Packs | % packs | Sales value | % value |
|---|---|---|---|---|
| Amul | 1,429 | 22.3 | ₹68,473 | 17.0 |
| Akshayakalpa Organic | 1,357 | 21.2 | ₹97,592 | 24.3 |
| Provilac | 899 | 14.0 | ₹1,16,641 | 29.0 |
| Nandini | 731 | 11.4 | ₹23,486 | 5.8 |
| Arokya | 452 | 7.1 | ₹15,246 | 3.8 |
| Heritage | 413 | 6.4 | ₹12,890 | 3.2 |
| Sids Farm | 315 | 4.9 | ₹19,263 | 4.8 |
| Country Delight | 308 | 4.8 | ₹14,995 | 3.7 |
| Nandini Goodlife | 171 | 2.7 | ₹6,734 | 1.7 |
| Yakult | 121 | 1.9 | ₹11,200 | 2.8 |

99% of Provilac's packs were sold through Store B, so its share depends on whether that store is visible.

### Price segments

| Segment | Products | Packs | % packs | Litres | Sales value | % value |
|---|---|---|---|---|---|---|
| Value (<₹60/L) | 11 | 1,418 | 22.1 | 752 | ₹40,306 | 10.0 |
| Mainstream (₹60–80) | 16 | 1,169 | 18.2 | 718 | ₹51,994 | 12.9 |
| Premium (₹80–150) | 47 | 2,407 | 37.6 | 1,425 | ₹1,43,038 | 35.5 |
| Specialty (₹150+) | 28 | 1,092 | 17.0 | 351 | ₹1,20,557 | 30.0 |
| Weight (₹/kg) | 3 | 321 | 5.0 | — | ₹46,510 | 11.6 |

Products labelled by weight have no defensible per-litre price, so they sit in their own group. Protein drinks (products with "protein" in the name): 22 products, 1,551 packs (24.2%) and ₹1,60,904 (40.0% of value).

### Pack sizes

400–500 ml packs are 65% of packs, and the exact 500 ml size is 53%.

### Top 10 products by estimated packs

| # | Product | Pack | Packs | In stock |
|---|---|---|---|---|
| 1 | Amul Taaza Toned | 500 ml | 301 | 75% |
| 2 | Akshayakalpa Cow | 500 ml | 295 | 86% |
| 3 | Akshayakalpa Amrutha Farm Fresh A2 | 500 ml | 271 | 84% |
| 4 | Nandini Toned | 500 ml | 270 | 92% |
| 5 | Provilac Cacao 26g High Protein | 250 g | 239 | 92% |
| 6 | Arokya Full Cream | 500 ml | 234 | 92% |
| 7 | Amul Gold Full Cream | 500 ml | 231 | 87% |
| 8 | Arokya Toned | 500 ml | 218 | 93% |
| 9 | Akshayakalpa A2 Cow | 500 ml | 203 | 80% |
| 10 | Amul Taaza Toned | 1 ltr | 198 | 100% |

### Average sales when available

Total packs reward products that are visible and in stock most often, so products are also ranked by packs per **sellable day**: 34 half-hours between 06:00 and 23:00 when the product was listed and in stock. Products with under 3 sellable days are left out.

Provilac takes the top three places. Cacao 26g Protein sells 25.9 packs per sellable day, against 15.6 for Amul Taaza Toned 500 ml, the top seller by total packs. Provilac's rates rest on only about 8–9 sellable days, so they're indicative.

## 4. Stockout response

These are associations, not proof that shoppers switched. For each pair, B's sales while A is out of stock or short are compared with B's usual sales at the same hour when A is available, scaled by that day's demand. Intervals come from 2,000 bootstrap resamples of days (seed 7, 90%), and Benjamini-Hochberg q-values check the results against chance. Pairs with expected sales below 5 packs or fewer than 10 half-hours are not tested.

A result counts as meaningful only if all of these hold:

- Its 90% interval is entirely above zero.
- The stockout happened on 5+ separate days.
- No more than 60% of those half-hours were overnight.
- A was in stock for at least a third of comparable half-hours.
- B's extra packs are no more than the packs A likely missed.
- For products, both meet the same need (regular milk, protein, plant-based or probiotic).

**Brands:** 7 of 193 tested pairs pass every test. These three have stronger evidence (q ≤ 0.25):

| Short brand | Brand that rises | Lift | 90% interval |
|---|---|---|---|
| Provilac | Arokya | +50% | +10% to +103% |
| Akshayakalpa | Arokya | +89% | +34% to +181% |
| Amul | Heritage | +116% | +33% to +293% |

**Products:** 14 of 2,585 tested pairs pass every test, and the [top 10 are charted](../charts/top10_product_substitutions.png). Only one of the top 10 has stronger evidence: Amul Moti Toned 450 ml rises 107% (+32% to +275%) when Akshayakalpa Cow 500 ml is out. The other nine could still be chance, so they are leads to test.

All tested pairs are in [`results/brand_substitution_all_pairs.csv`](../results/brand_substitution_all_pairs.csv) and [`results/product_substitution_all_pairs.csv`](../results/product_substitution_all_pairs.csv).

**Change from the first 13 days:** on 6–18 Oct, Nandini Toned rose significantly during three Akshayakalpa stockouts (+101% to +190%). On the full window, Akshayakalpa Cow out still shows Nandini Toned at +132% (+17% to +353%), but it fails the plausibility tests above. The other two no longer show a clear change, so the longer window is the better guide.

## 5. Availability

Complete snapshots only.

- **Unweighted:** 79.8% of listed product observations show stock, so about 1 in 5 listings is unavailable.
- **Sales-weighted:** 87.2%. Each product is weighted by its estimated packs + 1.
- **By brand, unweighted:** Arokya 92%, Heritage 88%, Amul 86%, Nandini 86%, Akshayakalpa Organic 79%, Country Delight 78%, Sids Farm 70%, Provilac 59%.
- **By hour:** sales-weighted availability is 91–98% from 5 am to noon, falling to 71% at 9 pm, just before restocking. Unweighted, the 9 pm low is 70.0%.

## 6. Sales value potentially missed

Each out-of-stock half-hour is valued at the product's average in-stock sales for that hour (minimum 3 observations) at its median listed price.

- **Result:** 1,158 packs and **₹79,087** potentially missed, or ₹2,934 a day. Unmet share: 15.3% of demand.
- **Largest:** Provilac 50g Protein 500 ml leads on value (₹6,465), and Amul Taaza Toned 500 ml leads on packs (145).
- **Caveat:** this ignores substitution and delayed purchases, so it is an upper-bound style estimate, not actual lost sales.

## 7. Restocking and stockout duration

- **Restocks:** a rise of 2+ units between snapshots at one store. There were 872, and 60% fall between 9 and 11 pm.
- **Daytime stockouts:** 434 episodes, median 3.0 hours. 51% lasted 3 hours or more.

## 8. Limitations

1. Sales are inferred from stock counts. Decreases may include write-offs or corrections beyond those filtered.
2. Stock pinned at 12 after the morning reset probably hides some morning sales, so totals are conservative.
3. Store B was often hidden from 9 Oct. Its sales while hidden are unknown, which affects the trend and Provilac's share.
4. One address, one category and 27 days. The stores also serve other areas.
5. Timing is only accurate to the 30-minute snapshot interval.
6. Partial snapshots are excluded from availability, and intervals with missing products are skipped for sales.
7. Thousands of stockout comparisons were tested. The false-discovery check limits this risk but doesn't remove it, and stockouts cluster at busy times, so shared timing can look like switching.
8. Listed prices only: no discounts, coupons or fees.
