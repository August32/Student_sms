from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError#从Exceptions异常模块导入完整性错误(能报业务错误)
from sqlalchemy.orm import Session#从数据库里导入会话,能增删改查

from app.models.teacher import Teacher, teacher_class
from app.models.class_info import ClassInfo  # [整合·增] 老师-班级联动：校验班级真实存在
from app.schemas.teacher import TeacherCreate, TeacherQuery, TeacherUpdate


# ---------- 内部小工具 ----------

# [整合·增] 老师-班级联动：head_class_id / class_ids 都指向班级表，但原先不做校验。
# MySQL 上外键不存在时插入报 IntegrityError，被下面 except 当成"该班级已有班主任"，
# 错误提示完全指错方向；这里先校验班级存在，把"班级不存在"和"班主任冲突"分开报
def _check_classes_exist(db: Session, class_ids: list[int], head_class_id: int | None = None):
#检验班级存在,去班级表里查数据(能增删改查)
    need = set(class_ids)#集合去重
    if head_class_id is not None:#如果不为空,把加入的数字加入到班主任带班号里
        need.add(head_class_id)
    if not need:#如果没传直接放行
        return
    found = {#去班级表查所有在名单上而且没被删除的班级
        row.id#row是变量,这是一个集合推导式
        for row in db.query(ClassInfo.id)
        .filter(ClassInfo.id.in_(need), ClassInfo.is_deleted == 0)
        #班级的 ID 必须在前端给的名单（need）里且是没被删除的
        .all()
    }
    missing = sorted(need - found)#前端要的班级清单-真实存在的班级 集合-集合(再转换成有顺序的列表)
    if missing:
        raise ValueError(f'班级不存在或已删除: {missing}，请先在班级管理里创建班级')


def _replace_teacher_classes(db: Session, teacher_id: int, class_ids: list[int]):
    """整体替换某位老师的授课班级：先清掉旧关系，再批量写入新关系"""
    db.execute(#删除被选定id的老师的带班数据
        teacher_class.delete().where(teacher_class.c.teacher_id == teacher_id)
    )
    if class_ids:
        db.execute(#批量插入授课班级数据
            teacher_class.insert(),
            [{'teacher_id': teacher_id, 'class_id': class_id} for class_id in class_ids],
        )


def _attach_class_ids(db: Session, teachers: list[Teacher]):
    """给老师对象挂上授课班级 class_ids。
    一次把这批老师的授课关系全查出来再拼回去，避免一个老师查一次库"""#避免循环查库
    if not teachers:#如果老师是空的,直接原路返回
        return
    rows = (#批量把名单上的老师id的班级记录都拉出来
        db.query(teacher_class.c.teacher_id, teacher_class.c.class_id)
        .filter(teacher_class.c.teacher_id.in_([t.id for t in teachers]))
        .all()
    )
    class_map: dict[int, list[int]] = {}  # {老师id: [班级id, ...]}
    for teacher_id, class_id in rows:
        class_map.setdefault(teacher_id, []).append(class_id)
    for teacher in teachers:
        teacher.class_ids = class_map.get(teacher.id, [])#把班级信息贴到查出来的老师id上


# ---------- 增删改查 ----------

def dao_get_teachers(db: Session, params: TeacherQuery) -> list[Teacher]:
    """按条件查询老师列表（默认只查在职的），每个老师带上授课班级"""
    query = db.query(Teacher)#准备调用

    if not params.include_deleted:#如果没选包含删除的,就只看在职的
        query = query.filter(Teacher.is_deleted == 0)

    if params.id is not None:#查id
        query = query.filter(Teacher.id == params.id)

    if params.name is not None:  # 模糊查询：名字里有这个字就命中
        query = query.filter(Teacher.name.like(f'%{params.name}%'))

    if params.class_id is not None:#根据班级id找老师
        # 这个班的老师 = 班主任（head_class_id） 或 在中间表里教这个班的
        teach_ids = select(teacher_class.c.teacher_id).where(#哪些老师教了这个班
            teacher_class.c.class_id == params.class_id#中间表的班级列
        )
        query = query.filter(#查询出要么是班主任要么是授课老师
            or_(Teacher.head_class_id == params.class_id, Teacher.id.in_(teach_ids))
        )

    if params.role == 'head':  # 班主任：带了班的都算（含既当班主任又授课的）
        query = query.filter(Teacher.head_class_id.isnot(None))
    elif params.role == 'subject':  # 授课老师：中间表里有授课记录的
        query = query.filter(Teacher.id.in_(select(teacher_class.c.teacher_id)))

    teachers = query.all()#所有符合条件的老师
    _attach_class_ids(db, teachers)#老师教的班级拉回来贴在老师身上
    return teachers


