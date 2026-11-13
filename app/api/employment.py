from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dao.dao_employment import (
    create_or_update_employment_dao,
    query_employment_by_student_dao,
    query_employment_by_class_dao,
    query_employments_dao,
    delete_employment_dao
)
from app.schemas.employment import (
    EmploymentResponse,
    EmploymentCreate,
    EmploymentQuery,
    DeleteResponse
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 按照学生编号、公司名称、工资范围等查询就业信息
emp_router = APIRouter()

# 获取学生就业信息
@emp_router.get(
    "/employment/students/{student_id}",
    response_model=EmploymentResponse
)
def get_student_employment_api(
    student_id: int,
    db: Session = Depends(get_db)
):
    employment = query_employment_by_student_dao(
        db=db,
        student_id=student_id
    )

    if employment is None:
        logger.warning("查询就业信息未命中 | student_id=%s", student_id)  # [日志·增] 单条查询只记未命中
        raise HTTPException(
            status_code=404,
            detail="该学生暂无就业信息"
        )

    return {
        "code": 200,
        "message": "查询成功",
        "data": employment
    }

# 获取班级学生就业信息
@emp_router.get(
    "/employment/class/{class_id}",
    response_model=EmploymentResponse
)
def get_class_employment_api(
    class_id: int,
    db: Session = Depends(get_db)
):
    # 调用dao层去数据库查数据
    employment_list = query_employment_by_class_dao(
        db=db,
        class_id=class_id
    )
    # 业务日志：记录查询条件、返回条数（监控、排错）
    logger.info("查询班级就业信息 | class_id=%s | 返回 %d 条", class_id, len(employment_list))

    return {
        "code": 200,
        "message": "查询成功",
        "data": employment_list
    }


# 新增/更新就业信息
@emp_router.post(
    "/employment/students/{student_id}",
    response_model=EmploymentResponse
)
def create_or_update_student_employment_api(
    student_id: int,
    params: EmploymentCreate,
    db: Session = Depends(get_db)
):
    employment = create_or_update_employment_dao(
        db=db,
        student_id=student_id,
        params=params
    )

    if employment is None:
        logger.warning("添加/更新就业信息被拒 | 学生不存在 student_id=%s", student_id)  # [日志·增] 联动校验被拦
        raise HTTPException(
            status_code=404,
            detail="学生不存在"
        )

    logger.info("添加/更新就业信息成功 | student_id=%s company=%s salary=%s",
                student_id, employment.company_name, employment.salary)  # [日志·增]

    return {
        "code": 200,
        "message": "添加或更新成功",
        "data": employment
    }

# 删除学生就业信息
@emp_router.delete(
    "/employment/{employment_id}",
    response_model=DeleteResponse
)
def delete_employment_api(
    employment_id: int,
    db: Session = Depends(get_db)
):
    employment = delete_employment_dao(
        employment_id=employment_id,
        db=db
    )

    if employment is None:
        logger.warning("删除就业信息未命中 | id=%s", employment_id)  # [日志·增]
        raise HTTPException(
            status_code=404,
            detail="就业信息不存在"
        )

    logger.info("删除就业信息成功 | id=%s student_id=%s", employment_id, employment.student_id)  # [日志·增]

    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }

# 按照学生编号、公司名字、工资范围查询学生就业信息
@emp_router.get(
    "/employment",
    response_model=EmploymentResponse
)
async def get_employments_api(
    params: EmploymentQuery = Depends(),
    db: Session = Depends(get_db)
):
    employment_list = query_employments_dao(
        db=db,
        params=params
    )

    logger.info("条件查询就业信息 | student_id=%s company=%s 薪资[%s~%s] | 返回 %d 条",
                params.student_id, params.company_name, params.min_salary, params.max_salary,
                len(employment_list))  # [日志·增] 条件查询记筛选条件和条数

    return {
        "code": 200,
        "message": "返回成功",
        "data": employment_list
    }

#
# # 新增学生就业信息
# @emp_router.post(
#     "/employment",
#     response_model=EmploymentResponse
# )
# async def create_employments_api(
#     params: EmploymentCreate,
#     db: Session = Depends(get_db)
# ):
#     employment = create_employment_dao(
#         db=db,
#         params=params
#     )
#
#     return {
#         "code": 201,
#         "message": "新增成功",
#         "data": employment
#     }
#
#
# # 修改学生就业信息
# @emp_router.put(
#     "/employment/{employment_id}",
#     response_model=EmploymentResponse
# )
# def update_employment_api(
#     employment_id: int,
#     params: EmploymentUpdate,
#     db: Session = Depends(get_db)
# ):
#     employment = update_employment_dao(
#         employment_id=employment_id,
#         db=db,
#         params=params
#     )
#
#     if employment is None:
#         raise HTTPException(
#             status_code=404,
#             detail="就业信息不存在"
#         )
#
#     return {
#         "code": 200,
#         "message": "修改成功",
#         "data": employment
#     }
#
#
