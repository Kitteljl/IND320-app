"""Local-only helpers: Spark and Cassandra. Used from the notebook, not the app."""

import os
import subprocess

CASSANDRA_HOST = "127.0.0.1"
CASSANDRA_PORT = 9042
KEYSPACE = "ind320"
CONNECTOR = "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1"  # matches Spark 3.5


def _set_java_home():
    """Find Java 17 if JAVA_HOME isn't already set."""
    if os.environ.get("JAVA_HOME"):
        return
    homebrew_java = "/opt/homebrew/opt/openjdk@17"
    if os.path.isdir(homebrew_java):
        os.environ["JAVA_HOME"] = homebrew_java
        return
    try:
        os.environ["JAVA_HOME"] = subprocess.check_output(
            ["/usr/libexec/java_home", "-v", "17"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        pass
    
def get_spark():
    """Start (or reuse) a local Spark session connected to Cassandra."""
    _set_java_home()
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName("IND320")
        .master("local[*]")
        .config("spark.jars.packages", CONNECTOR)
        .config("spark.cassandra.connection.host", CASSANDRA_HOST)
        .config("spark.cassandra.connection.port", str(CASSANDRA_PORT))
        .config("spark.cassandra.connection.localConnectionsPerExecutor", "1")
        .config("spark.cassandra.connection.remoteConnectionsPerExecutor", "1")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def get_cassandra_session(keyspace: str | None = None):
    """Plain Python session (for CREATE TABLE and small queries)."""
    from cassandra.cluster import Cluster

    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    return cluster.connect(keyspace)


def ensure_keyspace():
    session = get_cassandra_session()
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)
    return session


def cassandra_write(df, table: str, mode: str = "append"):
    """Write a Spark DataFrame to a Cassandra table."""
    (df.write.format("org.apache.spark.sql.cassandra")
       .options(table=table, keyspace=KEYSPACE)
       .mode(mode).save())


def cassandra_read(spark, table: str):
    """Read a Cassandra table as a Spark DataFrame."""
    return (spark.read.format("org.apache.spark.sql.cassandra")
            .options(table=table, keyspace=KEYSPACE)
            .load())