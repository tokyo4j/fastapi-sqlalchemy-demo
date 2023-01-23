from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, select, insert, delete, update
import uvicorn

DB_FILENAME = "test.db"
db_url = f"sqlite+aiosqlite:///{DB_FILENAME}"

Base = declarative_base()


class Task(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


app = FastAPI()

engine = create_async_engine(db_url)

session_maker = sessionmaker(engine, class_=AsyncSession)


async def get_session():
    async with session_maker() as session:
        yield session


@app.on_event("startup")
async def setup(session: AsyncSession = Depends(get_session)):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await session.execute(
            insert(Task),
            [{"name": n} for n in ["Homework", "Laundry", "Meeting"]],
        )
        await session.commit()


@app.get("/api/tasks")
async def get_tasks(session: AsyncSession = Depends(get_session)):
    users = await session.execute(select(Task))
    return users.scalars().all()


@app.put("/api/task")
async def put_task(name: str, session: AsyncSession = Depends(get_session)):
    await session.execute(insert(Task).values(name=name))
    await session.commit()


@app.delete("/api/task/{id}")
async def delete_task(id: int, session: AsyncSession = Depends(get_session)):
    await session.execute(delete(Task).where(Task.id == id))
    await session.commit()


@app.post("/api/task/{id}")
async def update_task(id: int, name: str, session: AsyncSession = Depends(get_session)):
    await session.execute(update(Task).where(Task.id == id).values(name=name))
    await session.commit()


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, host="127.0.0.1")
