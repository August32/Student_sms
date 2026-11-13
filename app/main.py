from fastapi  import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import app.core.database
from app.utils.logger import get_logger

from app.api.student import stu_router
from app.api.statistics import stat_router
from app.api.class_info import class_router
from app.api.employment import emp_router
from app.api.teacher import teacher_router
from app.api.score import score_router

logger = get_logger(__name__)

app=FastAPI()
app.include_router(stu_router,tags=["学生"])
app.include_router(class_router, tags=["班级管理"])
app.include_router(stat_router, tags=["统计分析"])   # 挂载子路由
app.include_router(emp_router,tags=["就业信息管理"])
app.include_router(teacher_router,tags=["老师管理"])
app.include_router(score_router, tags=["成绩管理"])


# 前端代码块 ------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def student_management_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="students.html",
        context={"request": request},
    )

@app.get("/{module}", response_class=HTMLResponse, include_in_schema=False)
async def module_page(request: Request, module: str):
    if module == "employment-page":
        module = "employment"
    if module not in {"classes", "teachers", "scores", "employment", "statistics"}:
        return HTMLResponse("Not Found", status_code=404)
    return templates.TemplateResponse(
        request=request,
        name="modules.html",
        context={"request": request, "module": module},
    )
# 前端代码块 ------------------------------------------------


# 全局异常兜底：所有未捕获异常统一收口。
# 原先 DAO 里 raise 上来的错误（班级/就业/成绩落库失败等）会返回 FastAPI 默认的裸
# "Internal Server Error" 文本，既不是项目的统一响应体，堆栈也不进 logs/app.log。
# 这里统一返回 {"code":500,...} 并记完整堆栈，各接口就不用各写一遍 try/except 了。
# 注意：HTTPException（teacher/employment 的 404/422）和参数校验 422 有自己的处理器，不受影响。
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未捕获异常 | %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误，请查看 logs/app.log", "data": None},
    )

#  启动日志：打印已注册接口
_paths = app.openapi().get("paths", {})
result = []
for p, ops in _paths.items():     # p = 路径, ops = 该路径下的方法字典
    for m in ops:                 # m = 方法名（小写）
        result.append(f"{m.upper()} {p}")
logger.info("服务启动完成 | 已注册接口: %s", result)


if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=6003)
