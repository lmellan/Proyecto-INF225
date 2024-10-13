# Usa una imagen base oficial de Python
FROM python:3.9-slim

# Set environment variables, recommended to udpate the mysql password and use  
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo
WORKDIR /app

# Add the current directory files (on your machine) to the container
ADD . /app/

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expone el puerto que el servidor Django utilizará
EXPOSE 8001

# Comando para correr el servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
