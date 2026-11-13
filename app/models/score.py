# app/models/score.py

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Float, UniqueConstraint, func  # [改] 增加 UniqueConstraint / func
from app.core.database import Base
class Score(Base):
    __tablename__ = 'student_scores'
    __table_args__ = (
        UniqueConstraint('student_id', 'exam_sequence', name='uq_student_exam'),
        # 表级配置。唯一约束，保证同一个学生每次考核只有一条成绩记录
    )
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 成绩记录主键ID
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False, index=True)  # 学生编号，外键关联students表
    exam_sequence = Column(Integer, nullable=False, index=True)  # 考核序次：第一次考核、第二次考核
    score = Column(Float, nullable=False)  # 考核成绩，支持小数分数
    # 扩展辅助字段，方便统计和日志追踪
    exam_date = Column(Date, nullable=True)  # 考核考试日期
    remark = Column(String(200), nullable=True)  # 成绩备注
    # ---- 统一的软删除 + 时间戳字段（五个模型保持一致）----
    is_deleted = Column(Integer, default=0, nullable=False, index=True)  # 逻辑删除标记 0未删 1已删
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())  #
