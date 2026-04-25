"""SQLModel database models for AuksionWatch.

Bitta jadval — `lot`. Har lot uchun e-auksion'dan kelgan asl ma'lumot,
risk engine natijasi (rule-based) va ML ensemble natijasi saqlanadi.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, JSON, Column


class Lot(SQLModel, table=True):
    # ───────── Asosiy identifikator ─────────
    id: int = Field(primary_key=True)             # e-auksion lot_id (masalan 23469523)
    url: str                                      # https://e-auksion.uz/lot-view?lot_id=...

    # ───────── Tavsif maydonlari ─────────
    title: Optional[str] = None                   # lot sarlavhasi
    lot_type: Optional[str] = None                # umumiy tur (yer, ko'chmas mulk, avto)
    lot_type_specific: Optional[str] = None       # batafsil kategoriya
    address: Optional[str] = None                 # joylashuv manzili
    region: Optional[str] = Field(default=None, index=True)   # UZ-TK, UZ-FA, ...
    district: Optional[str] = None                # tuman/shahar

    # ───────── Narx maydonlari ─────────
    start_price: Optional[float] = Field(default=None, index=True)  # boshlang'ich narx
    sold_price: Optional[float] = None            # sotuv narxi (tugagan auksion uchun)
    appraised_price: Optional[float] = None       # rasmiy baholangan narx (Excel'dan)
    deposit: Optional[float] = None               # zakalat puli
    step_price: Optional[float] = None            # auksion qadami
    installment_months: Optional[int] = None      # bo'lib to'lash oy soni

    # ───────── Auksion turi va vaqti ─────────
    auction_method: Optional[str] = None          # "Auksion", "Tanlov", h.k.
    auction_style: Optional[str] = None           # "Oshirib borish", "Pasaytirib borish"
    auction_type: str = Field(default="open", index=True)  # open / closed / unknown
    start_time: Optional[str] = None              # auksion boshlanish vaqti
    deadline: Optional[str] = None                # ariza qabul qilish oxirgi muddati
    end_time: Optional[str] = None                # auksion tugash vaqti
    status: Optional[str] = None                  # "tugagan", "savdoda", "kelgusi"

    # ───────── Faollik ko'rsatkichlari ─────────
    views: Optional[int] = None                   # ko'rishlar soni
    bidders_count: Optional[int] = None           # ishtirokchilar soni (auction_cnt)
    times_auctioned: Optional[int] = None         # necha marta qayta auksionga chiqarilgan

    # ───────── Sotuvchi ma'lumotlari ─────────
    seller_hint: Optional[str] = None             # davaktiv / court / bank / individual
    seller_name: Optional[str] = None             # to'liq nom
    seller_id: Optional[int] = Field(default=None, index=True)  # MD5(name) → integer

    # ───────── Geografiya (xarita uchun) ─────────
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    is_descending: Optional[bool] = None          # teskari auksion (narx tushadi)

    # ───────── Rule-based risk natijasi ─────────
    risk_score: float = Field(default=0.0, index=True)        # 0-100 weighted sum
    risk_level: str = Field(default="low", index=True)        # low / medium / high
    ai_summary: Optional[str] = None              # qisqa AI xulosasi (matn)
    flags: Optional[list] = Field(default=None, sa_column=Column(JSON))      # red-flag obyektlar ro'yxati
    categories: Optional[dict] = Field(default=None, sa_column=Column(JSON)) # 5 OECD toifasi sub-ball

    # ───────── ML ensemble natijasi (XGBoost + IsoForest) ─────────
    ml_score: Optional[float] = Field(default=None, index=True)  # 0..1 yakuniy ensemble
    ml_level: Optional[str] = None                # KRITIK / YUQORI / O'RTA / PAST (kvantil)
    ml_reason: Optional[str] = None               # "Bankrupcy + chegirmasiz | 35x re-list"
    ml_xgb_prob: Optional[float] = None           # XGBoost probability
    ml_iso_score: Optional[float] = None          # IsolationForest anomaly score

    # ───────── Metadata ─────────
    scraped_at: datetime = Field(default_factory=datetime.utcnow)  # DB'ga qachon yozilgan
