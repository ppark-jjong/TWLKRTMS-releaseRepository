"""
인수인계 모델 - init-db.sql 스키마와 정확히 일치하도록 수정됨
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from main.utils.database import Base


class Handover(Base):
    """인수인계 테이블 모델"""

    __tablename__ = "handover"

    handover_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    update_by = Column(
        String(50), ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False
    )
    create_by = Column(
        String(50), ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False
    )
    is_notice = Column(Boolean, default=False)
    # 부서 필드 추가
    department = Column(
        Enum("CS", "HES", "LENOVO", "ALL", name="handover_department_enum"),
        nullable=False,
        default="ALL",
    )
    update_at = Column(DateTime, nullable=False, default=func.now())
    create_time = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(
        Enum("OPEN", "CLOSE", name="handover_status_enum"),
        nullable=False,
        server_default="OPEN",
    )
    version = Column(Integer, nullable=False, server_default=text("1"))

    # 관계 설정 - backref 대신 back_populates로 명시적 양방향 관계 정의
    updater = relationship(
        "User", foreign_keys=[update_by], back_populates="updated_handovers"
    )
    creator = relationship(
        "User", foreign_keys=[create_by], back_populates="created_handovers"
    )
