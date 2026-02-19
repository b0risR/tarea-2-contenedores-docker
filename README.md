![](https://d2q79iu7y748jz.cloudfront.net/s/_squarelogo/128x128/bf65e024aee34c3cce4bb71e2dce9fc1) 
## Universidad Europea de Andalucía
Máster Universitario en Análisis de Grandes Cantidades de Datos (Big Data)

Estudiante: Boris Paternina

## tarea-2-contenedores-docker

Levantar una aplicación simple de procesamiento de datos usando 
PySpark que se conecte a una base de datos MySQL para leer/escribir datos.

Preguntas a Resolver: 

1.  Comparte y explica el código desarrollado demostrando que funciona.

Con el contenedor `mysql` en funcionamiento después de la ejecución del 
análisis, puede ejecutarse el siguiente 
comando:

`docker exec -it mysql mysql -uroot -proot -e "SELECT * 
FROM datos.resultado_analisis LIMIT 5;"`

Presentando la siguiente tabla como resultado:

```bash
+---------+--------------+-----------+-----------+
| Model   | count(Model) | min(Year) | max(Year) |
+---------+--------------+-----------+-----------+
| MODEL Y |        59314 |      2020 |      2026 |
| MODEL 3 |        37897 |      2017 |      2026 |
| LEAF    |        13512 |      2011 |      2026 |
| MODEL S |         7747 |      2012 |      2026 |
| BOLT EV |         7715 |      2017 |      2023 |
+---------+--------------+-----------+-----------+
```

Código desarrollado en [docker-compose.yml](https://github.com/b0risR/tarea-2-contenedores-docker/blob/main/docker-compose.yml)

```bash
services:
  mysql:
    image: mysql:lts
    container_name: mysql
    environment:
      MYSQL_ROOT_PASSWORD: root
    ports:
      - "3306:3306"
    volumes:
      - ./mysql/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - spark-net

  spark:
    build: ./spark
    container_name: tarea2spark
    user: root
    ports:
      - "4040:4040"
    depends_on:
      - mysql
    volumes:
       - ./spark:/opt/spark/work-dir
    environment:
      - SPARK_HOME=/opt/spark
    command: >
      /opt/spark/bin/spark-submit
      --jars /opt/spark/jars/mysql-connector-j-8.0.33.jar
      /opt/spark/work-dir/job.py
    networks:
      - spark-net

networks:
  spark-net:
```

Código desarrollado en [init.sql](https://github.com/b0risR/tarea-2-contenedores-docker/blob/main/mysql/init.sql)

```bash
CREATE DATABASE IF NOT EXISTS datos;
USE datos;

CREATE TABLE IF NOT EXISTS coches_electricos (
    County TEXT,
    City TEXT,
    State TEXT,
    Year INT,
    Model TEXT,
    Electric_Range INT,
    Electric_Utility TEXT
);
```

Código desarrollado en [Dockerfile](https://github.com/b0risR/tarea-2-contenedores-docker/blob/main/spark/Dockerfile)

```bash
FROM spark:python3

USER root

# Instalación del driver JDBC de MySQL dentro del contenedor spark
RUN mkdir -p /opt/spark/jars && \
    curl -L -o /opt/spark/jars/mysql-connector-j-8.0.33.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar

# Volver al usuario por defecto
USER spark
```

Código desarrollado en [job.py](https://github.com/b0risR/tarea-2-contenedores-docker/blob/main/spark/job.py)

```bash
import urllib.request
import os
import time
from pyspark import SparkConf
from pyspark.sql import SparkSession
import pyspark.sql.functions as sf

if __name__ == "__main__":
    conf = SparkConf()
    conf.setMaster("local[*]")
    conf.setAppName("conversionInicial")
    spark = SparkSession.builder.config(conf=conf).getOrCreate()

    jdbc_url = "jdbc:mysql://mysql:3306/datos"
    properties = {
        "user": "root",
        "password": "root",
        "driver": "com.mysql.cj.jdbc.Driver"
    }

    # inicio del proceso batch
    url = "https://data.wa.gov/api/views/f6w7-q2d2/rows.csv?accessType=DOWNLOAD"
    # dest_path = "/opt/spark/work-dir/electric.csv"
    print("descargando el archivo electric.csv , espere un momento..")
    urllib.request.urlretrieve(url, "/tmp/electric.csv")

    DFread = spark.read.csv("/tmp/electric.csv", header=True, sep=",", inferSchema=True)

    electric = DFread.select('County', 'City', 'State', 'Model Year',
                             'Model', 'Electric Range', 'Electric Utility')
    electric = (electric.withColumnRenamed("Electric Utility", "Electric_Utility")
                .withColumnRenamed("Model Year", "Year")
                .withColumnRenamed("Electric Range", "Electric_Range"))

    electric.show(5)
    print("\n\nDataFrame descargado")
    electric.printSchema()

    # populado de la tabla en mysql
    electric.write.jdbc(
        url=jdbc_url,
        table="coches_electricos",
        mode="overwrite",
        properties=properties
    )

    # lectura y análisis de la tabla coches_electricos
    DFanalisis = spark.read.jdbc(
        url=jdbc_url,
        table="coches_electricos",
        properties=properties)

    DFresultado = DFanalisis.groupBy("Model").agg(sf.count(DFanalisis.Model),
                                   sf.min(DFanalisis.Year),
                                   sf.max(DFanalisis.Year)).sort(sf.desc("count(Model)"))
    DFresultado.show(5)
    print("\n\nResultado del análisis de la tabla coches_electricos en mysql")

    # guardado de la tabla con los resultados
    DFresultado.write.jdbc(
        url=jdbc_url,
        table="resultado_analisis",
        mode="overwrite",
        properties=properties
    )
    spark.stop()

```

2.  ¿Qué se debería modificar en el compose.yaml para que Spark pudiera 
trabajar en modo clúster? 

Debe reemplazarce el servicio `spark` por los servicios `spark-master` 
y `spark-worker`

```bash
services:  
  spark-master:
    build: ./spark
    container_name: spark-master
    user: root
    ports:
      - "8080:8080" # Spark Master
      - "7077:7077" # Spark Cluster
    environment:
      - SPARK_MODE=master
    networks:
      - spark-net

  spark-worker:
    build: ./spark
    user: root
    depends_on:
      - spark-master
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_CORES=1
      - SPARK_WORKER_MEMORY=1G
    networks:
      - spark-net      
      
    (...)
```

3.  ¿Qué ocurre con los datos en la base de datos si los contenedores 
en ejecución se eliminan? 

La culminación normal de los Spark jobs no causan la eliminación de los
contenedores; no obstante, ejecutar el comando `docker rm <container>` causará
la eliminación de éstos con la consiguiente pérdida de las bases de datos.

4.  Si se deseara compartir este stack con otro profesional, ¿Cómo se podría hacer? ¿Podría 
el compañero tener problemas de configuración para ejecutarlo en su equipo? 

Deben eliminarse las claves hardcoded en los scripts, y deben guardarse
en un lugar seguro. Deben documentarse los requisitos, arquitectura de los
archivos, y comandos de arranque. Finalmente, se debe hacer una verificación 
final mediante los comandos `docker-compose down -v` seguido de
`docker compose up`. Estos serían los pasos necesarios para la correcta 
portabilidad del proyecto.