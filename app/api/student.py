from fastapi import APIRouter,Depends,HTTPException
from app.core.database import get_db
from app.schemas.student import StudentCreate,StudentRequest, StudentResponse,StudentUpdateRequest,StudentDetail,StudentDeleteRequest
# from app.dao.dao_student import batch_dao_get_students,batch_dao_update_student,batch_dao_delete_student,batch_dao_add_student
from app.dao.dao_student import *
from app.utils.logger import get_logger
logger=get_logger(__name__)
# 查询学⽣信息（⽀持按编号、姓名、班级等条件筛选）
stu_router=APIRouter()
@stu_router.get('/student',response_model=StudentResponse,description='学生列表，支持按编号/姓名/班级筛选')
async def get_student_list(stu_id: int | None = None,
                           name: str | None = None,
                           class_id: int | None = None,
                           db=Depends(get_db)):
    #  需求 2.1：按编号、姓名、班级等条件筛选
    stu_list=dao_get_student_list(db, stu_id=stu_id, name=name, class_id=class_id)
    logger.info("查询学生列表 | stu_id=%s name=%s class_id=%s | 返回 %d 条", stu_id, name, class_id, len(stu_list))  # [日志·增] 列表查询记条数
    return StudentResponse(code=200,message='返回成功',data=stu_list)
#创建新学生
@stu_router.post("/student", response_model=StudentResponse,description='创建新学生')
async def add_student(student: StudentCreate, db=Depends(get_db)):
    try:
        res = dao_add_student(db, student)
    except ValueError as error:  #  学生-班级联动：班级不存在/已删除
        logger.warning("新增学生被拒 | %s", error)
        return StudentResponse(code=404, message=str(error), data=None)
    if res:
        logger.info("新增学生成功 | id=%s name=%s class_id=%s", res.id, res.name, res.class_id)  # [日志·增]
        return StudentResponse(code=201, message="添加成功", data=res)
    logger.error("新增学生失败 | name=%s", student.name)
    return StudentResponse(code=500, message="添加失败", data=None)

#获得特定学生信息
@stu_router.get("/student/{student_id}", response_model=StudentResponse,description='获得特定学生信息')
async def get_one_student(stu_id: int, db=Depends(get_db)):
    # 调用dao，根据id查询单条
    student = dao_get_student_by_id(db, stu_id)
    if student:
        return StudentResponse(code=200, message="查询成功", data=student)
    logger.warning("查询学生未命中 | id=%s", stu_id)
    return StudentResponse(code=404, message="找不到该学生", data=None)
#更新学生信息
@stu_router.put("/student/{student_id}", response_model=StudentResponse,description='更新学生信息')
async def update_student(stu_id: int,
                         body:StudentUpdateRequest,
                         db=Depends(get_db)):
    try:
        student=dao_update_student(db,stu_id,body)
    except ValueError as error:  # 学生-班级联动：改班时目标班级不存在/已删除
        logger.warning("更新学生被拒 | id=%s | %s", stu_id, error)
        return StudentResponse(code=404, message=str(error), data=None)
    if not student:
        logger.warning("更新学生未命中 | id=%s", stu_id)
        return StudentResponse(code=404,message='没有匹配到对应学生',data=None)
    logger.info("更新学生成功 | id=%s", stu_id)
    return StudentResponse(code=200,message='更新成功',data=student)#StudentDetail.model_validate(student)

# 逻辑删除学⽣
@stu_router.delete("/student/{student_id}", response_model=StudentResponse)
async def delete_student(stu_id: int,db=Depends(get_db)):
    # 删除学生信息
    student = dao_delete_student(db,stu_id)
    if not student:
        logger.warning("删除学生未命中 | id=%s", stu_id)
        return StudentResponse(code=404,message='未找到对应学生，无法删除',data=None)
    logger.info("删除学生成功 | id=%s name=%s class_id=%s", student.id, student.name, student.class_id)  # [日志·增] 逻辑删除记下离班班级
    return StudentResponse(code=204,message='删除成功',data=student)






# @stu_router.post('/students/batch',response_model=StudentResponse)
# async def batch_get_students(student:StudentRequest,db=Depends(get_db)):
#     stu=dao_batch_get_students(db,student) #得到ORM 对象列表
#     #将ORM 对象转换为StudentRequest的实例（pydantic对象）
#     stu_list=[ StudentRequest.model_validate(i) for i in stu]  #
#     if not stu_list:
#         logger.error("查询失败: %s", 'err111111')
#         return {"code": 404,
#                 "message": "没有匹配到对应学生",
#                 "data": None
#                 }
#     return {"code":200,
#             "message":"返回成功",
#             "data":stu_list}
# # 更新学⽣信息
# @stu_router.put("/student/update/batch", response_model=StudentResponse)
# async def batch_update_student(
#         #StudentUpdateRequest包含了查询条件以及修改内容，由StudentUpdateRequest进行校验
#         body: StudentUpdateRequest,
#         db=Depends(get_db)
#     ):
#     # 把要更新的字段转字典，自动剔除None，不会覆盖数据库里没传的字段
#     update_dict = body.values.model_dump(exclude_none=True)
#     #修改学生信息
#     stu = batch_dao_update_student(db, body.filters, update_dict)
#     if not stu:
#         return {"code": 404,
#                 "message": "没有匹配到对应学生",
#                 "data": None
#                 }
#     return {
#         "code": 200,
#         "message": "更新成功",
#         "data": StudentDetail.model_validate(stu)
#     }
#
# # 逻辑删除学⽣
# @stu_router.delete("/student/delete_batch", response_model=StudentResponse)
# async def batch_delete_student(
#         # StudentDeleteRequest包含了查询条件以及修改内容，由StudentDeleteRequest进行校验
#         body: StudentDeleteRequest,
#         db=Depends(get_db)
# ):
#     # 删除学生信息
#     stu = batch_dao_delete_student(db,body.filters)
#     if not stu:
#         return {"code": 404,
#                 "message": "没有匹配到对应学生",
#                 "data": None
#                 }
#     data = [StudentDetail.model_validate(item) for item in stu]
#     return {
#         "code": 200,
#         "message": "删除成功",
#         "data": data
#     }
# #创建新学生
# @stu_router.post("/student/add/batch", response_model=StudentResponse)
# async def add_student(student:StudentCreate,db=Depends(get_db)):
#     res=batch_dao_add_student(db,student)
#     if res:
#         return {
#             "code": 200,
#             "message": "添加成功",
#             "data": student
#         }
#     return {"code": 500,
#                 "message": "添加失败",
#                 "data": None
#                 }


