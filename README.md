# wolin_sms 合并工程整合改动清单

- **审查日期**：2026-11-09
- **工程位置**：`C:\Users\Windows\Desktop\test\wolin_sms_lasted`
- **审查范围**：学生 / 班级 / 教师 / 成绩 / 就业 / 统计 六个模块之间的联调整合
- **标注约定**：代码内所有改动行均带 `[整合·增]`（新增）、`[整合·改]`（修改）、`[整合·恢复]`（恢复被注释的需求功能）标记，在 IDE 里全局搜索 **「整合」** 即可逐处定位

**改动统计**：共 14 个文件，修复模块断链 3 处、需求缺口 2 处、联动校验缺失 3 处、统计口径 1 处。

---

## 一、改动总览

| #  | 文件                          | 标记   | 改动内容                                              | 影响                 |
| -- | --------------------------- | ---- | ------------------------------------------------- | ------------------ |
| 1  | `app/main.py`               | 增+改  | 挂载成绩模块路由；修正教师模块标签                                 | 成绩 4 个端点从 404 → 可用 |
| 2  | `app/schemas/student.py`    | 增    | 补 `class_id` / `enroll_time` / `graduate_time` 字段 | 学生-班级-统计-就业整条链打通   |
| 3  | `app/models/student.py`     | 改    | 恢复 `class_id` 外键到 `classes.id`                    | 学生表与班级表建立关联        |
| 4  | `app/dao/dao_student.py`    | 增+改  | 查询筛选、班级校验、班级人数同步、软删除补时间戳                          | 学生-班级双向联动          |
| 5  | `app/api/student.py`        | 增+改  | 列表接口加筛选参数、捕获班级校验异常                                | 对应需求 2.1 条件查询      |
| 6  | `app/dao/dao_score.py`      | 增    | 录入成绩前校验学生存在                                       | 成绩-学生联动，防外键 500    |
| 7  | `app/api/score.py`          | 增    | 捕获学生不存在 → 业务 404                                  | 同上                 |
| 8  | `app/dao/dao_teacher.py`    | 增    | 创建/老师时校验班级存在                                      | 老师-班级联动，纠错误导性报错    |
| 9  | `smoke_test_teacher.py`     | 改    | 补造班级 101/102/103 测试数据                             | 测试数据与联动校验匹配        |
| 10 | `app/schemas/employment.py` | 恢复   | 恢复 `EmploymentQuery` 查询条件模型                       | 对应需求 2.3 条件查询      |
| 11 | `app/dao/dao_employment.py` | 恢复+改 | 恢复条件查询 DAO，公司名改模糊匹配                               | 同上                 |
| 12 | `app/api/employment.py`     | 恢复   | 恢复 `GET /employment` 条件查询接口                       | 同上                 |
| 13 | `app/dao/dao_statistics.py` | 改    | over-30 改 outerjoin，班级名可为空                        | 不漏掉无班级学生           |
| 14 | `app/schemas/statistics.py` | 改    | `class_name` 改为可空                                 | 配合上一条              |



---

## 二、逐处改动明细（改动前 → 改动后）

### 1. `app/main.py` — 成绩路由漏挂（致命，整模块不可用）

**问题**：成绩模块 API/DAO/Schema 都写完了，但 `main.py` 没有导入和挂载 `score_router`，需求 4.2 的 4 个成绩端点全部 404。组员单模块测试没走完整应用入口，所以各自都"跑通了"。

```python
# 改动前
from app.api.teacher import teacher_router
...
app.include_router(teacher_router,tags=["就业信息管理"])   # 教师被误归到就业标签

# 改动后
from app.api.teacher import teacher_router
from app.api.score import score_router  # [整合·增] 成绩模块路由原先没在这里挂载，需求 4.2 的 4 个成绩端点整体 404，补上
...
app.include_router(teacher_router,tags=["老师管理"])  # [整合·改] 原来误写成"就业信息管理"，老师是需求 2.5 独立模块
app.include_router(score_router, tags=["成绩管理"])  # [整合·增] 挂载成绩模块（成绩录入/查询/修改/删除）
```

