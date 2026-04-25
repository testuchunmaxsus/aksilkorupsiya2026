"""SQLModel database models for AuksionWatch."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, JSON, Column


class Lot(SQLModel, table=True):
    id: int = Field(primary_key=True)  # e-auksion lot_id
    url: str
    title: Optional[str] = None
    lot_type: Optional[str] = None
    lot_type_specific: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = Field(default=None, index=True)
    district: Optional[str] = None
    start_price: Optional[float] = Field(default=None, index=True)
    sold_price: Optional[float] = None
    appraised_price: Optional[float] = None
    deposit: Optional[float] = None
    step_price: Optional[float] = None
    installment_months: Optional[int] = None
    auction_method: Optional[str] = None
    auction_style: Optional[str] = None
    auction_type: str = Field(default="open", index=True)
    start_time: Optional[str] = None
    deadline: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None
    views: Optional[int] = None
    bidders_count: Optional[int] = None
    times_auctioned: Optional[int] = None
    seller_hint: Optional[str] = None
    seller_name: Optional[str] = None
    seller_id: Optional[int] = Field(default=None, index=True)
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    is_descending: Optional[bool] = None
    risk_score: float = Field(default=0.0, index=True)
    risk_level: str = Field(default="low", index=True)
    ai_summary: Optional[str] = None
    flags: Optional[list] = Field(default=None, sa_column=Column(JSON))
    categories: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # ML pipeline outputs (XGBoost + IsolationForest ensemble)
    ml_score: Optional[float] = Field(default=None, index=True)  # 0..1
    ml_level: Optional[str] = None  # KRITIK / YUQORI / O'RTA / PAST
    ml_reason: Optional[str] = None
    ml_xgb_prob: Optional[float] = None
    ml_iso_score: Optional[float] = None

    scraped_at: datetime = Field(default_factory=datetime.utcnow)
