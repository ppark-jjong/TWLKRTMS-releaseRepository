"""
사용자 모델 - init-db.sql 스키마와 정확히 일치하도록 수정됨
"""

from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from main.utils.database import Base


class User(Base):
    """사용자 테이블 모델"""

    __tablename__ = "user"

    user_id = Column(String(50), primary_key=True, index=True)
    user_name = Column(String(50), nullable=False)
    user_password = Column(String(255), nullable=False)
    user_department = Column(
        Enum("CS", "HES", "LENOVO", name="user_department_enum"), nullable=False
    )
    user_role = Column(Enum("ADMIN", "USER", name="user_role_enum"), nullable=False)

    created_handovers = relationship(
        "Handover",
        foreign_keys="[Handover.create_by]",
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    # 인수인계 수정자 관계
    updated_handovers = relationship(
        "Handover",
        foreign_keys="[Handover.update_by]",
        back_populates="updater",
        cascade="all, delete-orphan",
    )

    # 대시보드(주문) 수정자 관계 추가
    updated_dashboards = relationship(
        "Dashboard",
        foreign_keys="[Dashboard.update_by]",
        back_populates="updater",
        # cascade 설정은 Dashboard의 update_by가 NULL 허용이므로 불필요할 수 있음
    )
