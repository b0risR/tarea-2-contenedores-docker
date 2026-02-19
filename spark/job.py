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

