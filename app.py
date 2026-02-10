from fastapi import FastAPI, HTTPException

app = FastAPI(title="Fibonacci API")


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


@app.get("/")
async def root():
    return {
        "message": "Fibonacci API",
        "endpoints": {
            "/fibonacci/{n}": "Возвращает n-ое число Фибоначчи"
        }
    }


@app.get("/fibonacci/{n}")
async def get_fibonacci(n: int):
    """
    Возвращает n-ое число Фибоначчи
    
    - **n**: позиция в последовательности (неотрицательное целое число)
    """
    if n < 0:
        raise HTTPException(status_code=400, detail="n должно быть неотрицательным числом")
    
    if n > 1000:
        raise HTTPException(status_code=400, detail="n слишком большое (максимум 1000)")
    
    result = fibonacci(n)
    
    return {
        "n": n,
        "fibonacci": result
    }


@app.get("/health")
async def health():
    """Health check эндпоинт для Kubernetes"""
    return {"status": "healthy"}