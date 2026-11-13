from datetime import date  # [整合·增] 入学/毕业时间是日期类型
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class Gender(str, Enum):
    male = "男"
    female = "女"

# 新增学员请求体
class StudentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(min_length=1)
    # 创建学生带不上班级 → 学生和班级关联断裂 → 统计(按班级)、就业(按班级查)全查不到人，三个模块一起哑掉
    class_id: int | None = Field(None, gt=0, description="学生班级id，关联 classes.id")
    enroll_time: date | None = Field(None, description="入学时间")
    graduate_time: date | None = Field(None, description="毕业时间")
    native_place: str | None = Field(None, min_length=1)
    graduate_school: str | None = Field(None, min_length=1)
    major: str | None = Field(None, min_length=1)
    education: str | None = Field(None, min_length=1)
    consultant_no: str | None = Field(None, min_length=1)
    age: int | None = Field(None, gt=0)
    gender: Gender | None = Field(None)

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

# 查询筛选条件（新增基础上增加id）
class StudentRequest(StudentCreate):
    id: int | None = Field(None, gt=0)

# 更新的values：不锁死id字段，而是更新的时候 model_dump(exclude=["id"]) 剔除（更推荐）
class StudentUpdate(StudentCreate):
    pass

# 更新请求体：筛选条件 + 更新值
class StudentUpdateRequest(BaseModel):
    # filters: StudentRequest
    values: StudentUpdate

# 删除请求体
class StudentDeleteRequest(BaseModel):
    filters: StudentRequest

# 出参模型，序列化ORM
class StudentDetail(StudentRequest):
    pass

# 统一外层返回
class Response(BaseModel):
    code: int
    message: str

class StudentResponse(Response):
    data: StudentDetail | list[StudentDetail] | None = None
