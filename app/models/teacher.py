from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Table, func
#从sqlalchemy里导入列,整数,文字,日期,时间和外键,我想建立的中间表,函数统计
from app.core.database import Base
#从app里的core下的database里导入base(汇总管理,不管具体增删改查)

# 老师-授课班级 多对多中间表：
# 一个老师可以教多个班，一个班也有多个老师，数据库没法直接表达，所以建中间表
# (teacher_id, class_id) 一起做复合主键，天然防止重复记录
teacher_class = Table(
    'teacher_class',

    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('teachers.id'), primary_key=True),#老师ID.外键到老师表
    Column('class_id', Integer, ForeignKey('classes.id'), primary_key=True),#班级ID,外键到班级表
)
# 数据库没法多对多,建一个中间表,老师和班级的授课关系表:一个老师可以教多个班,一个班也可以有多个授课老师
# 复合主键(唯一且非空),把老师和班级绑在一起,不出现重复记录

class Teacher(Base):
    """老师信息表（对应需求 2.5 老师管理模块）"""
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # 老师编号:列名,整数,唯一且不为空的主键,建个索引,自增
    name = Column(String(50), index=True, nullable=False) #老师姓名:列名,50个字符串,索引,不允许为空
    gender = Column(String(10), nullable=True) #性别:男/女
    age = Column(Integer, nullable=True)  # 年龄
    phone = Column(String(20), index=True, nullable=True)  # 手机号
    email = Column(String(100), nullable=True)  # 邮箱
    education = Column(String(20), nullable=True)  # 学历
    major = Column(String(60), nullable=True)  # 专业
    title = Column(String(30), nullable=True)  # 职称：讲师/副教授/教授
    subject = Column(String(50), nullable=True)  # 授课科目
    hire_date = Column(Date, nullable=True)  # 入职时间

    # ---- 带班信息（对应需求里的"带班信息等"）----
    # 老师的身份完全由带班数据决定，不用单独存字段：
    #   有 head_class_id       -> 是班主任（一个班只能有一位班主任，所以 unique）
    #   在 teacher_class 有记录 -> 是授课老师
    #   两个都有               -> 既当班主任又授课
    # [删] teacher_type 字段（head/subject/both）：它能从上面两个数据推出来，
    #      再存一份就要到处校验"身份和带班信息是否一致"，纯属重复，删掉后代码简单一半
    head_class_id = Column(Integer, ForeignKey('classes.id'), nullable=True, unique=True)

    # ---- 统一的软删除 + 时间戳字段（五个模型保持一致）----
    is_deleted = Column(Integer, default=0, nullable=False, index=True)  # 0=在职 1=已删除
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
