# hello world nginx server
FROM nginx:latest

COPY nginx-selfsigned.crt /etc/nginx/ssl/nginx-selfsigned.crt
COPY nginx-selfsigned.key /etc/nginx/ssl/nginx-selfsigned.key

COPY nginx.conf /etc/nginx/nginx.conf

COPY *.html /usr/share/nginx/html/
COPY *.png /usr/share/nginx/html/