from fastapi import APIRouter, Depends, HTTPException
##从fastapi里导入接口路由器(全写在main里文件会爆炸),依赖注入,HTTP异常
from sqlalchemy.orm import Session#导入会话,方便增删改查

from app.core.database import get_db  # 打开会话传给接口，请求结束后自动关闭

from app.dao.dao_teacher import (
    dao_create_teacher,
    dao_delete_teacher,
    dao_get_teacher,
    dao_get_teachers,
    dao_update_teacher,
)
from app.schemas.teacher import (
    TeacherCreate,
    TeacherDetail,
    TeacherQuery,
    TeacherResponse,
    TeacherUpdate,
)
from app.utils.logger import get_logger#从api导入怎么保存文件怎么记录时间的功能,不用在每个文件里手写

logger = get_logger(__name__)#内置魔法变量,知道报错找这个模块
teacher_router = APIRouter()  # 所有老师接口都挂在这个路由里


def _to_detail(teacher) -> TeacherDetail:
    """把数据库 ORM 对象转成响应模板（最终序列化成 json 给前端）"""#定义输出标准
    return TeacherDetail.model_validate(teacher)
#把数据从数据库的orm对象(包含密码等内部状态)转换成pydantic模型(发生在api调用dao拿到数据后,准备返回之前,发生在schemas层
# ,防泄密防数据库崩溃),再转Jason格式(api给前端,前端只认识jason字符串)


# [改] 原 POST /teacher/query 不符合需求文档"接口要遵从 Restful 规范"，
#      查询改成 GET /teacher + 查询参数（和班级模块 GET /class_info 保持一致）
@teacher_router.post('/teacher', response_model=TeacherResponse, status_code=201)#201成功并且创建文件
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    """新增老师（可同时指定班主任带班 head_class_id 和授课班级 class_ids）"""
    try:
        teacher = dao_create_teacher(db, data)
    except ValueError as error:  # 业务校验失败（如重复班主任）
        logger.warning('新增老师被拒 | %s', error)  # [日志·增] 联动校验被拦（班级不存在/已有班主任）
        raise HTTPException(status_code=422, detail=str(error))#格式对但是内容或逻辑错误拒绝处理
    logger.info('新增老师成功 | id=%s name=%s', teacher.id, teacher.name)
    return {'code': 201, 'message': '创建成功', 'data': _to_detail(teacher)}


@teacher_router.get('/teacher', response_model=TeacherResponse)#访问这个网址,依赖注入按照这个格式
def query_teachers(params: TeacherQuery = Depends(), db: Session = Depends(get_db)):#用完自动关闭
    """按条件查询老师列表，例如 /teacher?name=王&class_id=1&role=head"""
    teachers = dao_get_teachers(db, params)
    logger.info('查询老师列表 | name=%s class_id=%s role=%s | 返回 %d 条',#占位符,参数会依次填入进去
                params.name, params.class_id, params.role, len(teachers))  # [日志·增] 列表查询记条数
    return {
        'code': 200,
        'message': '查询成功',
        'data': [_to_detail(teacher) for teacher in teachers],
    }


@teacher_router.get('/teacher/{teacher_id}', response_model=TeacherResponse)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """查询单个老师详情（含授课班级 class_ids）"""
    teacher = dao_get_teacher(db, teacher_id)
    if teacher is None:
        logger.warning('查询老师未命中 | id=%s', teacher_id)  # [日志·增] 单条查询只记未命中
        raise HTTPException(status_code=404, detail='老师不存在')#资源不存在
    return {'code': 200, 'message': '查询成功', 'data': _to_detail(teacher)}


@teacher_router.put('/teacher/{teacher_id}', response_model=TeacherResponse)
def update_teacher(teacher_id: int, data: TeacherUpdate, db: Session = Depends(get_db)):
    """修改老师信息（传 class_ids 则整体替换授课班级）"""
    try:
        teacher = dao_update_teacher(db, teacher_id, data)
    except ValueError as error:
        logger.warning('更新老师被拒 | id=%s | %s', teacher_id, error)  # [日志·增]
        raise HTTPException(status_code=422, detail=str(error))
    if teacher is None:
        logger.warning('更新老师未命中 | id=%s', teacher_id)  # [日志·增]
        raise HTTPException(status_code=404, detail='老师不存在')
    logger.info('修改老师成功 | id=%s', teacher_id)
    return {'code': 200, 'message': '修改成功', 'data': _to_detail(teacher)}


@teacher_router.delete('/teacher/{teacher_id}', response_model=TeacherResponse)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """逻辑删除老师（只标记 is_deleted，数据不物理删除）"""
    teacher = dao_delete_teacher(db, teacher_id)
    if teacher is None:
        logger.warning('删除老师未命中 | id=%s', teacher_id)  # [日志·增]
        raise HTTPException(status_code=404, detail='老师不存在')
    logger.info('删除老师成功 | id=%s', teacher_id)#后台记录
    return {'code': 200, 'message': '删除成功', 'data': None}