### 2. `app/schemas/student.py` — 学生缺班级/时间字段（跨模块断链核心）

**问题**：需求 2.1 的学生字段清单包含"学生班级、入学时间、毕业时间"，但出入参模型里完全没有这三个字段。创建学生带不上班级 → 统计模块（按班级）、就业模块（按班级查）联表全查不到人，三个下游模块一起失效。

```python
# 改动前
class StudentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str | None = Field(None, min_length=1)
    native_place: str | None = Field(None, min_length=1)
    ...

# 改动后
from datetime import date  # [整合·增] 入学/毕业时间是日期类型
class StudentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str | None = Field(None, min_length=1)
    # [整合·增] 需求 2.1 学生字段清单里的"学生班级、入学时间、毕业时间"原先整个出入参模型都没有：
    # 创建学生带不上班级 → 学生和班级关联断裂 → 统计(按班级)、就业(按班级查)全查不到人
    class_id: int | None = Field(None, gt=0, description="学生班级id，关联 classes.id")
    enroll_time: date | None = Field(None, description="入学时间")
    graduate_time: date | None = Field(None, description="毕业时间")
    native_place: str | None = Field(None, min_length=1)
    ...
```

另外顺手清理：删除了文件头部重复导入的两行、未使用的 `from app.schemas.class_info import ClassInfoDetail`。

### 3. `app/models/student.py` — 班级外键恢复

**问题**：`class_id` 的 ForeignKey 被注释掉，且注释里写的表名 `'class'` 是错的（班级表实际叫 `classes`），学生表和班级表在数据库层没有关联。

```python
# 改动前
class_id = Column(Integer) #学⽣班级,ForeignKey('class.id'),nullable=False

# 改动后
# [整合·改] 恢复外键：原先 ForeignKey 被注释掉且表名写成 'class'（班级表实际叫 classes），
# 现在 class_info.py 已实现，补回关联。注意：create_all 不改已建好的表，对现有库无影响，重建库时才生效
class_id = Column(Integer, ForeignKey('classes.id')) #学⽣班级，关联班级表
```

### 4. `app/dao/dao_student.py` — 查询筛选 + 三处班级联动

**问题 ①**：需求 2.1 明确"查询学生信息（支持按编号、姓名、班级等条件筛选）"，原来只能一次拉全表。  
**问题 ②**：`class_id` 悬空不校验，统计/就业按班级查人静默丢失。  
**问题 ③**：`classes.student_count` 是冗余字段（模型注释写明"学生增删时需同步维护"），但学生模块增删改从不维护它。  
**问题 ④**：软删除不填 `deleted_at`，和班级/老师/成绩/就业四个模块口径不一致；错误输出用 `print` 而非项目日志。

```python
# 新增两个内部工具（联动核心）
# [整合·增] 学生-班级联动（1/2）：带班级id时校验班级真实存在且删除
def _check_class_exists(db, class_id):
    if class_id is None:
        return
    exists = (db.query(ClassInfo)
              .filter(ClassInfo.id == class_id, ClassInfo.is_deleted == 0)
              .first())
    if not exists:
        raise ValueError(f"班级不存在或已删除: {class_id}")

# [整合·增] 学生-班级联动（2/2）：每次学生变动后按实际人数重算班级人数
def _refresh_class_student_count(db, class_id):
    if class_id is None:
        return
    real_count = (db.query(Student)
                  .filter(Student.class_id == class_id, Student.is_deleted == 0)
                  .count())
    class_info = db.query(ClassInfo).filter(ClassInfo.id == class_id).first()
    if class_info is not None:
        class_info.student_count = real_count
```

