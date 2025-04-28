"""
인수인계 모델 - init-db.sql 스키마와 정확히 일치하도록 수정됨
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
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
    is_notice = Column(Boolean, default=False)
    update_at = Column(DateTime, nullable=False, default=func.now())  # create_at 제거, nullable=False로 변경
    is_locked = Column(Boolean, default=False)

    # 관계 설정
    user = relationship("User", back_populates="handovers")
