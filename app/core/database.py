#数据库会话获取
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

# DATABASE_URL = "mysql+pymysql://root:123456@192.168.150.60/students"
DATABASE_URL = "mysql+pymysql://root:123456@192.168.1.124/students"

engine= create_engine(
    DATABASE_URL,
    pool_size=5
)
SessionLocal = sessionmaker(bind=engine)
Base=declarative_base()
# 获取会话
def get_db():
    db = SessionLocal()
    try:
        yield db   # 把会话交给调用方
    finally:
        db.close() # 请求结束自动关闭会话，防止连接泄露