```python
# 查询：改动前
def dao_get_student_list(db):
    stu_list=db.query(Student).filter(Student.is_deleted==0).all()
    return stu_list

# 查询：改动后
# [整合·改] 需求 2.1 明确要求"支持按编号、姓名、班级等条件筛选"
def dao_get_student_list(db, stu_id=None, name=None, class_id=None):
    query = db.query(Student).filter(Student.is_deleted == 0)
    if stu_id is not None:
        query = query.filter(Student.id == stu_id)  # 按编号精确筛
    if name:
        query = query.filter(Student.name.like(f'%{name}%'))  # 按姓名模糊筛，和老师模块口径一致
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)  # 按班级筛
    stu_list = query.all()
    return stu_list
```

```python
# 新增学生：改动后（含两处联动）
def dao_add_student(db,student):
    data = student.model_dump(exclude_none=True)
    _check_class_exists(db, data.get("class_id"))  # [整合·增] 校验放 try 外面，ValueError 冒给接口层
    try:
        student = Student(**data)
        db.add(student)
        db.commit()
        db.refresh(student)
        _refresh_class_student_count(db, student.class_id)  # [整合·增] 新学生进班，班级人数重算
        db.commit()
        return student
    except Exception as e:
        db.rollback()
        logger.error("新增学生失败: %s", e)  # [整合·改] 原 print(e)
        return None
```

```python
# 更新学生：改动后（换班时原班级+新班级人数都要重算）
    update_dict = student.values.model_dump(exclude_none=True, exclude=["id"])
    _check_class_exists(db, update_dict.get("class_id"))  # [整合·增] 改班也要校验目标班级存在
    old_class_id = stu.class_id  # [整合·增] 记下原班级
    for k, v in update_dict.items():
        setattr(stu, k, v)
    _refresh_class_student_count(db, old_class_id)  # [整合·增]
    _refresh_class_student_count(db, stu.class_id)  # [整合·增]
    db.commit()
```

```python
# 删除学生：改动后
        student.is_deleted = 1
        student.deleted_at = datetime.now()  # [整合·增] 原来只标记不记删除时间，和其他四个模块软删除口径不一致
        _refresh_class_student_count(db, student.class_id)  # [整合·增] 学生离班，班级人数重算
        db.commit()
```

### 5. `app/api/student.py` — 列表筛选参数 + 异常转业务提示

```python
# 改动前
@stu_router.get('/student',description='学生列表')
async def get_student_list(db=Depends(get_db)):
    stu_list=dao_get_student_list(db)
    return StudentResponse(code=200,message='返回成功',data=stu_list)

# 改动后
@stu_router.get('/student',response_model=StudentResponse,description='学生列表，支持按编号/姓名/班级筛选')
async def get_student_list(stu_id: int | None = None,
                           name: str | None = None,
                           class_id: int | None = None,
                           db=Depends(get_db)):
    # [整合·改] 需求 2.1：按编号、姓名、班级等条件筛选，原来只能一次拉全表
    stu_list=dao_get_student_list(db, stu_id=stu_id, name=name, class_id=class_id)
    return StudentResponse(code=200,message='返回成功',data=stu_list)
```

`add_student` / `update_student` 两处增加（写法相同）：

```python
    try:
        res = dao_add_student(db, student)
    except ValueError as error:  # [整合·增] 学生-班级联动：班级不存在/已删除
        return StudentResponse(code=404, message=str(error), data=None)
```

### 6. `app/dao/dao_score.py` — 录成绩前校验学生存在

**问题**：`student_id` 是外键，给不存在的学生录成绩，MySQL 上直接 IntegrityError 变 500，没有任何提示。

```python
from app.models.student import Student  # [整合·增] 成绩-学生联动：录入前确认学生存在

# dao_create_score 开头增加：
    # [整合·增] 成绩-学生联动：只给存在且未删除的学生录入成绩。
    # student_id 是外键，学生不存在时插入直接报 IntegrityError 变成 500，这里先拦下来转成明确提示
    student = (db.query(Student)
               .filter(Student.id == score_data.student_id, Student.is_deleted == 0)
               .first())
    if student is None:
        raise ValueError("学生不存在或已删除，无法录入成绩")
```

### 7. `app/api/score.py` — 异常转业务 404

