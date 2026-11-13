
from pydantic import BaseModel,Field
from datetime import datetime
from pydantic import ConfigDict


class ClassInfoQuery(BaseModel): #查询请求体：按条件筛选班级
    class_name:str|None=Field(default=None,min_length=2,max_length=30,description="班级名称")
    class_teacher: str | None = Field(default=None, min_length=2, max_length=30, description="班主任名字")
    class_time_start:datetime | None=Field(default=None,description="开课日期-起")
    class_time_end: datetime | None = Field(default=None, description="开课日期-止")
    class_status:str |None=Field(default=None,min_length=2,max_length=16,description="班级状态（未开课/进行中/已结课）")
    min_student_count:int |None=Field(default=None,ge=0,description="班级学生人数下限")
    max_student_count: int | None = Field(default=None, ge=0, description="班级人数上限")


class ClassInfoCreate(BaseModel): #新增请求体：新增班级提交的数据
    class_name: str = Field(min_length=2, max_length=30, description="班级名称")
    class_time: datetime = Field(description="开课日期")
    class_teacher: str = Field(min_length=2, max_length=30, description="班主任名字")
    class_status: str  = Field(default="未开课", min_length=2, max_length=16,description="班级状态（未开课/进行中/已结课）")
    student_count: int  = Field(default=0, ge=0, description="班级学生人数")


class ClassInfoUpdate(BaseModel): #修改请求体：全部可选，传哪个字段就改哪个
    # class_id: int | None = Field(default=None,description="班级")
    class_name:str|None=Field(default=None,min_length=2,max_length=30,description="班级名称")
    class_time:datetime | None=Field(default=None,description="开课日期")
    class_teacher:str | None=Field(default=None,min_length=2,max_length=30,description="班主任名字")
    class_status:str |None=Field(default=None,min_length=2,max_length=16,description="班级状态（未开课/进行中/已结课）")
    student_count:int |None=Field(default=None,ge=0,description="班级学生人数")


class ClassInfoDelete(BaseModel): #删除请求体：软删除指定班级
    class_name:str = Field(min_length=1, max_length=30, description="要删除的班级名字")

class ClassInfoDetail(ClassInfoCreate):#响应数据：完整班级信息（支持直接把 SQLAlchemy ORM 对象丢进来自动映射字段）
    model_config = ConfigDict(from_attributes=True)
    id:int = Field(ge=0,description="班级ID")
    created_at:datetime | None = Field(default=None,description="创建时间")
    updated_at:datetime | None = Field(default=None,description="更新时间")

class ClassInfoResponse(BaseModel):  #统一返回体：code + message + data（路由的 response_model 用它）
    code: int
    message: str
    data: ClassInfoDetail | list[ClassInfoDetail] | None


