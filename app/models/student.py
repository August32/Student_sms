from sqlalchemy import Column, Integer, String, ForeignKey,Date,DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base
# 创建新学⽣记录（学⽣编号、学⽣班级、学⽣姓名、籍贯、毕业院校、专业、
# ⼊学时间、毕业时间、学历、顾问编号、年龄、性别）
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) #学⽣编号
    class_id = Column(Integer, ForeignKey('classes.id')) #学⽣班级，关联班级表
    name= Column(String(50), index=True, nullable=False) #学⽣姓名
    native_place = Column(String(50), nullable=True) #籍贯
    graduate_school = Column(String(100), nullable=True) #毕业院校
    major = Column(String(60), nullable=True) #专业
    enroll_time = Column(Date, nullable=True) #⼊学时间
    graduate_time = Column(Date, nullable=True) #毕业时间
    education = Column(String(20), nullable=True) #学历
    consultant_no = Column(String(30), nullable=True, index=True)  # 顾问编号
    age = Column(Integer, nullable=True) #年龄
    gender = Column(String(1), nullable=True) #性别
    is_deleted = Column(Integer, default=0, nullable=False) #是否删除
    deleted_at = Column(DateTime, nullable=True) #删除时间

# # back_populates 必须和 ClassInfo 里的 relationship 名字一致
#     class_info = relationship("ClassInfo", back_populates="students", lazy="select")
#





