FROM nginx:1.18.0

ADD nginx.conf /etc/nginx/nginx.conf

RUN mkdir /app
COPY index.html /app
COPY assets /app

EXPOSE 8080:8080

CMD ["nginx", "-g", "daemon off;"]
