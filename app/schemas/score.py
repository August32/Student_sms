
from datetime import date
# datetime.date 是 Python 内置的“纯日期”类型（只有年月日，没有时分秒）。
# 用来声明 exam_date 字段的类型。Pydantic 校验时会自动把
# JSON 里的 "2026-11-08" 这种字符串解析成 date 对象；格式不对直接 422。

# ---------- 第三方库导入（Pydantic：最流行的数据校验库） ----------
from pydantic import BaseModel, Field, ConfigDict
# BaseModel：所有校验模型的基类。继承它之后，类就具备了
#            “自动校验、自动转换类型、自动报错”的能力。
# Field：    字段的“详细说明书”。可以给字段设默认值、取值范围、
#            描述文字（会出现在 Swagger 文档里）。
# ConfigDict：模型的全局配置项容器（这里用来开启 from_attributes）。

from typing import List, Union
# ==================== 请求体模型 ====================
class ScoreRequest(BaseModel):
    #是让 Pydantic 模型能直接接收 SQLAlchemy 的 ORM 对象，把数据库查询结果自动转换成响应模型，不用手动逐字段赋值。
    model_config = ConfigDict(from_attributes=True)
    student_id:int | None = Field(None,gt=0,description='学生ID,外键关联学生表')
    exam_sequence:int | None = Field(None,gt=0,description='考核序次，第几次考核，必须大于0')
    score:float | None = Field(None,ge=0,le=100,description='考核成绩，0~100分')
    exam_date:date | None = Field(None,description='考核日期') #格式 YYYY-MM-DD
    remark:str | None = Field(None,max_length=200,description='成绩备注')
# ==================== 响应体模型 ====================
class ScoreDetail(ScoreRequest):
    id: int | None = Field(None, gt=0)  # 成绩记录主键 ID
    # id 是数据库自增主键，只有“查询出来/新建成功”后才有值，
class Response(BaseModel):
    """统一响应格式，和其他模块保持一致。"""
    code: int  # 业务状态码：200 成功 / 201 录入成功 / 400 参数缺失 / 404 未找到 / 409 重复录入
    message: str  # 提示信息：给人看的文字，如"录入成功""没有匹配到成绩"
class ScoreResponse(Response):
    data: (
            ScoreRequest          # 形态1：一条成绩（请求体结构，不含 id）
            | list[ScoreRequest]  # 形态2：成绩列表（不含 id）
            | None                # 形态3：没有数据（删除成功、查询无结果）
            | ScoreDetail         # 形态4：一条成绩详情（含数据库 id）
            | list[ScoreDetail]   # 形态5：成绩详情列表（含 id，查询接口用）
    )
