FROM spark:python3

USER root

# Instalación del driver JDBC de MySQL dentro del contenedor spark
RUN mkdir -p /opt/spark/jars && \
    curl -L -o /opt/spark/jars/mysql-connector-j-8.0.33.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar

# Volver al usuario por defecto
USER spark

