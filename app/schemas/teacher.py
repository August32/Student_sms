from datetime import date, datetime
from enum import Enum
from typing import Literal#类似枚举,不需要单独建类
from pydantic import BaseModel, ConfigDict, Field
#从数据安检导入基础模型,万用读卡器(把数据库对象转换成pydantic能读懂的对象),字段限制


class Gender(str, Enum):
    """性别下拉选项（和学生模块保持一致）"""
    male = '男'
    female = '女'


# ---------- 请求体 ----------

class TeacherCreate(BaseModel):
    """新增老师的请求体"""
    # from_attributes：允许把数据库 ORM 对象直接丢进来转成响应格式
    # use_enum_values：性别校验通过后直接存枚举的值("男"/"女")，
    #   不用写库前再手动转换（pymysql 不认识枚举对象，直接塞会存成 "Gender.male"）
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    # 把数据从数据库的orm对象(包含密码等内部状态)转换成pydantic模型(发生在api调用dao拿到数据后,准备返回之前,发生在schemas层
    # ,防泄密防数据库崩溃),再转Jason格式(api给前端,前端只认识jason字符串)
    # 允许直接去读数据库对象的属性,枚举直接取里面的值而不是枚举对象本身
    name: str = Field(..., min_length=1, max_length=50, description='老师姓名')
    gender: Gender | None = Field(None, description='性别：男/女')
    age: int | None = Field(None, gt=0, lt=100, description='年龄')
    phone: str | None = Field(None, max_length=20, description='手机号')
    email: str | None = Field(None, max_length=100, description='邮箱')
    education: str | None = Field(None, max_length=20, description='学历')
    major: str | None = Field(None, max_length=60, description='专业')
    title: str | None = Field(None, max_length=30, description='职称')
    subject: str | None = Field(None, max_length=50, description='授课科目')
    hire_date: date | None = Field(None, description='入职时间')

    head_class_id: int | None = Field(None, gt=0, description='班主任负责的班级id，不是班主任就不传')
    class_ids: list[int] = Field(default_factory=list, description='授课班级id列表，可多个')


class TeacherUpdate(BaseModel):
    """修改老师的请求体：所有字段可选，只传要改的。
    想清空某个字段（比如取消班主任带班），显式传 null 即可"""
    model_config = ConfigDict(use_enum_values=True)

    name: str | None = Field(None, min_length=1, max_length=50)
    gender: Gender | None = Field(None)
    age: int | None = Field(None, gt=0, lt=100)#大于0小于100,ge是大于或等于,le是小于或等于
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=100)
    education: str | None = Field(None, max_length=20)
    major: str | None = Field(None, max_length=60)
    title: str | None = Field(None, max_length=30)
    subject: str | None = Field(None, max_length=50)
    hire_date: date | None = Field(None)

    head_class_id: int | None = Field(None, gt=0)
    class_ids: list[int] | None = Field(None, description='传了就整体替换授课班级')


class TeacherQuery(BaseModel):
    #查询体和请求体的区别:前端给后端的一大包数据(装在http请求里,用post等方法)
    #直接用来筛选 分类 分页,跟在网址后面(通常用get)
    """查询条件（GET /teacher 的查询参数）"""
    id: int | None = Field(None, gt=0)
    name: str | None = Field(None, min_length=1, description='按姓名模糊查')
    class_id: int | None = Field(None, gt=0, description='按班级查老师：班主任和授课老师都算')
    role: Literal['head', 'subject'] | None = Field(
        None, description='head=只看班主任，subject=只看有授课班级的老师'
    )
    include_deleted: bool = Field(False, description='是否包含已逻辑删除的老师')


# ---------- 响应体 ----------

class TeacherDetail(TeacherCreate):
    """返回给前端的老师详情：在创建字段基础上加 id / 状态 / 时间戳"""
    id: int = Field(..., gt=0)
    is_deleted: int = Field(0, description='0=正常，1=已删除')
    deleted_at: datetime | None = Field(None)
    created_at: datetime = Field(..., description='创建时间')
    updated_at: datetime = Field(..., description='更新时间')


class Response(BaseModel):
    """统一响应外壳，告诉前端这次请求结果咋样"""
    code: int
    message: str


class TeacherResponse(Response):
    """老师接口的统一响应：data 支持单条 / 列表 / 空"""
    data: TeacherDetail | list[TeacherDetail] | None = None
