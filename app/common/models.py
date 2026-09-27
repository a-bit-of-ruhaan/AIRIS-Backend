from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from app.common.database import Base
from datetime import datetime
import enum

class SourceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEGRADED = "DEGRADED"

class RunStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DEGRADED = "DEGRADED"

class Source(Base):
    __tablename__ = 'source'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # e.g. "airline", "aggregator"
    status = Column(Enum(SourceStatus), default=SourceStatus.ACTIVE)
    is_direct = Column(Boolean, default=False)
    parser_contract = Column(String)
    provenance_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class RouteFrame(Base):
    __tablename__ = 'route_frame'
    route_id = Column(String, primary_key=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    stratum = Column(String, nullable=False)
    inclusion_probability = Column(Float, nullable=False)
    horvitz_thompson_weight = Column(Float, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

class CollectionRun(Base):
    __tablename__ = 'collection_run'
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey('source.id'), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    expected_yield_min = Column(Integer)
    expected_yield_max = Column(Integer)
    actual_yield = Column(Integer)
    status = Column(Enum(RunStatus))
    is_degraded = Column(Boolean, default=False)
    policy_checks = Column(JSON)
    robots_evidence_ref = Column(String)
    request_rate = Column(Float)
    delay_applied = Column(Float)
    parser_version = Column(String)
    error_summary = Column(String)
    
    source = relationship("Source")

class RawQuote(Base):
    __tablename__ = 'raw_quote'
    id = Column(String, primary_key=True)
    collection_run_id = Column(String, ForeignKey('collection_run.id'), nullable=False)
    source_id = Column(String, ForeignKey('source.id'), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    request_spec_id = Column(String)
    route = Column(String, nullable=False)
    departure_date = Column(Date, nullable=False)
    booking_horizon = Column(Integer, nullable=False)
    raw_payload_ref = Column(String, nullable=False) # e.g., s3 path or json hash
    response_hash = Column(String, nullable=False)
    source_url = Column(String)
    http_metadata = Column(JSON)
    parser_version = Column(String)
    policy_evidence_ref = Column(String)
    timestamps = Column(JSON)

    collection_run = relationship("CollectionRun")

class Cell(Base):
    __tablename__ = 'cell'
    id = Column(String, primary_key=True)
    route = Column(String, nullable=False)
    carrier = Column(String, nullable=False)
    cabin = Column(String, nullable=False)
    fare_product_identity = Column(String, nullable=False)
    booking_horizon = Column(Integer, nullable=False)
    source_id = Column(String, ForeignKey('source.id'), nullable=False)
    definition_metadata = Column(JSON)

class Observation(Base):
    __tablename__ = 'observation'
    id = Column(String, primary_key=True)
    raw_quote_id = Column(String, ForeignKey('raw_quote.id'), nullable=False)
    source_id = Column(String, ForeignKey('source.id'), nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    carrier = Column(String, nullable=False)
    flight_identifier = Column(String)
    departure_datetime = Column(DateTime, nullable=False)
    arrival_datetime = Column(DateTime)
    cabin = Column(String, nullable=False)
    fare_basis_code = Column(String)
    rbd = Column(String)
    fare_product_identity = Column(String, nullable=False)
    is_refundable = Column(Boolean)
    baggage_allowance = Column(String)
    change_fee_flag = Column(Boolean)
    brand_label = Column(String)
    base_fare = Column(Float)
    taxes = Column(Float)
    fees = Column(Float)
    all_inclusive_price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    booking_horizon = Column(Integer, nullable=False)
    cell_id = Column(String, ForeignKey('cell.id'), nullable=False)
    validation_status = Column(String, nullable=False) # e.g. "VALID", "INVALID"
    rejection_reason = Column(String)
    is_duplicate = Column(Boolean, default=False)
    is_outlier = Column(Boolean, default=False)
    is_surrogate = Column(Boolean, default=False)
    cleaning_rule_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class CellPrice(Base):
    __tablename__ = 'cell_price'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cell_id = Column(String, ForeignKey('cell.id'), nullable=False)
    period = Column(Date, nullable=False)
    representative_price = Column(Float, nullable=False) # Geometric mean
    matched_observation_count = Column(Integer, nullable=False)
    valid_observation_count = Column(Integer, nullable=False)
    dispersion = Column(Float)
    outlier_count = Column(Integer, default=0)
    source_id = Column(String, ForeignKey('source.id'))
    quality_flags = Column(JSON)

class IndexValue(Base):
    __tablename__ = 'index_value'
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(String, nullable=False)
    period = Column(Date, nullable=False)
    aggregate_level = Column(String, nullable=False) # e.g., 'national', 'route'
    index_value = Column(Float, nullable=False)
    estimator = Column(String, nullable=False) # 'GEKS-Jevons', 'TPD', 'naive-mean'
    coverage_grade = Column(String)
    contributing_cell_count = Column(Integer)
    observation_count = Column(Integer)
    thin_cell_share = Column(Float)
    spliced_share = Column(Float)
    surrogate_share = Column(Float)
    dispersion = Column(Float)
    confidence_interval = Column(JSON)
    contributing_sources = Column(JSON)
    publication_status = Column(String, nullable=False) # 'provisional', 'revised', 'final'
    methodology_version = Column(String)
    weight_version = Column(String)
    data_vintage = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class IndexVintage(Base):
    __tablename__ = 'index_vintage'
    id = Column(Integer, primary_key=True, autoincrement=True)
    index_value_id = Column(Integer, ForeignKey('index_value.id'), nullable=False)
    original_published_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    publication_timestamp = Column(DateTime, nullable=False)
    revision_timestamp = Column(DateTime)
    revision_reason = Column(String)
    status = Column(String, nullable=False) # 'provisional', 'revised', 'final'
    methodology_version = Column(String)

class Weight(Base):
    __tablename__ = 'weight'
    route = Column(String, primary_key=True)
    weight_value = Column(Float, nullable=False)
    is_illustrative = Column(Boolean, default=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    source_metadata = Column(String) # e.g., 'DGCA'