def dao_get_teacher(db: Session, teacher_id: int) -> Teacher | None:#db: Session(数据库会话,能增删改查)
    """查询单个在职老师，并带上授课班级"""
    teacher = (
        db.query(Teacher)
        .filter(Teacher.id == teacher_id, Teacher.is_deleted == 0)#在职的老师
        .first()
    )
    if teacher is not None:#找到人了,把班级贴上去
        _attach_class_ids(db, [teacher])#批量老师列表里查,不用再返回数据库一个个查
    return teacher


def dao_create_teacher(db: Session, data: TeacherCreate) -> Teacher:#返回类型注解,返回一个老师对象
    """新增老师，并写入授课班级关系"""
    _check_classes_exist(db, data.class_ids, data.head_class_id)  # [整合·增] 先确认班级存在，再动老师表
    payload = data.model_dump(exclude={'class_ids'})
    #把前端传来的TeacherCreate数据排除班级关系后处理成字典
    #为什么要单独处理:班级关系在中间表，单独处理主表没有班级表中间表有,且按照业务顺序应该先给老师建档才排班级
    teacher = Teacher(**payload)#把字典解包后作为参数传入主表
    try:
        db.add(teacher)
        db.flush()  # 先拿到自增 id，此时事务还没提交(调用函数但是操作在事务中别人查不到)
        _replace_teacher_classes(db, teacher.id, data.class_ids)
        db.commit()
        db.refresh(teacher)  # 刷新出创建时间等数据库生成的字段
    except IntegrityError:
        # head_class_id 有唯一约束：同一个班指定了两个班主任会走到这
        db.rollback()
        raise ValueError('该班级已有班主任，请检查 head_class_id')
    except Exception:
        db.rollback()  # 其它错误回滚，不留脏数据(兜底)
        raise
    teacher.class_ids = list(data.class_ids)  # 回给接口刚提交的班级名单,把班级名单贴老师身上
    return teacher


def dao_update_teacher(db: Session, teacher_id: int, data: TeacherUpdate) -> Teacher | None:
    """修改老师信息：传了 class_ids 就整体替换授课班级"""
    teacher = (
        db.query(Teacher)
        .filter(Teacher.id == teacher_id, Teacher.is_deleted == 0)
        .first()
    )
    if teacher is None:  # 查无此人（或已删除）
        return None

    update_data = data.model_dump(exclude_unset=True)  # 更新的数据,只改需要改的地方,其他内容会在真实前端保留
    class_ids = update_data.pop('class_ids', None)  # 班级关系在中间表，从补丁里拆出来

    # [整合·增] 传了授课班级或班主任带班就校验班级存在（没传的字段不动、不校验）
    _check_classes_exist(db, class_ids if class_ids is not None else [], update_data.get('head_class_id'))
#如果前端传了授课班级(id)就用他填写的,如果没填就给个空列表,如果前端改了班主任的班级,就给出具体的班级号,如果没给就跳过
    for key, value in update_data.items():#遍历字典
        setattr(teacher, key, value)  # 逐个字段覆盖
    if class_ids is not None:#前面的函数,整体替换老师的授课班级
        _replace_teacher_classes(db, teacher.id, class_ids)

    try:
        db.commit()
        db.refresh(teacher)
    except IntegrityError:
        db.rollback()
        raise ValueError('该班级已有班主任，请检查 head_class_id')
    except Exception:#兜底报错,扔给api
        db.rollback()
        raise

    _attach_class_ids(db, [teacher])  # 返回最新的授课班级
    return teacher


def dao_delete_teacher(db: Session, teacher_id: int) -> Teacher | None:
    """逻辑删除老师：只标记 is_deleted，数据还在表里（可恢复）"""
    teacher = (#找目前在职的老师id
        db.query(Teacher)
        .filter(Teacher.id == teacher_id, Teacher.is_deleted == 0)
        .first()
    )
    if teacher is None:
        return None
    teacher.head_class_id = None
    teacher_class.
    teacher.is_deleted = 1
    teacher.deleted_at = datetime.now()
    db.commit()
    return teacher
