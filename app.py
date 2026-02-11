from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import time
import asyncpg
from contextlib import asynccontextmanager

# Конфигурация БД
DATABASE_URL = "postgresql://gen_user:Nv1#mUmS@^1wH,@31.130.135.213:5432/default_db"

# Пул соединений
db_pool = None


class FibonacciResponse(BaseModel):
    n: int
    fibonacci: int
    execution_time_ms: float
    db_operation_time_ms: Optional[float] = None
    user_stats: Optional[dict] = None


async def get_db_pool():
    """Получение пула соединений с БД"""
    return db_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool
    db_pool = await asyncpg.create_pool(
        user="gen_user",
        password="Nv1#mUmS@^1wH,",
        database="default_db",
        host="31.130.135.213",
        port=5432,
        min_size=10,
        max_size=50
    )
    yield
    # Shutdown
    await db_pool.close()


app = FastAPI(title="Fibonacci API", lifespan=lifespan)


def fibonacci(n: int) -> int:
    """Вычисляет n-ое число Фибоначчи"""
    if n < 0:
        raise ValueError("n должно быть неотрицательным")
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


async def complex_db_operation(pool: asyncpg.Pool, n: int, result: int, exec_time: float):
    """
    Сложная операция с БД:
    1. Получаем случайного пользователя
    2. Сохраняем запрос в БД
    3. Обновляем статистику по числу
    4. Получаем аналитику по пользователю с JOIN'ами
    5. Вычисляем агрегации
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. Получаем случайного активного пользователя
            user = await conn.fetchrow("""
                SELECT id, username, email 
                FROM users 
                WHERE is_active = TRUE 
                ORDER BY random() 
                LIMIT 1
            """)
            
            if not user:
                return None
            
            # 2. Сохраняем запрос
            await conn.execute("""
                INSERT INTO fibonacci_requests (user_id, n_value, result, execution_time_ms)
                VALUES ($1, $2, $3, $4)
            """, user['id'], n, result, exec_time)
            
            # 3. Обновляем статистику по числу (upsert)
            await conn.execute("""
                INSERT INTO number_stats (number, request_count, last_requested)
                VALUES ($1, 1, CURRENT_TIMESTAMP)
                ON CONFLICT (number) 
                DO UPDATE SET 
                    request_count = number_stats.request_count + 1,
                    last_requested = CURRENT_TIMESTAMP
            """, n)
            
            # 4. Получаем сложную аналитику по пользователю
            stats = await conn.fetchrow("""
                SELECT 
                    u.username,
                    COUNT(fr.id) as total_requests,
                    AVG(fr.execution_time_ms) as avg_execution_time,
                    MAX(fr.n_value) as max_n_requested,
                    MIN(fr.n_value) as min_n_requested,
                    SUM(CASE WHEN fr.created_at > CURRENT_TIMESTAMP - interval '24 hours' 
                        THEN 1 ELSE 0 END) as requests_last_24h,
                    COUNT(DISTINCT fr.n_value) as unique_numbers_requested
                FROM users u
                LEFT JOIN fibonacci_requests fr ON u.id = fr.user_id
                WHERE u.id = $1
                GROUP BY u.id, u.username
            """, user['id'])
            
            # 5. Получаем топ-5 самых популярных чисел
            popular_numbers = await conn.fetch("""
                SELECT number, request_count
                FROM number_stats
                ORDER BY request_count DESC
                LIMIT 5
            """)
            
            # 6. Получаем статистику по времени выполнения для этого числа
            n_stats = await conn.fetchrow("""
                SELECT 
                    AVG(execution_time_ms) as avg_time,
                    MIN(execution_time_ms) as min_time,
                    MAX(execution_time_ms) as max_time,
                    COUNT(*) as total_calculations
                FROM fibonacci_requests
                WHERE n_value = $1
            """, n)
            
            return {
                "user_id": user['id'],
                "username": stats['username'],
                "total_requests": stats['total_requests'],
                "avg_execution_time": float(stats['avg_execution_time']) if stats['avg_execution_time'] else 0,
                "max_n_requested": stats['max_n_requested'],
                "min_n_requested": stats['min_n_requested'],
                "requests_last_24h": stats['requests_last_24h'],
                "unique_numbers_requested": stats['unique_numbers_requested'],
                "popular_numbers": [
                    {"number": row['number'], "count": row['request_count']} 
                    for row in popular_numbers
                ],
                "n_statistics": {
                    "avg_time": float(n_stats['avg_time']) if n_stats['avg_time'] else 0,
                    "min_time": float(n_stats['min_time']) if n_stats['min_time'] else 0,
                    "max_time": float(n_stats['max_time']) if n_stats['max_time'] else 0,
                    "total_calculations": n_stats['total_calculations']
                }
            }


@app.get("/")
async def root():
    return {
        "message": "Fibonacci API",
        "endpoints": {
            "/fibonacci/{n}": "Возвращает n-ое число Фибоначчи",
            "/fibonacci/{n}?with_db=true": "Возвращает n-ое число Фибоначчи с операцией БД"
        }
    }


@app.get("/fibonacci/{n}", response_model=FibonacciResponse)
async def get_fibonacci(
    n: int, 
    with_db: bool = False,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Возвращает n-ое число Фибоначчи
    
    - **n**: позиция в последовательности (неотрицательное целое число)
    - **with_db**: если True, выполняет сложную операцию с БД для теста производительности
    """
    if n < 0:
        raise HTTPException(status_code=400, detail="n должно быть неотрицательным числом")
    
    if n > 1000:
        raise HTTPException(status_code=400, detail="n слишком большое (максимум 1000)")
    
    # Вычисление числа Фибоначчи
    start_time = time.time()
    result = fibonacci(n)
    execution_time = (time.time() - start_time) * 1000
    
    # Опциональная операция с БД
    db_operation_time = None
    user_stats = None
    
    if with_db and pool:
        db_start = time.time()
        try:
            user_stats = await complex_db_operation(pool, n, result, execution_time)
            db_operation_time = (time.time() - db_start) * 1000
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return FibonacciResponse(
        n=n,
        fibonacci=result,
        execution_time_ms=round(execution_time, 3),
        db_operation_time_ms=round(db_operation_time, 3) if db_operation_time else None,
        user_stats=user_stats
    )


@app.get("/health")
async def health():
    """Health check эндпоинт для Kubernetes"""
    db_healthy = db_pool is not None
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected"
    }


@app.get("/stats/popular")
async def get_popular_numbers(pool: asyncpg.Pool = Depends(get_db_pool), limit: int = 10):
    """Получить самые популярные числа Фибоначчи"""
    async with pool.acquire() as conn:
        results = await conn.fetch("""
            SELECT number, request_count, last_requested
            FROM number_stats
            ORDER BY request_count DESC
            LIMIT $1
        """, limit)
        
        return {
            "popular_numbers": [
                {
                    "number": row['number'],
                    "request_count": row['request_count'],
                    "last_requested": row['last_requested'].isoformat()
                }
                for row in results
            ]
        }


@app.get("/stats/users/{user_id}")
async def get_user_stats(user_id: int, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Получить статистику по пользователю"""
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT * FROM user_fibonacci_analytics
            WHERE user_id = $1
        """, user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="User not found")
        
        return dict(stats)