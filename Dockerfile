FROM nginx:alpine
RUN apk add --no-cache python3
COPY public /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY proxy/server.py /proxy/server.py
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
