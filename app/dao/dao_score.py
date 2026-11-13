# ---------- 标准库 ----------
from datetime import datetime
from sqlalchemy import and_
# ---------- 本项目的模型层 ----------
from app.models.score import Score
from app.models.student import Student  # [整合·增] 成绩-学生联动：录入前确认学生存在
# ==================== 查询成绩 ====================
def dao_get_scores(db,score_filter,is_deleted=0):
    query=db.query(Score).filter(Score.is_deleted == is_deleted)
    # 把用户传入的筛选条件一个一个收集起来，先放进列表。
    conditions=[]
    if score_filter.student_id is not None:
        conditions.append(Score.student_id == score_filter.student_id)
    if score_filter.exam_sequence is not None:
        conditions.append(Score.exam_sequence == score_filter.exam_sequence)
    if score_filter.score is not None:
        conditions.append(Score.score == score_filter.score)
    if score_filter.exam_date is not None:
        conditions.append(Score.exam_date == score_filter.exam_date)
    if score_filter.remark is not None:
        conditions.append(Score.remark == score_filter.remark)
    if conditions:
        query = query.filter(and_(*conditions))
    return query
# ==================== 录入成绩 ====================
def dao_create_score(db, score_data):
    # ---------- 第 0 步：确认学生存在（成绩-学生联动）----------
    student = (db.query(Student)
               .filter(Student.id == score_data.student_id, Student.is_deleted == 0)
               .first())
    if student is None:
        raise ValueError("学生不存在或已删除，无法录入成绩")  # student_id 是外键，学生不存在时插入直接报错
    # ---------- 第 1 步：查重（防重复录入）----------
    # 模型里有唯一约束：同一个学生每次考核只允许一条成绩。
    old_score = (
        db.query(Score)
        .filter(
            Score.student_id == score_data.student_id,
            Score.exam_sequence == score_data.exam_sequence,
        )
        .first()
    )
    if old_score:
        if old_score.is_deleted == 0:
            return None  # 情况A:已存在有效成绩，返回 None 让 API 层转成 409
        # 情况 B：旧记录已被逻辑删除 → “复活并覆盖”旧记录。
        old_score.score = score_data.score
        old_score.exam_date = score_data.exam_date
        old_score.remark = score_data.remark
        old_score.is_deleted = 0          # 复活：标记为未删除
        old_score.deleted_at = None       # 清空删除时间
        db.commit()                       # 提交修改
        db.refresh(old_score)             # 从数据库重新读一遍，拿到最新的时间戳等字段
        return old_score
    # ---------- 第 2 步：正常插入新记录 ---------
    new_score = Score(
        student_id=score_data.student_id,
        exam_sequence=score_data.exam_sequence,
        score=score_data.score,
        exam_date=score_data.exam_date,
        remark=score_data.remark,
    )
    db.add(new_score)
    db.commit()
    db.refresh(new_score)  # 刷新对象，拿回数据库生成的字段（id、时间戳）
    return new_score
# ==================== 修改成绩 ====================
def dao_update_score(db, filter_model, update_dict):
    score = (
        db.query(Score)
        .filter(
            Score.student_id == filter_model.student_id,
            Score.exam_sequence == filter_model.exam_sequence,
            Score.is_deleted == 0,
        )
        .first()
    )
    if not score:
        return None  # 没找到：要么真没有，要么已被逻辑删除
    allow_fields = {"score", "exam_date", "remark"}
    for field, value in update_dict.items():
        if field in allow_fields:
            setattr(score, field, value) # setattr(对象, "字段名", 新值)：动态给对象的字段赋值，
    db.commit()  # 提交修改（真正 UPDATE 进数据库）
    db.refresh(score)  # 回读最新状态（updated_at 等自动生成的字段会刷新到对象）

    return score
# ==================== 删除成绩 ====================
def dao_delete_score(db, filter_model):
    score = (
        db.query(Score)
        .filter(
            Score.student_id == filter_model.student_id,
            Score.exam_sequence == filter_model.exam_sequence,
            Score.is_deleted == 0,
        )
        .first()
    )
    if not score:
        return None  # 没找到（或已删过一次，is_deleted 已是 1，查不到）
    # 逻辑删除的全部动作就这两行：
    score.is_deleted = 1              # 打上“已删除”标记
    score.deleted_at = datetime.now()  # 记下删除时间（datetime.now() = 此时此刻）
    db.commit()  # 提交：数据库里执行 UPDATE ... SET is_deleted=1, deleted_at=...
    db.refresh(score)
    return score