```python
    # [整合·增] 成绩-学生联动：学生不存在/已删除时 DAO 抛 ValueError，转成业务 404
    try:
        new_score = dao_create_score(db, body)
    except ValueError as error:
        return {
            "code": 404,
            "message": str(error),
            "data": None,
        }
```

### 8. `app/dao/dao_teacher.py` — 老师带班班级校验

**问题**：`head_class_id` / `class_ids` 都指向班级表但从不校验班级是否存在。MySQL 上外键不存在时抛 `IntegrityError`，被下面的 `except` 当成"该班级已有班主任"，错误提示完全指错方向。

```python
from app.models.class_info import ClassInfo  # [整合·增] 老师-班级联动：校验班级真实存在

# [整合·增] 新增校验工具
def _check_classes_exist(db: Session, class_ids: list[int], head_class_id: int | None = None):
    need = set(class_ids)
    if head_class_id is not None:
        need.add(head_class_id)
    if not need:
        return
    found = {
        row.id
        for row in db.query(ClassInfo.id)
        .filter(ClassInfo.id.in_(need), ClassInfo.is_deleted == 0)
        .all()
    }
    missing = sorted(need - found)
    if missing:
        raise ValueError(f'班级不存在或已删除: {missing}，请先在班级管理里创建班级')
```

`dao_create_teacher` / `dao_update_teacher` 各调用一处：

```python
    _check_classes_exist(db, data.class_ids, data.head_class_id)          # 创建时
    _check_classes_exist(db, class_ids if class_ids is not None else [],  # 更新时（没传的字段不校验）
                         update_data.get('head_class_id'))
```

### 9. `smoke_test_teacher.py` — 测试造数补齐

**问题**：测试直接用班级 101/102/103 建老师，但从不建班级记录。SQLite 默认不强制外键所以侥幸通过，换 MySQL 会直接报外键错；加了联动校验后必须先造班级。

```python
# [整合·改] 老师-班级联动校验后，授课/带班班级必须真实存在。
_db = TestingSession()
for _cid, _name in [(101, '整合测试一班'), (102, '整合测试二班'), (103, '整合测试三班')]:
    _db.add(ClassInfo(id=_cid, class_name=_name,
                      class_time=datetime.datetime(2025, 9, 1),
                      class_teacher='测试班主任'))
_db.commit()
_db.close()
```

### 10~12. 就业模块 — 恢复需求 2.3 条件查询（三处配套）

**问题**：需求 2.3 明确"按照学生编号，公司名字，工资范围查询学生就业信息"，但 schemas / dao / api 三处实现全被整段注释，等于功能缺失。

`app/schemas/employment.py` — 恢复查询条件模型：

```python
# [整合·恢复] 需求 2.3 明确要求"按照学生编号，公司名字，工资范围查询学生就业信息"，
# 原实现（含 DAO 和路由）被整段注释掉了，等于功能缺失，这里恢复
class EmploymentQuery(BaseModel):
    student_id: int | None = Field(default=None, gt=0, description='学生编号')
    company_name: str | None = Field(default=None, min_length=1, max_length=100, description='就业公司名称（模糊匹配）')
    min_salary: Decimal | None = Field(default=None, ge=0, description='最低工资')
    max_salary: Decimal | None = Field(default=None, ge=0, description='最高工资')
    employment_open_date_start: date | None = ...
    employment_open_date_end: date | None = ...
    offer_date_start: date | None = ...
    offer_date_end: date | None = ...
```


`app/dao/dao_employment.py` — 恢复 `query_employments_dao`，其中一处口径改动：

```python
    if params.company_name is not None:
        # [整合·改] 精确匹配改成模糊匹配：按公司名查通常记不全全称，和老师模块按姓名查的口径一致
        query = query.filter(Employment.company_name.like(f'%{params.company_name}%'))
```

`app/api/employment.py` — 恢复路由（与需求 4.3 的三个既有端点并存）：

```python
# [整合·恢复] 需求 2.3：按照学生编号、公司名字、工资范围查询学生就业信息
@emp_router.get("/employment", response_model=EmploymentResponse)
async def get_employments_api(params: EmploymentQuery = Depends(), db: Session = Depends(get_db)):
    employment_list = query_employments_dao(db=db, params=params)
    return {"code": 200, "message": "返回成功", "data": employment_list}
```

