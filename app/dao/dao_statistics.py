# 就业统计的 SQL 查询
# 三个查询都要联表：employments -> students -> classes
#   employments.student_id = students.id
#   students.class_id      = classes.id
from os.path import join

from sqlalchemy.orm import Session

from app.models.employment import Employment
from app.models.student import Student
from app.models.class_info import ClassInfo
from app.models.score import Score


# 算就业时长（天）：offer下发时间 - 就业开放时间，两个时间缺一个就返回 None
def _calc_days(employment_open_date, offer_date):
    if employment_open_date and offer_date:
        return (offer_date - employment_open_date).days
    return None

# 按班级筛选
def _filter_by_class(query, class_id=None, class_name=None):
    if class_id is not None:
        query = query.filter(ClassInfo.id == class_id)            # 按班级编号精确筛
    if class_name:
        query = query.filter(ClassInfo.class_name == class_name)  # 按班级名精确筛
    return query


# 1. 就业薪资最高的前 N 名学生：姓名、班级、就业时间、就业公司（N 默认 5，即需求里的“前五名”）
# [优化] 新参数：top_n=5 取前几名；class_id/class_name 按班级筛
def query_salary_top5(db: Session, top_n=5, class_id=None, class_name=None):
    top_n = min(max(0, int(top_n)), 100)  # 防非法值和上限100
    query = (db.query(Employment, Student, ClassInfo)
            .join(Student, Employment.student_id == Student.id)
            .join(ClassInfo, Student.class_id == ClassInfo.id)
            .filter(Employment.is_deleted == 0,
                    Student.is_deleted == 0,
                    Employment.salary.isnot(None)))   # 没填薪资的不参与排名
    query = _filter_by_class(query, class_id, class_name)  # 班级筛选
    rows = (query.order_by(Employment.salary.desc())       # 薪资从高到低
            .limit(top_n)                                  # 现在取前 top_n 名
            .all())

    # rows 里每一行是 (就业对象, 学生对象, 班级对象)，拆开取字段
    return [
        {
            "name": student.name,
            "class_name": class_info.class_name,
            "employment_open_date": emp.employment_open_date,
            "offer_date": emp.offer_date,
            "company_name": emp.company_name,
            "salary": emp.salary,
        }
        for emp, student, class_info in rows
    ]   #  结果组装：把列表中的每个三元组解包 组装成字典


# 2. 每个学生的就业时长（offer下发时间 - 就业开放时间）
# [优化] 新参数：class_id/class_name 按班级筛（原来只能一次拉全部）
def query_student_duration(db: Session, class_id=None, class_name=None):
    query = (db.query(Employment, Student)
            .join(Student, Employment.student_id == Student.id)
            .filter(Employment.is_deleted == 0,
                    Student.is_deleted == 0))
    # class_id 直接走 students.class_id（不用联表）；class_name 要 join classes 才能比名字
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)
    if class_name:
        query = (query.join(ClassInfo, Student.class_id == ClassInfo.id)
                      .filter(ClassInfo.class_name == class_name))
    rows = query.all()

    return [
        {
            "student_id": student.id,
            "name": student.name,
            "employment_open_date": emp.employment_open_date,
            "offer_date": emp.offer_date,
            "duration_days": _calc_days(emp.employment_open_date, emp.offer_date),
        }
        for emp, student in rows
    ]


# 3. 每个班级的平均就业时长（只统计进入就业阶段的学生 = 有就业开放时间）
# [优化] 新参数：class_id/class_name 按班级筛
def query_class_avg_duration(db: Session, class_id=None, class_name=None):
    query = (db.query(Employment, Student, ClassInfo)
            .join(Student, Employment.student_id == Student.id)
            .join(ClassInfo, Student.class_id == ClassInfo.id)
            .filter(Employment.is_deleted == 0,
                    Student.is_deleted == 0,
                    Employment.employment_open_date.isnot(None)))  # 只统计进入就业阶段的
    query = _filter_by_class(query, class_id, class_name)  # 班级筛选
    rows = query.all()

    # 先按班级把就业时长收集成列表：{班级名: [时长1, 时长2, ...]}
    class_days = {}
    for emp, student, class_info in rows:
        days = _calc_days(emp.employment_open_date, emp.offer_date)
        if days is None:
            continue  # 没有 offer 时间算不出时长，跳过
        class_days.setdefault(class_info.class_name, []).append(days)
        # class_days[]
    #等价于：
        # if class_info.class_name not in class_days:
        #     class_days[class_info.class_name] = []  # 不存在就新建空列表
        # class_days[class_info.class_name].append(days)  # 往对应列表追加

    # 再算每个班的平均值
    result = []
    for cls_name, days_list in class_days.items():
        result.append({
            "class_name": cls_name,
            "student_count": len(days_list),
            "avg_duration_days": round(sum(days_list) / len(days_list), 1),
        })
    return result   # 列表套字典

