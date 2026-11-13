from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.dao.dao_score import (
    dao_create_score,
    dao_delete_score,
    dao_get_scores,
    dao_update_score,
)
from app.schemas.score import ScoreDetail, ScoreRequest, ScoreResponse
from app.utils.logger import get_logger
logger = get_logger(__name__)
# 创建成绩模块的子路由
score_router = APIRouter()
# 好处：模块化——每个模块一个 router，互不干扰。
# ==================== 查询成绩 ====================
@score_router.get("/score/{stu_id}", response_model=ScoreResponse)
#FastAPI 自动创建数据库会话传给函数，用完自动关闭连接
async def get_scores(stu_id: int, db=Depends(get_db)):#声明查的是哪一个学生
#第一行把 URL 里的学生编号包装成查询条件对象传给 DAO
    score_filter = ScoreRequest(student_id=stu_id) #只按学生编号查，其他条件不管
    score_list = dao_get_scores(db, score_filter, 0).all() # 调 DAO 查数据
    if not score_list:
        logger.error("查询成绩失败：学生 %s 没有成绩记录", stu_id)
        return {
            "code": 404,
            "message": "没有匹配到成绩",
            "data": None,
        }      # 如果列表为空，返回 404
    data = [ScoreDetail.model_validate(item) for item in score_list] #把成绩表中的每一个被遍历出的ORM对象转成Pydantic对象
    logger.info("查询学生成绩 | student_id=%s | 返回 %d 条", stu_id, len(score_list))
    return {
        "code": 200,
        "message": "返回成功",
        "data": data
    } #最后装进统一的 code / message / data 格式返回

# ==================== 录入成绩 ====================
# POST = “提交新数据”。请求体（body）= 前端发来的 JSON，
# FastAPI 按 ScoreRequest 自动校验并转成 body 对象（格式不合法直接 422）。
@score_router.post("/score/", response_model=ScoreResponse)
#1.必填字段校验
async def create_score(body: ScoreRequest, db=Depends(get_db)):
    if body.student_id is None or body.exam_sequence is None or body.score is None:
        logger.warning("录入成绩被拒 | 必填项缺失 student_id=%s exam_sequence=%s", body.student_id, body.exam_sequence)  # [日志·增]
        return {
            "code": 400,
            "message": "学生编号、考核序次和成绩不能为空",
            "data": None
        }   #检查必填字段，三个字段只要缺一个就报错400
    try:
        new_score = dao_create_score(db, body)
    except ValueError as error:
        logger.warning("录入成绩被拒 | %s", error)
        return {
            "code": 404,
            "message": str(error),
            "data": None
        } #用 try/except 包起来——因为 DAO 会先查学生存不存在，不存在...
    if not new_score:
        logger.warning("录入成绩被拒 | 重复录入 student_id=%s exam_sequence=%s", body.student_id, body.exam_sequence)  # [日志·增]
        return {
            "code": 409,
            "message": "该学生本次考核成绩已经存在",
            "data": None
        }  #判断是不是重复录入，DAO 发现同一个学生同一次考核已有成绩时返回 None。
    logger.info("录入成绩成功 | student_id=%s exam_sequence=%s score=%s",
                body.student_id, body.exam_sequence, body.score)
    return {
        "code": 201,
        "message": "录入成功",
        "data": ScoreDetail.model_validate(new_score)
    }   # 这说明成功了，返回 201 和新成绩

# ==================== 修改成绩 ====================
@score_router.put("/score", response_model=ScoreResponse)
async def update_score(body: ScoreRequest, db=Depends(get_db)):
    # student_id 和 exam_sequence 用来定位要修改哪条成绩——缺一个就找不到目标。
    if body.student_id is None or body.exam_sequence is None:
        return {
            "code": 400,
            "message": "学生编号和考核序次不能为空",
            "data": None
        }
    update_dict = body.model_dump(    #把请求对象转成字典，方便后面逐个字段处理
        exclude_none=True,   #没传的字段（值是 None）不进字典,防止没传的字段被覆盖成空值
        exclude={"student_id", "exam_sequence"},  #定位字段不许进字典。用来找哪条，不是"改成什么"的，防止越权改身份
    )
    if not update_dict:
        logger.warning("修改成绩被拒 | 无修改内容 student_id=%s exam_sequence=%s", body.student_id, body.exam_sequence)  # [日志·增]
        return {
            "code": 400,
            "message": "没有需要修改的内容",
            "data": None,
        }

    updated_score = dao_update_score(db, body, update_dict)

    if not updated_score:
        logger.warning("修改成绩未命中 | student_id=%s exam_sequence=%s", body.student_id, body.exam_sequence)  # [日志·增]
        return {
            "code": 404,
            "message": "没有匹配到要修改的成绩",
            "data": None,
        } #DAO 返回 None 说明没找到目标记录（不存在或已被逻辑删除）

    logger.info("修改成绩成功 | student_id=%s exam_sequence=%s 修改项=%s",
                body.student_id, body.exam_sequence, list(update_dict.keys()))  # [日志·增] 记修改了哪些字段

    return {
        "code": 200,
        "message": "修改成功",
        "data": ScoreDetail.model_validate(updated_score),
    }


# ==================== 删除成绩 ====================
@score_router.delete("/score", response_model=ScoreResponse)
async def delete_score(body: ScoreRequest, db=Depends(get_db)):
    if body.student_id is None or body.exam_sequence is None:
        return {
            "code": 400,
            "message": "学生编号和考核序次不能为空",
            "data": None,
        }
    deleted_score = dao_delete_score(db, body)

    if not deleted_score:
        logger.warning("删除成绩未命中 | student_id=%s exam_sequence=%s", body.student_id, body.exam_sequence)
        return {
            "code": 404,
            "message": "没有匹配到要删除的成绩",
            "data": None
        }

    logger.info("删除成绩成功 | student_id=%s exam_sequence=%s score=%s",
                deleted_score.student_id, deleted_score.exam_sequence, deleted_score.score)  # [日志·增] 逻辑删除，记下被删的成绩值便于追溯

    return {
        "code": 200,
        "message": "删除成功",
        "data": ScoreDetail.model_validate(deleted_score),
    }