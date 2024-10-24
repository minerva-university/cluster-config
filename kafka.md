```sh

# Initial setup - the ??? should be replaced with the version number

wget https://archive.apache.org/dist/kafka/???
sudo tar -xzvf kafka_??? -C /opt
sudo mkdir -p /data/kafka-logs
sudo mkdir -p /data/kafka-broker
sudo ln -s /opt/kafka_??? /opt/kafka
sudo useradd -m -s /bin/bash kafka
sudo chown kafka -R /opt/kafka_??? /data/kafka-logs /data/kafka-broker
sudo su - kafka

# Run this on each node, changing the CURRENT_SERVER_INDEX for each node (0,1,2)

export CURRENT_SERVER_INDEX=2
export CLUSTER_UUID=dZmpfrGnSaq_XBDWsSsKPg
cd /opt/kafka/config/kraft
sed -i "s#node.id=.*#node.id=${CURRENT_SERVER_INDEX}#g" controller.properties

sed -i "s#controller.quorum.voters=.*#controller.quorum.voters=0@cs0.minerva.local:9093,1@cs1.minerva.local:9093,2@cs2.minerva.local:9093#g" controller.properties

sed -i "s#log.dirs=.*#log.dirs=/data/kafka-logs#g" controller.properties

/opt/kafka/bin/kafka-storage.sh format -t ${CLUSTER_UUID} -c /opt/kafka/config/kraft/controller.properties

/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/controller.properties


# Run this on each node, changing the CURRENT_SERVER_INDEX for each node (0,1,2)
# Run this on each node, changing the CURRENT_BROKER_INDEX for each node (4,5,6)
export CURRENT_SERVER_INDEX=1
export CURRENT_BROKER_INDEX=4
export CLUSTER_UUID=dZmpfrGnSaq_XBDWsSsKPg
cd /opt/kafka/config/kraft

sed -i "s#node.id=.*#node.id=${CURRENT_BROKER_INDEX}#g" broker.properties

sed -i "s#controller.quorum.voters=.*#controller.quorum.voters=0@cs0.minerva.local:9093,1@cs1.minerva.local:9093,2@cs2.minerva.local:9093#g" broker.properties

sed -i "s#listeners=.*#listeners=PLAINTEXT://cs${CURRENT_SERVER_INDEX}.minerva.local:9092#g" broker.properties

sed -i "s#log.dirs=.*#log.dirs=/data/kafka-broker#g" broker.properties

/opt/kafka/bin/kafka-storage.sh format -t ${CLUSTER_UUID} -c /opt/kafka/config/kraft/broker.properties

/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/broker.properties


# Run this on any node

/opt/kafka/bin/kafka-topics.sh --bootstrap-server cs0.minerva.local:9092 --create --topic philip_test_topic --partitions 3 --replication-factor 2
/opt/kafka/bin/kafka-topics.sh --bootstrap-server cs0.minerva.local:9092 --list

# Clear logs and start again

/opt/kafka/bin/kafka-server-stop.sh
ps -A | grep kafka

rm -rf /data/kafka-broker/*
rm -rf /data/kafka-logs/*

```