# 4. 查询所有超过 N 岁的学员的信息（N 默认 30，即需求里的“超过30岁”）
# [优化] 新参数：min_age=30 年龄阈值；class_id/class_name 按班级筛
def query_students_over30(db: Session, min_age=30, class_id=None, class_name=None):
    # outerjoin：没班级照样返回，班级名为空
    query = (db.query(Student, ClassInfo)
            .outerjoin(ClassInfo, Student.class_id == ClassInfo.id)
            .filter(Student.is_deleted == 0,
                    Student.age > min_age))
    query = _filter_by_class(query, class_id, class_name)  # 班级筛选（传了班级就只看该班）
    rows = query.all()

    return [
        {
            "id": student.id,
            "name": student.name,
            "class_name": class_info.class_name if class_info is not None else None,
            "age": student.age,
            "gender": student.gender,
            "native_place": student.native_place,
            "graduate_school": student.graduate_school,
            "major": student.major,
            "education": student.education,
            "consultant_no": student.consultant_no,
            "enroll_time": student.enroll_time,
            "graduate_time": student.graduate_time,
        }
        for student, class_info in rows
    ]

# 5. 统计每个班级的人数以及男生女生的人数
# [优化] 新参数：class_id/class_name 按班级筛（只统计指定班级）
def query_class_gender_count(db: Session, class_id=None, class_name=None):
    # 从班级表出发 left join 学生： 没学生的班级也会出现,对「没有学生的班级」这一行，Student.is_deleted 是 NULL
    query = (db.query(ClassInfo, Student)
            .outerjoin(Student,(Student.class_id == ClassInfo.id)&(Student.is_deleted == 0))
            .filter(ClassInfo.is_deleted == 0))
    query = _filter_by_class(query, class_id, class_name)  # 班级筛选
    rows = query.all()

    # 按班级名收集成{班级名:计数}，最后再转成列表
    result = {}

    for class_info, student in rows:
        item = result.setdefault(class_info.class_name, {
            "class_name": class_info.class_name,
            "total_count": 0,
            "male_count": 0,
            "female_count": 0,
        })
        if student is None:
            continue            # left join 出来的空班级，人数保持 0
        item["total_count"] += 1
        if student.gender == '男':
            item["male_count"] += 1
        elif student.gender == '女':
            item["female_count"] += 1

    return list(result.values())



# 6. 查询每次考试成绩都在80分以上的学生：编号、姓名、成绩
# 口径：80分以上含80分（>= 80）；至少要有一条成绩记录才算
def query_students_all_over80(db: Session):
    rows = (db.query(Score, Student)
            .join(Student, Score.student_id == Student.id)
            .filter(Score.is_deleted == 0,
                    Student.is_deleted == 0)
            .order_by(Score.student_id, Score.exam_sequence)  # 按学生、按考核序次排好
            .all())

    # 先按学生把成绩收集成 {学生编号: {"name": ..., "scores": [...]}}
    groups = {}
    for score_row, student in rows:
        item = groups.setdefault(student.id, {"student_id": student.id,
                                             "name": student.name,
                                             "scores": []})
        item["scores"].append({"exam_sequence": score_row.exam_sequence,
                               "score": score_row.score})

    # 只保留"所有成绩都 >= 80"的学生（有一门低于80就淘汰）
    return [g for g in groups.values()
            if min(s["score"] for s in g["scores"]) >= 80]


# 7. 查询两次以上不及格的学生：姓名、班级、不及格成绩
# 口径：不及格 = 成绩 < 60；两次以上 = 不及格次数 >= 2（含两次）
def query_students_multi_fail(db: Session):
    rows = (db.query(Score, Student, ClassInfo)
            .join(Student, Score.student_id == Student.id)
            .join(ClassInfo, Student.class_id == ClassInfo.id)
            .filter(Score.is_deleted == 0,
                    Student.is_deleted == 0,
                    ClassInfo.is_deleted == 0,
                    Score.score < 60)                # 只取不及格的成绩
            .order_by(Score.student_id, Score.exam_sequence)
            .all())

    # 按学生把不及格成绩收集成 {学生编号: {"name": ..., "fail_scores": [...]}}
    groups = {}
    for score_row, student, class_info in rows:
        item = groups.setdefault(student.id, {"name": student.name,
                                             "class_name": class_info.class_name,
                                             "fail_scores": []})
        item["fail_scores"].append({"exam_sequence": score_row.exam_sequence,
                                    "score": score_row.score})

    # 两次以上：不及格次数 >= 2
    return [g for g in groups.values() if len(g["fail_scores"]) >= 2]


# 8. 统计每次考试每个班级的平均分，按照从高到低排序
def query_class_exam_avg(db: Session):
    rows = (db.query(Score, Student, ClassInfo)
            .join(Student, Score.student_id == Student.id)
            .join(ClassInfo, Student.class_id == ClassInfo.id)
            .filter(Score.is_deleted == 0,
                    Student.is_deleted == 0,
                    ClassInfo.is_deleted == 0)
            .all())

    # 按 (考核序次, 班级) 把成绩收集成列表
    groups = {}
    for score_row, student, class_info in rows:
        key = (score_row.exam_sequence, class_info.class_name)
        groups.setdefault(key, []).append(score_row.score)

    # 算每组平均分
    result = []
    for (exam_sequence, class_name), scores in groups.items():
        result.append({
            "exam_sequence": exam_sequence,
            "class_name": class_name,
            "avg_score": round(sum(scores) / len(scores), 1),
            "student_count": len(scores),
        })

    # 按照平均分从高到低排序
    result.sort(key=lambda x: x["avg_score"], reverse=True)
    return result