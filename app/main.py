from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.common.database import get_db
from app.common.models import IndexValue, IndexVintage, CellPrice, Observation, RawQuote, CollectionRun

app = FastAPI(
    title="AIRIS API",
    description="Real-time Airfare Price Index for India",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MethodologyBlock(BaseModel):
    formula: str = "GEKS-Jevons (13-period rolling window) / TPD / Naive-Mean"
    weights: str = "DGCA passenger-volume proxies (Illustrative)"
    coverage_rules: str = "Matched observations > 500 (A), Cells > 30 (A)"

class IndexResponse(BaseModel):
    series_id: str
    period: date
    index_value: float
    estimator: str
    coverage_grade: Optional[str]
    publication_status: str
    methodology: MethodologyBlock = MethodologyBlock()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/v1/series", response_model=List[str])
def get_series(db: Session = Depends(get_db)):
    series = db.query(IndexValue.series_id).distinct().all()
    return [s[0] for s in series]

@app.get("/api/v1/index/{series_id}", response_model=List[IndexResponse])
def get_index(
    series_id: str, 
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None,
    estimator: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(IndexValue).filter(IndexValue.series_id == series_id)
    if start_date: query = query.filter(IndexValue.period >= start_date)
    if end_date: query = query.filter(IndexValue.period <= end_date)
    if estimator: query = query.filter(IndexValue.estimator == estimator)
    
    results = query.order_by(IndexValue.period).all()
    
    return [
        IndexResponse(
            series_id=r.series_id,
            period=r.period,
            index_value=r.index_value,
            estimator=r.estimator,
            coverage_grade=r.coverage_grade,
            publication_status=r.publication_status
        ) for r in results
    ]

@app.get("/api/v1/index/{series_id}/lineage/{period}")
def get_lineage(series_id: str, period: date, db: Session = Depends(get_db)):
    """
    Returns full lineage trace for a given series and period.
    """
    index_vals = db.query(IndexValue).filter(
        IndexValue.series_id == series_id,
        IndexValue.period == period
    ).all()
    
    if not index_vals:
        raise HTTPException(status_code=404, detail="Index not found")
        
    # Find contributing cell prices
    # Simplified lineage trace for demonstration
    cell_prices = db.query(CellPrice).filter(CellPrice.period == period).all()
    
    # Just return counts/samples to avoid massive payloads
    return {
        "index_values": [{"id": v.id, "value": v.index_value, "estimator": v.estimator} for v in index_vals],
        "contributing_cells_count": len(cell_prices),
        "sample_cells": [{"cell_id": cp.cell_id, "price": cp.representative_price} for cp in cell_prices[:5]]
    }

@app.get("/api/v1/runs")
def get_runs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    List collection runs.
    """
    runs = db.query(CollectionRun).order_by(desc(CollectionRun.started_at)).offset(skip).limit(limit).all()
    return [
        {
            "id": r.id,
            "source_id": r.source_id,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "status": r.status,
            "quotes_collected": r.quotes_collected,
            "is_degraded": r.is_degraded
        } for r in runs
    ]

@app.get("/api/v1/observations")
def get_observations(run_id: str = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    List observations. If run_id is provided, filter by run.
    """
    query = db.query(Observation)
    if run_id:
        query = query.join(RawQuote).filter(RawQuote.collection_run_id == run_id)
        
    observations = query.order_by(desc(Observation.created_at)).offset(skip).limit(limit).all()
    return [
        {
            "id": o.id,
            "origin": o.origin,
            "destination": o.destination,
            "carrier": o.carrier,
            "flight_identifier": o.flight_identifier,
            "departure_datetime": o.departure_datetime,
            "arrival_datetime": o.arrival_datetime,
            "all_inclusive_price": o.all_inclusive_price,
            "currency": o.currency,
            "validation_status": o.validation_status
        } for o in observations
    ]

from fastapi.responses import StreamingResponse
import io
import csv

@app.get("/api/v1/reports/download/{report_type}")
def download_report(report_type: str, db: Session = Depends(get_db)):
    """
    Generate and download real-time CSV reports.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "index":
        # Export latest index values
        writer.writerow(["Series ID", "Period", "Index Value", "Estimator", "Publication Status"])
        records = db.query(IndexValue).order_by(desc(IndexValue.period)).limit(1000).all()
        for r in records:
            writer.writerow([r.series_id, r.period, r.index_value, r.estimator, r.publication_status])
        filename = "airis_index_report.csv"
        
    elif report_type == "flights":
        # Export recent flight observations
        writer.writerow(["Origin", "Destination", "Carrier", "Flight", "Departure", "Price", "Status"])
        records = db.query(Observation).order_by(desc(Observation.created_at)).limit(1000).all()
        for r in records:
            writer.writerow([r.origin, r.destination, r.carrier, r.flight_identifier, r.departure_datetime, r.all_inclusive_price, r.validation_status])
        filename = "airis_flights_report.csv"
    else:
        raise HTTPException(status_code=400, detail="Unknown report type")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
