
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


# 统一外层返回结构：code + message + data
class Response(BaseModel):
    code: int
    message: str


# ---------- 1. 就业薪资最高的前五名 ----------
# 需求：姓名、班级、就业开放时间、offer下发时间、就业公司、就业薪资
class SalaryTopItem(BaseModel):
    name: str                                        # 学生姓名
    class_name: str                                  # 班级
    employment_open_date: date | None = None         # 就业开放时间
    offer_date: date | None = None                   # offer下发时间
    company_name: str | None = None                  # 就业公司
    salary: Decimal | None = None                    # 就业薪资


class SalaryTopResponse(Response):
    data: list[SalaryTopItem]


# ---------- 2. 每个学生的就业时长 ----------
# 需求：就业时长 = offer下发时间 - 就业开放时间
class StudentDurationItem(BaseModel):
    student_id: int                                  # 学生编号
    name: str                                        # 学生姓名
    employment_open_date: date | None = None         # 就业开放时间
    offer_date: date | None = None                   # offer下发时间
    duration_days: int | None = None                 # 就业时长（天），时间不全就是 None


class StudentDurationResponse(Response):
    data: list[StudentDurationItem]


# ---------- 3. 每个班级的平均就业时长 ----------
# 需求：只统计进入就业阶段的学生（有就业开放时间）
class ClassAvgDurationItem(BaseModel):
    class_name: str                                  # 班级
    student_count: int                               # 参与统计的学生数
    avg_duration_days: float | None = None           # 平均就业时长（天），保留 1 位小数


class ClassAvgDurationResponse(Response):
    data: list[ClassAvgDurationItem]


# ---------- 4. 超过30岁的学员信息 ----------
# 需求：查询所有超过30岁的学员的信息
class Over30StudentItem(BaseModel):
    id: int                                          # 学生编号
    name: str                                        # 学生姓名
    class_name: str | None = None                    # 学生班级
    age: int | None = None                           # 年龄
    gender: str | None = None                        # 性别
    native_place: str | None = None                  # 籍贯
    graduate_school: str | None = None               # 毕业院校
    major: str | None = None                         # 专业
    education: str | None = None                     # 学历
    consultant_no: str | None = None                 # 顾问编号
    enroll_time: date | None = None                  # 入学时间
    graduate_time: date | None = None                # 毕业时间


class Over30StudentResponse(Response):
    data: list[Over30StudentItem]


# ---------- 5. 每个班级的人数以及男生女生的人数 ----------
class ClassGenderCountItem(BaseModel):
    class_name: str                                  # 班级
    total_count: int                                 # 班级总人数
    male_count: int                                  # 男生人数（gender='男'）
    female_count: int                                # 女生人数（gender='女'）

class ClassGenderCountResponse(Response):
    data: list[ClassGenderCountItem]








# ---------- 6. 每次考试都在80分以上的学生 ----------
class ExamScoreItem(BaseModel):
    exam_sequence: int  # 考核序次
    score: float  # 本次成绩

class AllOver80Item(BaseModel):
    student_id: int  # 学生编号
    name: str  # 学生姓名
    scores: list[ExamScoreItem]  # 各次成绩（全部在80分以上）

class AllOver80Response(Response):
    data: list[AllOver80Item]

# ---------- 7. 两次以上不及格的学生 ----------
class FailScoreItem(BaseModel):
    exam_sequence: int  # 考核序次
    score: float  # 不及格成绩（<60 分）

class MultiFailItem(BaseModel):
    name: str  # 学生姓名
    class_name: str  # 班级
    fail_scores: list[FailScoreItem]  # 不及格的那几次成绩

class MultiFailResponse(Response):
    data: list[MultiFailItem]

# ---------- 8. 每次考试每个班级的平均分 ----------
class ClassExamAvgItem(BaseModel):
    exam_sequence: int  # 考核序次
    class_name: str  # 班级
    avg_score: float  # 平均分（保留 1 位小数）
    student_count: int  # 参与统计的人数

class ClassExamAvgResponse(Response):
    data: list[ClassExamAvgItem]