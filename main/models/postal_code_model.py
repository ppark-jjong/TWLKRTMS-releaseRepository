"""
우편번호 모델
"""

from sqlalchemy import Column, String, Integer, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from main.utils.database import Base


class PostalCode(Base):
    """우편번호 테이블 모델"""

    __tablename__ = "postal_code"

    postal_code = Column(String(5), primary_key=True)
    city = Column(String(100), nullable=True)
    county = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    # 관계 설정
    dashboard_entries = relationship("Dashboard", back_populates="postal_code_obj")
    detail_entries = relationship("PostalCodeDetail", back_populates="postal_code_obj")


class PostalCodeDetail(Base):
    """우편번호 상세 정보 테이블 모델"""

    __tablename__ = "postal_code_detail"

    postal_code = Column(
        String(5), ForeignKey("postal_code.postal_code"), primary_key=True
    )
    warehouse = Column(
        Enum("SEOUL", "BUSAN", "GWANGJU", "DAEJEON", name="warehouse_enum"),
        primary_key=True,
    )
    distance = Column(Integer, nullable=False)
    duration_time = Column(Integer, nullable=False)

    # 관계 설정
    postal_code_obj = relationship("PostalCode", back_populates="detail_entries")

    # 인덱스 설정
    __table_args__ = (Index("idx_warehouse_postal", "warehouse"),)
