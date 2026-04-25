# AuksionWatch — ML Dataset (1-bosqich)

e-auksion.uz saytidan 10,000 lotlik structured dataset. AI red-flag detector o'qitish uchun.

## Tez boshlash

```bash
pip install -r requirements.txt
playwright install chromium

python scripts/00_get_lot_ids.py          # ~30 daqiqa
python scripts/01_scrape_lots.py           # ~1-2 soat (10K lot)
python scripts/01_scrape_lots.py --resume  # to'xtagan joydan davom etish

python scripts/02_clean.py                 # ~10 daqiqa
python scripts/03_features.py             # ~20 daqiqa (embedding bilan)
python scripts/05_label.py                # 200 ta lot tanlaydi
# ... red_flags_labeled_template.csv ni qo'lda to'ldiring ...
python scripts/04_eda.py                  # HTML hisobot

python scripts/06_validate.py             # topshirishdan oldin tekshiring
```

## Chiqish fayllari

| Fayl | Format | Mazmuni |
|------|--------|---------|
| `data/lots_raw.parquet` | Parquet | Scrape qilingan xom ma'lumot |
| `data/lots_clean.parquet` | Parquet | Tozalangan, normalizatsiya qilingan |
| `data/lots_features.parquet` | Parquet | 30+ ML feature |
| `data/red_flags_labeled.csv` | CSV | 200 ta qo'lda yorliqlangan lot |
| `data/eda_report.html` | HTML | Avtomatik EDA hisobot |
| `notebooks/notebook_eda.ipynb` | Jupyter | 10 ta vizualizatsiya |

## Dataset sxemasi

### lots_clean.parquet
| Ustun | Tur | Tavsif |
|-------|-----|--------|
| `lot_id` | int | Unikal identifikator |
| `lot_type` | str | Mulk turi (normalized) |
| `region_code` | str | UZ-XX format (UZ-TK, UZ-FA, ...) |
| `auction_type` | str | `open` yoki `closed` |
| `start_price` | Int64 | Boshlang'ich narx (so'm) |
| `sold_price` | Int64 | Sotilgan narx (so'm) |
| `area_m2` | float | Maydon (m²) |
| `bidders_count` | Int64 | Ishtirokchilar soni |
| `seller_inn` | str | Sotuvchi INN (9 raqam) |
| `winner_inn` | str | G'olib INN (9 raqam) |
| `start_time` | datetime | Boshlanish vaqti |
| `end_time` | datetime | Tugash vaqti |
| `status` | str | `completed`, `active`, `upcoming`, `cancelled` |
| `geo_lat`, `geo_lon` | float | Koordinatalar |

### lots_features.parquet (qo'shimcha)
| Feature | Tavsif |
|---------|--------|
| `price_per_m2` | m² narxi |
| `discount_pct` | Chegirma % |
| `is_closed` | Yopiq auksion (0/1) |
| `is_single_bidder` | 1 ishtirokchi (0/1) |
| `duration_hours` | Auksion davomiyligi |
| `red_flag_score` | Shubhalilik indeksi (0–10) |
| `description_emb` | 384-dim embedding |
| ... | 30+ feature |

## Muammolar va yechimlar

| Muammo | Yechim |
|--------|--------|
| IP block | `--resume` + VPN, yoki sleep oshirish (01_scrape_lots.py: `SLEEP_BETWEEN`) |
| Scraping to'xtab qoldi | `python scripts/01_scrape_lots.py --resume` |
| Selector ishlamayapti | `selectors.md` ni yangilang, `raw_html` ni qarang |
| Geocoding sekin | `DO_GEOCODING = False` deb 02_clean.py da o'chiring |

## Scraping parametrlari

`scripts/01_scrape_lots.py` ichida:
```python
CONCURRENCY = 5      # parallel sahifalar soni
SLEEP_BETWEEN = 0.3  # har lot orasida (sekund)
```
IP block bo'lsa: `CONCURRENCY = 2`, `SLEEP_BETWEEN = 1.0`
