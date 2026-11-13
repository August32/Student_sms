# DAO 层负责数据库查询和事务处理
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.student import Student
from app.models.employment import Employment
from app.schemas.employment import EmploymentCreate, EmploymentQuery
from app.utils.logger import get_logger  # DAO 异常原先静默 raise，500 错误在日志里无痕迹

logger = get_logger(__name__)  # [日志·增]

# 通过学生id获取学生就业信息
def query_employment_by_student_dao(
    db: Session,
    student_id: int
):
    employment = (
        db.query(Employment)
        .filter(
            Employment.student_id == student_id,
            Employment.is_deleted == 0  # 通过 is_deleted 过滤已删除数据
        )
        .first()
    )

    return employment

# 通过班级id获取班级学生就业信息
def query_employment_by_class_dao(
    db: Session,
    class_id: int
):
    employment_list = (
        db.query(Employment)
        .join(
            Student,
            Employment.student_id == Student.id
        )
        .filter(
            Student.class_id == class_id,
            Student.is_deleted == 0,
            Employment.is_deleted == 0
        )
        .all()
    )

    return employment_list

# 添加或更新就业信息
def create_or_update_employment_dao(
    db: Session,
    student_id: int,
    params: EmploymentCreate
):
    # 1. 先判断学生是否存在
    student = (
        db.query(Student)
        .filter(
            Student.id == student_id,
            Student.is_deleted == 0
        )
        .first()
    )

    # 不存在直接返回 None 给上层 API，抛出 404
    if student is None:
        return None

    # 2. 查询该学生是否有就业记录
    employment = (
        db.query(Employment)
        .filter(
            Employment.student_id == student_id,
            Employment.is_deleted == 0
        )
        .first()
    )

    try:
        if employment is None:
            # 3. 没有就业记录，新增
            employment = Employment(
                student_id=student_id,
                employment_open_date=(
                    params.employment_open_date
                ),
                offer_date=params.offer_date,
                company_name=params.company_name,
                salary=params.salary
            )

            db.add(employment)

        else:
            # 4. 已有就业记录，只更新请求中值不为 None 的字段
            if params.company_name is not None:
                employment.company_name = params.company_name

            if params.salary is not None:
                employment.salary = params.salary

            if params.offer_date is not None:
                employment.offer_date = params.offer_date

            if params.employment_open_date is not None:
                employment.employment_open_date = (
                    params.employment_open_date
                )

        # 更新时间
        employment.updated_at = datetime.now()

        # 5. 提交数据库
        db.commit()

        # 6. 重新加载数据库生成的 id
        db.refresh(employment)

        return employment

    except Exception:
        # 出错时回滚，避免当前 Session 处于不可继续使用的异常状态
        logger.exception("添加/更新就业信息落库失败 | student_id=%s", student_id)  # [日志·增] 记异常堆栈再上抛
        db.rollback()
        raise

# 删除学生就业信息
def delete_employment_dao(employment_id: int, db: Session):
    employment = (
        db.query(Employment)
        .filter(
            Employment.id == employment_id,
            Employment.is_deleted == 0
        )
        .first()
    )

    if employment is None:
        return None

    try:
        employment.is_deleted = 1
        employment.deleted_at = datetime.now()
        db.commit()
        return employment

    except Exception:
        logger.exception("删除就业信息落库失败 | id=%s", employment_id)  # [日志·增]
        db.rollback()
        raise

# 按照学生编号，公司名字，工资范围等信息查询学生就业信息
# 采用动态条件查询：只有当请求参数不为空时才追加对应过滤条件，
# 因此同一个接口可以支持按学生、公司、工资和日期组合查询。
def query_employments_dao(db:Session, params:EmploymentQuery):
    query = (db.query(Employment)
             .filter(Employment.is_deleted==0))

    if params.student_id is not None:
        query = query.filter(Employment.student_id == params.student_id)

    if params.company_name is not None:
        # 公司名称使用模糊匹配
        query = query.filter(Employment.company_name.like(f'%{params.company_name}%'))

    if params.min_salary is not None:
        query = query.filter(Employment.salary >= params.min_salary)

    if params.max_salary is not None:
        query = query.filter(Employment.salary <= params.max_salary)

    if params.employment_open_date_start is not None:
        query = query.filter(Employment.employment_open_date >= params.employment_open_date_start)

    if params.employment_open_date_end is not None:
        query = query.filter(Employment.employment_open_date <= params.employment_open_date_end)

    if params.offer_date_start is not None:
        query = query.filter(Employment.offer_date >= params.offer_date_start)

    if params.offer_date_end is not None:
        query = query.filter(Employment.offer_date <= params.offer_date_end)

    return query.all()

# [整合·注] 下面的新增/修改就业 DAO 是旧版独立接口的实现，已被 create_or_update_employment_dao 的
# upsert 取代（需求 4.3 写的是 POST /employment/students/{id} 添加/更新），保留作参考不再使用
#
# # 新增学生就业信息
# def create_employment_dao(db:Session, params:EmploymentCreate):
#     employment = Employment(
#         student_id = params.student_id,
#         employment_open_date = params.employment_open_date,
#         offer_date = params.offer_date,
#         company_name = params.company_name,
#         salary = params.salary
#     )
#     try:
#         db.add(employment)
#         employment.created_at = datetime.now()
#         db.commit()
#         db.refresh(employment) #把数据库生成的字段重新加载到 Python 对象中
#         return employment
#     # 提交失败任务回滚
#     except Exception:
#         db.rollback()
#         raise
#
# 修改学生就业信息
# def update_employment_dao(employment_id: int, db:Session, params:EmploymentUpdate):
#     employment = (db.query(Employment)
#         .filter(Employment.id == employment_id,
#                 Employment.is_deleted == 0)
#         .first())
#     if employment is None:
#         return None
#
#     if params.company_name is not None:
#         employment.company_name = params.company_name
#
#     if params.salary is not None:
#         employment.salary = params.salary
#
#     if params.offer_date is not None:
#         employment.offer_date = params.offer_date
#
#     if params.employment_open_date is not None:
#         employment.employment_open_date = (
#             params.employment_open_date
#         )
#
#     try:
#         employment.updated_at = datetime.now()
#         db.commit()
#         db.refresh(employment)
#         return employment
#
#     except Exception:
#         db.rollback()
#         raise
