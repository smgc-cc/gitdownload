FROM python:3.9-alpine

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 安装 git
RUN apk add --no-cache git

RUN pip install --no-cache-dir Flask requests gitpython

COPY . .

# 设置 start.sh 可执行权限
RUN chmod +x /app/start.sh

EXPOSE 3000

CMD ["/app/start.sh"]
