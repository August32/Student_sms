
from fastapi import APIRouter, Depends
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.dao.dao_class_info import query_class_infos, create_class_info, update_class_info, delete_class_info
from app.schemas.class_info import (
    ClassInfoQuery, ClassInfoResponse, ClassInfoCreate, ClassInfoUpdate, ClassInfoDelete,
)
from app.utils.logger import get_logger  # [日志·增] 班级模块原先没有任何日志输出

logger = get_logger(__name__)  # [日志·增]
class_router = APIRouter()

# 按照班级名称、班主任、班级状态、开课时间范围、班级人数范围等信息查询班级信息
@class_router.get('/class_info',response_model=ClassInfoResponse)
async def get_class_infos(params:ClassInfoQuery=Depends(),
                          db:Session=Depends(get_db)):
    class_info_list=query_class_infos(db=db,params=params)
    logger.info("查询班级列表 | class_name=%s class_teacher=%s | 返回 %d 条",
                params.class_name, params.class_teacher, len(class_info_list))  # [日志·增] 列表查询记条数
    return {"code":200,
            "message":"返回成功",
            "data":class_info_list
            }

# 新增班级信息
@class_router.post('/class_info',response_model=ClassInfoResponse)
async def create_class_infos(params:ClassInfoCreate,
                             db:Session=Depends(get_db)): #给这个接口自动配一个数据库连接，用完自动关
    try:
        class_info =create_class_info(db=db,params=params)
    except ValueError as error:  # [异常·增]
        return {"code": 409,
                "message": str(error),
                "data": None
                }
    logger.info("新增班级成功 | id=%s class_name=%s", class_info.id, class_info.class_name)  # [日志·增]
    return {"code": 201,
            "message": "新增成功",
            "data": class_info
            }

# 修改班级信息
@class_router.put('/class_info/{class_name}',response_model=ClassInfoResponse)
async def update_class_infos(class_name:str,params:ClassInfoUpdate,
                            db:Session=Depends(get_db)):
    try:
        class_info = update_class_info(class_name=class_name,db=db,params=params)
    except ValueError as error:  # [异常·增] 改名撞重复班级名 → 409
        return {"code": 409,
                "message": str(error),
                "data": None
                }
    if class_info is None:
        logger.warning("修改班级未命中 | class_name=%s", class_name)  # [日志·增]
        return {"code":404,
                "message":"班级不存在",
                "data":None
                }
    logger.info("修改班级成功 | class_name=%s", class_name)  # [日志·增]
    return {"code":200,
            "message":"修改成功",
            "data":class_info
            }

# 删除班级信息（软删除）
@class_router.delete('/class_info',response_model=ClassInfoResponse)
async def delete_class_infos(params:ClassInfoDelete,
                             db:Session=Depends(get_db)):
    class_info=delete_class_info(db=db,params=params)
    if class_info is None:
        logger.warning("删除班级未命中 | class_name=%s", params.class_name)  # [日志·增]
        return {"code":404,
                "message":"班级不存在",
                "data":None
                }
    logger.info("删除班级成功 | id=%s class_name=%s", class_info.id, class_info.class_name)  # [日志·增] 逻辑删除
    return {"code":200,
            "message":"删除成功",
            "data":class_info
            }



