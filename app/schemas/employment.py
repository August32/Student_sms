# Schema 层负责请求参数校验和响应结构约束
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


# 接收新增或更新参数
class EmploymentCreate(BaseModel):
    employment_open_date: date | None = None
    offer_date: date | None = None
    company_name: str | None = Field(default=None, min_length=1, max_length=100)
    salary: Decimal | None = Field(default=None, ge=0)

# 支持多条件组合查询
class EmploymentQuery(BaseModel):
    student_id: int | None = Field(default=None, gt=0, description='学生编号')
    company_name: str | None = Field(default=None, min_length=1, max_length=100, description='就业公司名称（模糊匹配）')
    min_salary: Decimal | None = Field(default=None, ge=0, description='最低工资')
    max_salary: Decimal | None = Field(default=None, ge=0, description='最高工资')
    employment_open_date_start: date | None = Field(default=None, description='就业开放起始时间')
    employment_open_date_end: date | None = Field(default=None, description='就业开放结束时间')
    offer_date_start: date | None = Field(default=None, description='Offer 下发起始日期')
    offer_date_end: date | None = Field(default=None, description='Offer 下发结束日期')

# 约束返回格式
class EmploymentDetail(BaseModel):
    id: int
    student_id: int
    employment_open_date: date | None = None
    offer_date: date | None = None
    company_name: str | None = Field(default=None, min_length=1, max_length=100)
    salary: Decimal | None = Field(default=None, ge=0)

    # 允许 Pydantic 去读取 ORM 对象的 .属性，不用 ORM 是字典才能解析
    model_config = ConfigDict(from_attributes=True)

class Response(BaseModel):
    code:int
    message:str

class EmploymentResponse(Response):
    data: list[EmploymentDetail] | EmploymentDetail | None

# 删除
class DeleteResponse(Response):
    data : None = None


# 更新
# class EmploymentUpdate(BaseModel):
#     employment_open_date: date | None = None
#     offer_date: date | None = None
#     company_name: str | None = Field(default=None, min_length=1, max_length=100)
#     salary: Decimal | None = Field(default=None,ge=0)

