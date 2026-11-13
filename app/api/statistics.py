# 统计分析接口
# GET /statistics/age-over-30           超过30岁的学员信息
# GET /statistics/class-gender-count    每个班级人数及男女生人数
# GET /statistics/all-over-80           每次考试都在80分以上的学生
# GET /statistics/multi-fail            两次以上不及格的学生
# GET /statistics/class-exam-avg        每次考试每个班级的平均分
# GET /statistics/salary-top5           就业薪资最高的前五名
# GET /statistics/employment-duration   每个学生的就业时长
# GET /statistics/class-avg-duration    每个班级的平均就业时长
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.logger import get_logger
from app.core.database import get_db

from app.dao.dao_statistics import (query_salary_top5, query_student_duration, query_class_avg_duration,
                                    query_students_over30, query_class_gender_count,
                                    query_students_all_over80, query_students_multi_fail, query_class_exam_avg)
from app.schemas.statistics import (SalaryTopResponse, StudentDurationResponse, ClassAvgDurationResponse,
                                    Over30StudentResponse, ClassGenderCountResponse,
                                    AllOver80Response, MultiFailResponse, ClassExamAvgResponse)

logger = get_logger(__name__)

stat_router = APIRouter(prefix="/statistics")


# 1. 就业薪资最高的前 N 名学生：姓名、班级、就业时间、就业公司
# 查询参数：top_n 前几名（默认 5）；class_id/class_name 按班级筛
@stat_router.get('/salary-top5', response_model=SalaryTopResponse)
async def get_salary_top5(top_n: int = 5,
                          class_id: int | None = None,
                          class_name: str | None = None,
                          db: Session = Depends(get_db)):
    logger.info("收到薪资前N名统计请求 | top_n=%s class_id=%s class_name=%s", top_n, class_id, class_name)
    try:
        data = query_salary_top5(db=db, top_n=top_n, class_id=class_id, class_name=class_name)
        logger.info("薪资前N名统计成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("薪资前N名统计失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}


# 2. 每个学生的就业时长（offer下发时间 - 就业开放时间）
# 查询参数：class_id/class_name 按班级筛
@stat_router.get('/employment-duration', response_model=StudentDurationResponse)
async def get_employment_duration(class_id: int | None = None,
                                  class_name: str | None = None,
                                  db: Session = Depends(get_db)):
    logger.info("收到学生就业时长统计请求 | class_id=%s class_name=%s", class_id, class_name)
    try:
        data = query_student_duration(db=db, class_id=class_id, class_name=class_name)
        logger.info("学生就业时长统计成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("学生就业时长统计失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}


# 3. 每个班级的平均就业时长（只统计进入就业阶段的学生）
# 查询参数：class_id/class_name 按班级筛
@stat_router.get('/class-avg-duration', response_model=ClassAvgDurationResponse)
async def get_class_avg_duration(class_id: int | None = None,
                                 class_name: str | None = None,
                                 db: Session = Depends(get_db)):
    logger.info("收到班级平均就业时长统计请求 | class_id=%s class_name=%s", class_id, class_name)
    try:
        data = query_class_avg_duration(db=db, class_id=class_id, class_name=class_name)
        logger.info("班级平均就业时长统计成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("班级平均就业时长统计失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}

# 4. 查询所有超过 N 岁的学员的信息
# 查询参数：min_age 年龄阈值（默认 30）；class_id/class_name 按班级筛
@stat_router.get('/age-over-30', response_model=Over30StudentResponse)
async def get_students_over30(min_age: int = 30,
                              class_id: int | None = None,
                              class_name: str | None = None,
                              db: Session = Depends(get_db)):
    logger.info("收到超过N岁学员查询请求 | min_age=%s class_id=%s class_name=%s", min_age, class_id, class_name)
    try:
        data = query_students_over30(db=db, min_age=min_age, class_id=class_id, class_name=class_name)
        logger.info("超过N岁学员查询成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("超过N岁学员查询失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}


# 5. 统计每个班级的人数以及男生女生的人数
# 查询参数：class_id/class_name 按班级筛
@stat_router.get('/class-gender-count', response_model=ClassGenderCountResponse)
async def get_class_gender_count(class_id: int | None = None,
                                 class_name: str | None = None,
                                 db: Session = Depends(get_db)):
    logger.info("收到班级人数统计请求 | class_id=%s class_name=%s", class_id, class_name)
    try:
        data = query_class_gender_count(db=db, class_id=class_id, class_name=class_name)
        logger.info("班级人数统计成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("班级人数统计失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}


# 6. 查询每次考试成绩都在80分以上的学生的编号、姓名和成绩
@stat_router.get('/all-over-80', response_model=AllOver80Response)
async def get_students_all_over80(db: Session = Depends(get_db)):
    logger.info("收到80分以上学生查询请求")
    try:
        data = query_students_all_over80(db=db)
        logger.info("80分以上学生查询成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("80分以上学生查询失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}  # [异常·改] 原来 f"统计失败: {e}" 把内部异常原文漏给前端，堆栈日志里已有，固定文案


# 7. 查询两次以上不及格的学生的姓名、班级和不及格成绩
@stat_router.get('/multi-fail', response_model=MultiFailResponse)
async def get_students_multi_fail(db: Session = Depends(get_db)):
    logger.info("收到多次不及格学生查询请求")
    try:
        data = query_students_multi_fail(db=db)
        logger.info("多次不及格学生查询成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("多次不及格学生查询失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}  # [异常·改] 原来 f"统计失败: {e}" 把内部异常原文漏给前端，堆栈日志里已有，固定文案


# 8. 统计每次考试每个班级的平均分，按照从高到低排序
@stat_router.get('/class-exam-avg', response_model=ClassExamAvgResponse)
async def get_class_exam_avg(db: Session = Depends(get_db)):
    logger.info("收到班级考试平均分统计请求")
    try:
        data = query_class_exam_avg(db=db)
        logger.info("班级考试平均分统计成功 | 返回 %d 条", len(data))
        return {"code": 200,
                "message": "返回成功",
                "data": data}
    except Exception:
        logger.exception("班级考试平均分统计失败")
        return {"code": 500, "message": "统计失败，请查看 logs/app.log", "data": []}  # [异常·改] 原来 f"统计失败: {e}" 把内部异常原文漏给前端，堆栈日志里已有，固定文案