### 13~14. 统计模块 — over-30 口径修正

**问题**：需求 2.6.1 原文是"查询**所有**超过 30 岁的学员的信息"，原实现 inner join 班级表，没分配班级 / 班级被软删的学生会被整条漏掉。

`app/dao/dao_statistics.py`：

```python
# 改动前
    rows = (db.query(Student, ClassInfo)
            .join(ClassInfo, Student.class_id == ClassInfo.id)
            .filter(Student.is_deleted == 0,
                    ClassInfo.is_deleted == 0,
                    Student.age > 30)
            .all())

# 改动后
    # [整合·改] 需求写的是"查询所有超过30岁的学员"，原来 inner join classes 会把
    # 没分配班级 / 班级被软删的学生整条漏掉。改 outerjoin：没班级照样返回，班级名为空
    rows = (db.query(Student, ClassInfo)
            .outerjoin(ClassInfo, Student.class_id == ClassInfo.id)
            .filter(Student.is_deleted == 0,
                    Student.age > 30)
            .all())
```

返回组装处同步防 None：

```python
            # [整合·改] outerjoin 后没班级的学生 class_info 为 None，班级名返回 None 而不是报错
            "class_name": class_info.class_name if class_info is not None else None,
```

`app/schemas/statistics.py`：

```python
# 改动前
class_name: str                                  # 学生班级

# 改动后
class_name: str | None = None                    # 学生班级（[整合·改] 可空：没分配班级的学生也要出现在"所有超过30岁"里，班级名为空）
```

---

## 三、回归验证结果

### 3.1 模块冒烟测试（改动前 → 改动后）

| 测试文件                       | 改动前基线                            | 改动后                  |
| -------------------------- | -------------------------------- | -------------------- |
| `smoke_test_score.py`      | 29 个用例 **挂 12 个**（全部 API 用例 404） | **29/29 通过**         |
| `smoke_test_teacher.py`    | 25/25（外键假数据侥幸通过）                 | **25/25 通过**（真实班级数据） |
| `smoke_test_class_info.py` | 11/11                            | **11/11 通过**         |
| `smoke_test_statistics.py` | 全部断言通过                           | **全部断言通过**           |

### 3.2 跨模块端到端串联验证（本次新增 22 项，全部通过）

覆盖链路：建班 → 带班级建学生（班级人数自动同步）→ 按编号/姓名/班级筛选学生 → 假班级被拦 → 录成绩（含不存在学生被拦）→ 老师带真/假班级 → 就业录入 + 按公司名/工资范围查询 → 统计（over-30 含无班级学生、班级人数/薪资前五/平均就业时长联表）→ 删学生后班级人数回落。

启动日志确认 31 个接口全部注册：

```
学生 5 个 + 班级 5 个 + 统计 8 个 + 就业 5 个 + 老师 5 个 + 成绩 4 个 = 31 个
```

---

## 四、遗留事项（本次刻意没动，答辩前需知）

1. **`test_employment_api.py` 未跑**：该脚本需要连团队 MySQL（192.168.150.60）并启动服务，本次环境不可达。到能连库的机器上请跑一遍确认。
2. **Student 模型缺 `created_at` / `updated_at`**（其余四个模型都有这两个时间戳字段）：补字段需要 ALTER TABLE，对已建好的库有风险，故未动。答辩被问到可说明"学生表建得早，字段规划不一致，已记录待迁移"。
3. **路径风格与需求示例有出入**：需求 4.1 示例是 `GET /students`，当前是 `/student`；班级 `/class_info`、老师 `/teacher` 也是自定义。因各模块冒烟测试均绑定现路径，改动会引发连锁破坏，保持现状。可引用需求 4.5"其它模块端点自定义"答辩。
4. **演示顺序提醒**：学生带 `class_id` 创建时会校验班级存在，演示/造数据请**先建班级，再建学生**，否则返回业务 404"班级不存在"。
5. **建议补 `requirements.txt`**（当前缺失）：`fastapi`、`uvicorn`、`sqlalchemy`、`pymysql`、`pydantic`，答辩环境部署会用到。

