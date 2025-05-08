"""
대시보드(주문) 모델
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    Index,
    Computed,
    text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from main.utils.database import Base
from main.models.user_model import User


class Dashboard(Base):
    """대시보드(주문) 테이블 모델"""

    __tablename__ = "dashboard"

    dashboard_id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(255), nullable=False)
    type = Column(
        Enum("DELIVERY", "RETURN", name="dashboard_type_enum"), nullable=False
    )
    status = Column(
        Enum(
            "WAITING",
            "IN_PROGRESS",
            "COMPLETE",
            "ISSUE",
            "CANCEL",
            name="dashboard_status_enum",
        ),
        nullable=False,
        default="WAITING",
    )
    department = Column(
        Enum("CS", "HES", "LENOVO", name="dashboard_department_enum"), nullable=False
    )
    warehouse = Column(
        Enum("SEOUL", "BUSAN", "GWANGJU", "DAEJEON", name="dashboard_warehouse_enum"),
        nullable=False,
    )
    # region 컬럼은 데이터베이스에서 GENERATED ALWAYS AS (CONCAT(city, ' ', county, ' ', district)) STORED 로 자동 생성됨
    # SQLAlchemy에서는 자동 생성 컬럼은 그냥 선언만 함
    region = Column(
        String(153),
        Computed("CONCAT(city, ' ', county, ' ', district)", persisted=True),
        nullable=True,
    )
    sla = Column(String(10), nullable=False)
    eta = Column(DateTime, nullable=False)
    create_time = Column(DateTime, nullable=False, default=func.now())
    depart_time = Column(DateTime, nullable=True)
    complete_time = Column(DateTime, nullable=True)
    postal_code = Column(
        String(5), ForeignKey("postal_code.postal_code"), nullable=False
    )
    city = Column(String(21), nullable=True)
    county = Column(String(51), nullable=True)
    district = Column(String(51), nullable=True)
    distance = Column(Integer, nullable=True)
    duration_time = Column(Integer, nullable=True)
    address = Column(Text, nullable=False)
    customer = Column(String(150), nullable=False)
    contact = Column(String(20), nullable=True)
    driver_name = Column(String(153), nullable=True)
    driver_contact = Column(String(50), nullable=True)
    update_by = Column(String(50), ForeignKey("user.user_id"), nullable=True)
    remark = Column(Text, nullable=True)
    update_at = Column(DateTime, nullable=True, onupdate=func.now())
    version = Column(Integer, nullable=False, server_default=text("1"))
    delivery_company = Column(
        Enum("로얄", "서경", "택화", name="delivery_company_enum"), nullable=True
    )

    # 관계 설정
    postal_code_obj = relationship("PostalCode", back_populates="dashboard_entries")
    updater = relationship("User", foreign_keys=[update_by])

    # 인덱스 설정 (init-db.sql에 언급된 인덱스 추가)
    __table_args__ = (
        Index("idx_eta", "eta"),
        Index("idx_department", "department"),
        Index("idx_order_no", "order_no"),
    )
