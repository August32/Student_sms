from sqlalchemy import Column, Integer, String, ForeignKey,Date,DECIMAL,DateTime, func
from app.core.database import Base
from app.models import student
# 就业信息管理
# 记录学生的就业档案（学生编号、学生姓名，学生班级，就业开放时间、offer下发时间、就业公司名称、就业薪资）
class Employment(Base):
    __tablename__ = 'employments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False, unique=True, index=True) #学生编号
    employment_open_date = Column(Date, nullable=True) #就业开放时间
    offer_date = Column(Date, nullable=True) #offer下发时间
    company_name = Column(String(100), nullable=True) #就业公司名称
    salary = Column(DECIMAL(10,2), nullable=True) #就业薪资

    is_deleted = Column(Integer, default=0, nullable=False, index=True)  # 0=未删除 1=已删除
    deleted_at = Column(DateTime)  # 删除时间
    created_at = Column(DateTime, nullable=False, server_default=func.now())  # 创建时间
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())  # 更新时间

    # student_name
    # class_id