---

## 五、日志补充（2026-11-09 第二轮，标记 `[日志·增]`）

按统一口径给各模块补关键节点日志（statistics / main 原本就有，未动）：

| 节点类型 | 级别 | 示例 |
|---|---|---|
| 写操作成功（增/改/删） | INFO | `新增学生成功 \| id=1 name=日志甲 class_id=1` |
| 列表/条件查询 | INFO（记筛选条件+条数） | `查询学生列表 \| stu_id=None name=日志 \| 返回 1 条` |
| 单条查询未命中 | WARNING | `查询学生未命中 \| id=999` |
| 业务失败（404/409/400） | WARNING | `录入成绩被拒 \| 重复录入 student_id=1 exam_sequence=1` |
| 联动校验被拦 | WARNING | `新增学生被拒 \| 班级不存在或已删除: 999` |
| 落库异常 | ERROR（logger.exception 记堆栈） | DAO except 块内，记完再上抛 |

**改动文件**：`api/student.py`、`api/class_info.py`（补 logger 导入）、`api/teacher.py`、`api/score.py`、`api/employment.py`（补 logger 导入）、`dao/dao_class_info.py`（3 处 except）、`dao/dao_employment.py`（2 处 except）。

**日志落盘**：`logs/app.log`（5MB 轮转保留 3 份）+ 控制台双通道。回归：4 套冒烟测试全绿，业务链路触发验证通过。

---

## 六、异常处理优化（2026-11-09 第三轮，标记 `[异常·增]` / `[异常·改]`）

| 优先级 | 问题 | 改法 | 文件 |
|---|---|---|---|
| P0 | 未捕获异常返回裸 `Internal Server Error`，不是统一响应体，堆栈不进 app.log | `@app.exception_handler(Exception)` 全局兜底：统一返回 `{"code":500,"message":"服务器内部错误，请查看 logs/app.log","data":None}` 并 `logger.exception` 记堆栈 | `app/main.py` |
| P1 | 重复建同名班级 / 改名撞名 → IntegrityError 裸 500（演示最容易撞到） | DAO 识别 IntegrityError 转 ValueError"班级已存在"，API 转业务 409 | `dao_class_info.py`、`api/class_info.py` |
| P1 | dao_student 三函数口径不一致（update 无保护）；删除时 DB 故障被吞成 None → 接口返回 **404"未找到对应学生"**，故障伪装成查无此人 | None 只表示真不存在；DB 错误记堆栈后上抛给全局兜底 | `dao_student.py` |
| P2 | statistics 8 处 `f"统计失败: {e}"` 把内部异常原文漏给前端 | 固定文案"统计失败，请查看 logs/app.log" | `api/statistics.py` |

**刻意不动**：teacher/employment 的 HTTPException 风格（冒烟测试绑定 422/404 状态码）；不引入自定义异常类体系（2-3 天项目过度设计）；不在每个 DAO 重复包 try/except（全局兜底已覆盖）。

**验证**：4 套冒烟测试全绿 + 9 项异常场景专项验证（重复建班 409、改名撞名 409、全局兜底 500 统一体、固定文案不泄漏、None 语义正确、HTTPException 不受影响）。

---

## 七、附：全局检索定位方法

在 IDE 中搜索关键字 **`整合`** / **`日志`** / **`异常`**（或 `[整合` / `[日志` / `[异常`），即可按标记逐处比对：

- `[整合·增]` —— 原代码没有，整合审查时新增
- `[整合·改]` —— 原代码有，整合审查时修改
- `[整合·恢复]` —— 原代码被注释，整合审查时恢复（对应需求明确要求的功能）
- `[日志·增]` —— 日志补充轮新增的日志行
- `[异常·增]` / `[异常·改]` —— 异常处理优化轮的新增/修改
