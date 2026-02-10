# FastAPI Fibonacci - Тестовый проект для Kubernetes

## Описание
Простое FastAPI приложение с эндпоинтом для вычисления чисел Фибоначчи.

## Эндпоинты
- `GET /` - информация об API
- `GET /fibonacci/{n}` - возвращает n-ое число Фибоначчи
- `GET /health` - health check

## Шаги для развертывания

### 1. Соберите Docker образ
```bash
cd k8s-fastapi-test
docker build -t fastapi-fibonacci:latest .
```

### 2. Проверьте, что Kubernetes работает
```bash
kubectl cluster-info
kubectl get nodes
```

### 3. Разверните приложение в Kubernetes
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 4. Проверьте статус развертывания
```bash
# Проверить pods
kubectl get pods

# Проверить deployment
kubectl get deployments

# Проверить service
kubectl get services

# Детальная информация о pods
kubectl describe pods
```

### 5. Получите доступ к приложению

На Windows с Docker Desktop Kubernetes, сервис будет доступен по адресу:
```
http://localhost:30080
```

Тестовые запросы:
```bash
# Главная страница
curl http://localhost:30080/

# 10-е число Фибоначчи
curl http://localhost:30080/fibonacci/10

# 20-е число Фибоначчи
curl http://localhost:30080/fibonacci/20

# Health check
curl http://localhost:30080/health
```

### 6. Просмотр логов
```bash
# Логи всех pods
kubectl logs -l app=fastapi-fibonacci

# Логи конкретного pod
kubectl logs <pod-name>

# Следить за логами в реальном времени
kubectl logs -f <pod-name>
```

### 7. Масштабирование
```bash
# Увеличить количество реплик
kubectl scale deployment fastapi-fibonacci --replicas=5

# Уменьшить количество реплик
kubectl scale deployment fastapi-fibonacci --replicas=2
```

### 8. Доступ к Kubernetes Dashboard

Вы уже установили dashboard:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
```

Для доступа к dashboard:

#### Создайте admin-user:
```bash
# Создайте файл dashboard-adminuser.yaml
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF
```

#### Получите токен:
```bash
kubectl -n kubernetes-dashboard create token admin-user
```

#### Запустите proxy:
```bash
kubectl proxy
```

#### Откройте dashboard в браузере:
```
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

Введите полученный токен для авторизации.

### 9. Удаление ресурсов
```bash
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
```

## Структура проекта
```
k8s-fastapi-test/
├── app.py              # FastAPI приложение
├── requirements.txt    # Python зависимости
├── Dockerfile          # Docker образ
├── deployment.yaml     # Kubernetes Deployment
├── service.yaml        # Kubernetes Service
└── README.md           # Эта инструкция
```

## Проверка работы Kubernetes

### Базовые проверки:
```bash
# Информация о кластере
kubectl cluster-info

# Версия
kubectl version

# Все ресурсы
kubectl get all

# Nodes
kubectl get nodes

# Namespaces
kubectl get namespaces
```

### Мониторинг приложения:
```bash
# Статус pods в реальном времени
kubectl get pods --watch

# События
kubectl get events --sort-by=.metadata.creationTimestamp

# Использование ресурсов (если установлен metrics-server)
kubectl top pods
kubectl top nodes
```

## Troubleshooting

### Pod не запускается:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Service недоступен:
```bash
kubectl get svc
kubectl describe svc fastapi-fibonacci-service
```

### Перезапуск deployment:
```bash
kubectl rollout restart deployment fastapi-fibonacci
```
