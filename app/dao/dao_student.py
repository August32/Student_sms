# 查询学⽣信息（⽀持按编号、姓名、班级等条件筛选）
from sqlalchemy import and_
from app.models.student import Student
from app.models.class_info import ClassInfo  # [整合·增] 学生-班级联动：校验班级存在、同步班级人数
from datetime import datetime
from app.utils.logger import get_logger  # [整合·改] 原来用 print 打错误，统一走项目日志
logger = get_logger(__name__)


#带班级id时校验班级真实存在且未删除。
# class_id 是学生和班级唯一的关联，悬空的 class_id 会让统计模块（按班级）、就业模块（按班级查）静默查不到人
def _check_class_exists(db, class_id):
    if class_id is None:
        return
    exists = (db.query(ClassInfo)
              .filter(ClassInfo.id == class_id, ClassInfo.is_deleted == 0)
              .first())
    if not exists:
        raise ValueError(f"班级不存在或已删除: {class_id}")


# classes.student_count 是冗余字段（模型注释写明"学生增删时需同步维护"），
# 但学生模块原先增删改都不维护它。这里每次学生变动后按实际人数重算一次，保证班级接口返回的人数不失真
def _refresh_class_student_count(db, class_id):
    if class_id is None:
        return
    real_count = (db.query(Student)
                  .filter(Student.class_id == class_id, Student.is_deleted == 0)
                  .count())
    class_info = db.query(ClassInfo).filter(ClassInfo.id == class_id).first()
    if class_info is not None:
        class_info.student_count = real_count


#获取学生列表
def dao_get_student_list(db, stu_id=None, name=None, class_id=None):
    query = db.query(Student).filter(Student.is_deleted == 0)
    if stu_id is not None:
        query = query.filter(Student.id == stu_id)  # 按编号精确筛
    if name:
        query = query.filter(Student.name.like(f'%{name}%'))  # 按姓名模糊筛，和老师模块口径一致
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)  # 按班级筛
    stu_list = query.all()  # .all() 转成列表，否则 Query 对象无法 JSON 序列化
    return stu_list
#创建新学生
def dao_add_student(db,student):
    data = student.model_dump(exclude_none=True)
    _check_class_exists(db, data.get("class_id"))
    try:
        student = Student(**data)
        db.add(student)
        db.commit()
        db.refresh(student)  # 回填数据库生成的id
        _refresh_class_student_count(db, student.class_id)  #新学生进班，班级人数重算
        db.commit()
        return student
    except Exception as e:
        # 交给全局异常兜底返回统一 500；None 只留给真正的业务失败
        logger.exception("新增学生落库失败 | name=%s", data.get("name"))
        db.rollback()
        raise
#获得特定学生信息
def dao_get_student_by_id(db,stu_id):
    student=db.query(Student).filter(Student.id==stu_id,Student.is_deleted==0).first()
    return student
#更新学生
def dao_update_student(db,stu_id,student):
    stu=dao_get_student_by_id(db,stu_id)
    if not stu:
        return None
    update_dict = student.values.model_dump(exclude_none=True, exclude=["id"])
    _check_class_exists(db, update_dict.get("class_id"))  #改班也要校验目标班级存在
    old_class_id = stu.class_id  #换班后原班级和新班级人数都要重算
    #更新字典里面所有要修改的字段，批量给 SQLAlchemy ORM 实例对象赋值，实现局部更新。
    for k, v in update_dict.items():
        setattr(stu, k, v)
    _refresh_class_student_count(db, old_class_id)  # 刷新老班级的人数
    _refresh_class_student_count(db, stu.class_id)  # 刷新新班级人数
    try:
        db.commit()
        db.refresh(stu)
    except Exception:
        logger.exception("更新学生落库失败 | id=%s", stu_id)
        db.rollback()
        raise
    return stu
#删除学生
def  dao_delete_student(db,stu_id):
    student = dao_get_student_by_id(db,stu_id)
    if not student:  # 找不到直接返回 None
        return None
    try:
        student.is_deleted = 1
        student.deleted_at = datetime.now()  # 获取删除时间
        _refresh_class_student_count(db, student.class_id)  # 学生离班，班级人数重算
        db.commit()
        return student
    except Exception:
        # 交给全局兜底；None 只表示真的不存在
        logger.exception("删除学生落库失败 | id=%s", stu_id)
        db.rollback()
        raise





# #多条件查找学生
# def batch_dao_get_students(db,student,is_deleted=0):
#     #得到SQLAlchemy Query 查询对象（未拼接查询条件）
#     query=db.query(Student)
#     #存储非空请求的查询条件
#     conditions=[]
#     if student.id is not None:
#         conditions.append(Student.id==student.id)
#     if student.name is not None:
#         conditions.append(Student.name == student.name)
#     # if student.class_name is not None:
#     #     conditions.append(Student.class_name == student.class_name)
#     if student.native_place is not None:
#         conditions.append(Student.native_place == student.native_place)
#     if student.graduate_school is not None:
#         conditions.append(Student.graduate_school == student.graduate_school)
#     if student.major is not None:
#         conditions.append(Student.major == student.major)
#     if student.education is not None:
#         conditions.append(Student.education == student.education)
#     if student.consultant_no is not None:
#         conditions.append(Student.consultant_no == student.consultant_no)
#     if student.age is not None:
#         conditions.append(Student.age == student.age)
#     if student.gender is not None:
#         conditions.append(Student.gender == student.gender)
#     if conditions:
#         conditions.append(Student.is_deleted==is_deleted)
#         #得到query对象，返回该对象，拼接该条件
#         query=query.filter(and_(*conditions))
#     return query
# #批量更新
# def batch_dao_update_student(db,filter_model,update_dict):
#     # 调用查询接口得到第一个对象
#     query = batch_dao_get_students(db,filter_model)
#     stu=query.first()
#     if not stu:
#         return None
#     for k, v in update_dict.items():
#         setattr(stu, k, v)  # 动态设置字段
#
#     db.commit()
#     # db.refresh,刷新stu对象，不用重新查一次
#     db.refresh(stu)
#     return stu
#单个删除/批量删除
# def batch_dao_delete_student(db,filter_model):
#     query = batch_dao_get_students(db, filter_model,0)
#     #方案1：单个删除:
#     # stu_list = query.all()
#     # if len(stu_list) == 0:
#     #     return None
#     # if len(stu_list) > 1:
#     #     raise ValueError("匹配多条数据，禁止删除")
#     # stu = stu_list[0]
#     # stu.is_deleted = 1
#     # db.refresh,刷新stu对象，不用重新查一次
#     # db.refresh(stu)
#     #方案2：批量删除
#     query.update( { 'is_deleted': 1,'deleted_at':datetime.now()} )
#     db.commit()
#     stu_list = query = batch_dao_get_students(db, filter_model,1)
#     if not stu_list:
#         return None
#     return stu_list
#增加
# def batch_dao_add_student(db,student):
#     try:
#         student = Student(**student.model_dump(exclude_none=True))
#         db.add(student)
#         db.commit()
#         db.refresh(student)  # 回填数据库生成的id
#         return student
#     except Exception as e:
#         db.rollback()
#         print(e)
#         return None
