FROM python
RUN mkdir /app
COPY server.py /app/
WORKDIR /app
RUN pip install flask
EXPOSE 8080
CMD ["python", "server.py"]
