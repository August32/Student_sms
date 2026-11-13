from datetime import datetime

from sqlalchemy.exc import IntegrityError  # [异常·增] 唯一键冲突（重复班级名）单独识别
from sqlalchemy.orm import Session

from app.models.class_info import ClassInfo
from app.schemas.class_info import ClassInfoQuery, ClassInfoCreate, ClassInfoUpdate, ClassInfoDelete
from app.utils.logger import get_logger  # [日志·增] DAO 异常原先静默 raise，500 错误在日志里无痕迹

logger = get_logger(__name__)  # [日志·增]

# 按照班级名称、班主任、班级状态、开课时间、班级人数等信息查询班级信息
# 最后返回所有符合条件的班级
def query_class_infos(db:Session,params:ClassInfoQuery):
    query=(db.query(ClassInfo) #返回的是 Query 对象,不是结果
           .filter(ClassInfo.is_deleted==0)) #逻辑删除过滤，只查没有被软删除的数据
    if params.class_name is not None: #判断：前端有没有传班级名称，不为空才加这个条件
        query=query.filter(ClassInfo.class_name==params.class_name)
     #query = query.filter(...) 重新赋值
    if params.class_teacher is not None:  #班主任名字
        query=query.filter(ClassInfo.class_teacher==params.class_teacher)

    if params.class_status is not None:  #班级状态
        query=query.filter(ClassInfo.class_status==params.class_status)

    if params.class_time_start is not None: #前端传了【开课起始时间】：班级开课时间 >= 这个起始时间（从这天及以后的班级）
        query = query.filter(ClassInfo.class_time >= params.class_time_start)

    if params.class_time_end is not None: #班级开课时间 <= 这个结束时间（到这天及之前的班级）
        query = query.filter(ClassInfo.class_time <= params.class_time_end)

    if params.min_student_count is not None: #前端传了最小人数：班级人数 >= 最小人数
        query = query.filter(ClassInfo.student_count >= params.min_student_count)

    if params.max_student_count is not None: #班级人数 <= 最小人数
        query = query.filter(ClassInfo.student_count <= params.max_student_count)

    return query.all()


# 新增班级信息
def create_class_info(db:Session,params:ClassInfoCreate): # 把前端入参（Pydantic模型）组装成数据库ORM对象
    class_info=ClassInfo(      #组建ORM对象
        class_name=params.class_name,
        class_teacher=params.class_teacher,
        class_status=params.class_status,
        class_time=params.class_time,
        student_count=params.student_count
    )
    try:
        db.add(class_info)#把 ORM 对象 加入当前数据库会话的待提交队列
        db.commit()#提交事务,真正写入数据库
        db.refresh(class_info)#从数据库重新查询这条刚插入的记录，拿到数据库自动生成的id、创建时间
        return class_info #返回刷新后的完整 ORM 对象，包含数据库生成的 id、创建时间等字段，供上层接口返回给前端。
    except IntegrityError:
        # [异常·增] class_name 有唯一约束：重复建同名班级原来直接裸 500，转成业务提示
        logger.warning("新增班级被拒 | 班级名重复 class_name=%s", params.class_name)
        db.rollback()
        raise ValueError(f"班级已存在: {params.class_name}")
    except Exception:
        logger.exception("新增班级落库失败 | class_name=%s", params.class_name)  # [日志·增] 记异常堆栈再上抛
        db.rollback() # 失败回滚，撤销本次修改
        raise    #向上抛出异常，交给上层处理

# 修改班级信息
def update_class_info(class_name:str, db: Session, params: ClassInfoUpdate):
# - `class_name: int`：要修改的班级名称
# - `db: Session`：数据库会话，用来查询、提交事务
# - `params: ClassInfoUpdate`：更新参数对象（Pydantic 模型），里面所有字段都是**可选**的，前端传什么就改什么，没传的就是 `None`
# > 对应你之前学的 `BookCreate`，这里 `ClassInfoUpdate` 专门用于修改，字段一般都设为可选（`Optional` / `| None`）。
    class_info = (db.query(ClassInfo) #构造查询，目标表是班级表
                  .filter(ClassInfo.class_name==class_name,#按班级名字精准定位某一条
                   ClassInfo.is_deleted==0)#只查未删除的数据（逻辑删除保护）
                  .first()#取第一条匹配结果，找到返回 ORM 对象，找不到返回 `None`
                  )
    if class_info is None:
        return None #如果没找到对应班级（名字错了 / 已经被删除），直接返回 `None`
    if params.class_name is not None:
        class_info.class_name=params.class_name
    if params.class_teacher is not None:#通过 `is not None` 判断：只有传了的字段才覆盖原值，没传的保持数据库原来的值
        class_info.class_teacher=params.class_teacher
    if params.class_status is not None:
        class_info .class_status=params.class_status
    if params.class_time is not  None:
        class_info.class_time=params.class_time
    # if params.student_count is not None:
    #     class_info.student_count = params.student_count
    try:
        db.commit()#注意：更新不需要 `db.add()`！
# 因为这个 `class_info` 是从数据库查出来的，本来就在 Session 托管状态，直接改属性，`commit` 就会自动生成 update 语句
        db.refresh(class_info)
        return class_info
    except IntegrityError:
        # [异常·增] 改名撞上已有班级名（唯一约束）也转成业务提示，不再裸 500
        logger.warning("修改班级被拒 | 班级名重复 class_name=%s", params.class_name or class_name)
        db.rollback()
        raise ValueError(f"班级已存在: {params.class_name or class_name}")
    except Exception:#异常回滚
        logger.exception("修改班级落库失败 | class_name=%s", class_name)  # [日志·增]
        db.rollback()
        raise


# 删除班级信息（软删除：is_deleted 标成 1 并记下删除时间，数据还在表里、随时可恢复）
def delete_class_info(db:Session,params:ClassInfoDelete):
    class_info=(db.query(ClassInfo)
                .filter(ClassInfo.class_name==params.class_name,
                ClassInfo.is_deleted==0)
                .first()
                )
    if class_info is None:
        return None
    class_info.is_deleted=1
    class_info.deleted_at=datetime.now()
    try:
        db.commit()
        db.refresh(class_info) # 把数据库生成的字段重新加载到 Python 对象中
        return class_info
    except Exception:  # 提交失败事务回滚
        logger.exception("删除班级落库失败 | class_name=%s", params.class_name)  # [日志·增]
        db.rollback()
        raise









