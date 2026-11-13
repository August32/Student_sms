

# 班级信息模型（对应需求 2.4 班级管理模块）

from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

class ClassInfo(Base):
    """班级信息表"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # [改] 原 class_id
# id：主键，自增，唯一标识每条班级记录

    class_name = Column(String(30), nullable=False, unique=True, index=True)  # [改] 长度 8→30
# class_name：班级名字，非空，唯一

    class_time = Column(DateTime, nullable=False)
# class_time：开课时间，日期时间，非空

    class_teacher = Column(String(30), nullable=False)
# class_teacher：班主任，字符串长度30，非空

# [删] lecturer 字段：授课老师改用 teacher.py 中的 teacher_class 多对多中间表维护

    class_status = Column(String(16), nullable=False, default="未开课")
# class_status：班级状态，非空，默认"未开课"（未开课/进行中/已结课）

    student_count = Column(Integer, nullable=False, default=0)
# student_count：班级学生人数，非空，默认0（冗余字段，学生增删时需同步维护）

    # ---- 统一的软删除 + 时间戳字段（五个模型保持一致）----
    is_deleted = Column(Integer, default=0, nullable=False, index=True)  # [改] 原 is_delete(String)
# is_deleted：软删除标记，0=未删除，1=已删除（删除只做标记，数据还在表里）

    deleted_at = Column(DateTime, nullable=True)  # [增] 删除时间

    created_at = Column(DateTime, nullable=False, server_default=func.now())
# created_at：创建时间，自动填入当前时间

    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
# updated_at：更新时间，每次修改自动刷新为当前时间