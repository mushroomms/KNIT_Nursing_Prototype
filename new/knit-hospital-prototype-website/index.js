// mqtt-socketio-bridge
//
// (c) Copyright 2018 MCQN Ltd
//

var mqtt = require('mqtt');
var express = require('express');
var app = express();

const { createServer } = require("https");
const { readFileSync } = require("fs");
const { Server } = require("socket.io");
const MongoClient = require('mongodb').MongoClient;

// Port that the web server should listen on
const PORT = process.env.PORT || 3001;
const clientId = `mqttjs_${Math.random().toString(16).substr(2, 8)}`;

// Enter details of the MQTT broker that you want to interface to
// By default we'll use the public HiveMQ one, so any Arduino clients using
// the PubSubClient library can easily talk to it
const MQTT_BROKER = process.env.MQTT_BROKER || "wss://192.168.223.139:8084/mqtt"
const OPTIONS = {
        username: "username",
        password: "password",
        protocolVersion: 5,
        clientId: clientId,
        rejectUnauthorized: false,
        protocolId: "MQTT",
        reconnectPeriod: 1000,
        connectTimeout: 30 * 1000,
        ca: readFileSync("/home/user/Documents/socketio_crt/ca.crt"),
        cert: readFileSync("/home/user/Documents/socketio_crt/client.crt"),
        key: readFileSync("/home/user/Documents/socketio_crt/client.key")
};

const httpsServer = createServer({
        ca: readFileSync("/etc/mosquitto/certs/ca.crt"),
        key: readFileSync("/etc/mosquitto/certs/server.key"),
        cert: readFileSync("/etc/mosquitto/certs/server.crt")
}, app);

const io = new Server(httpsServer, {
        cors: {
                origin: "*"
        }

});
var client = mqtt.connect(MQTT_BROKER, OPTIONS);

// Connect to MQTT broker
client.on('connect', function () {
        console.log("Connected to " + MQTT_BROKER);
})

// Handle connection errors and attempt reconnection
function handleConnectionError() {
        client.on('error', function (err) {
                console.error("MQTT connection error:", err);

                // Attempt to reconnect after a delay
                setTimeout(function () {
                        console.log("Attempting to reconnect to MQTT broker...");
                        client.reconnect();
                }, 5000);  // 5 seconds delay
        });
}

// Add the error handling function
handleConnectionError();

// We need to cope with wildcards in topics, so can't just do a simple comparison
// This function returns true if they match and false otherwise
// topic1 can include wildcards, topic2 can't
const topicMatch = (topic1, topic2) => {
        const matchStr = topic1.replace(/#/g, '.*');
        return new RegExp(`^${matchStr}$`).test(topic2);
};

// MQTT messages
client.on('message', (topic, payload) => {
        console.log('topic:', topic);
        console.log('payload:', payload.toString());

        // Store MQTT data
        storeMqttData(payload.toString());

        // Efficiently broadcast to matching rooms using `to` and `except`
        io.to(Object.keys(io.sockets.adapter.rooms)
                .filter(room_name => topicMatch(room_name, topic))
        ).emit('mqtt', { topic, payload: payload.toString() });
});

// Socket IO middleware for authentication
io.use((socket, next) => {
        const token = socket.handshake.auth.token;
        console.log("Authenticating [", socket.id, "] Token: [", token, "]");
        next();
});

io.on('connection', (socket) => {
        console.log("New connection from", socket.id);

        // ...subscribe messages
        socket.on('subscribe', async (msg) => {
                try {
                        if (msg.topic) {
                                await socket.join(msg.topic);

                                const hasOtherSubscribers = io.sockets.adapter.rooms.get(msg.topic)?.size > 1; // Check for other subscribers

                                if (!hasOtherSubscribers) {
                                        await client.subscribe(msg.topic);
                                } else {
                                        console.log("Already subscribed to", msg.topic);
                                }

                                console.log("Subscribed to topic:", msg.topic, "(First subscriber:", !hasOtherSubscribers, ")");
                        } else {
                                console.error("Subscription attempt with missing topic.");
                        }
                } catch (error) {
                        console.error("Error handling subscription:", error);
                        // Consider sending an error message back to the user
                }
        });

        // ...publish messages
        socket.on('publish', (msg) => {
                console.log("socket published [", msg.topic, "] >>", msg.payload, "<<");
                client.publish(msg.topic, msg.payload);
        });

        socket.on("connect_error", (err) => {
                console.log(`connect_error due to ${err.message}`);
        });

        // ...and disconnections
        socket.on('disconnect', (reason) => {
                console.log("disconnect from", socket.id);

                // Iterate over keys of client._resubscribeTopics for compatibility
                Object.keys(client._resubscribeTopics).forEach((sub) => {
                        if (!io.sockets.adapter.rooms.get(sub)) {
                                console.log("Unsubscribing from", sub);
                                client.unsubscribe(sub);
                        }
                });
        });

        socket.on('unsub', (msg) => {
                client.unsubscribe(msg.topic);
                console.log("Unsubscribing from", msg.topic);
        })
});

const uri = "mongodb://Admin:password@localhost:27017/"; // Replace with your actual URI

const dbClient = new MongoClient(uri); // Connect to MongoDB and store the client

async function storeMqttData(message) {
        try {
                const mqttMessage = JSON.parse(message);
                const { s, r, bp, sp } = mqttMessage;

                // Define the collection name based on the room number
                const collectionName = `room_${r}`;

                // Connect to the database and get the collection
                const db = dbClient.db("knit_hospital"); // Use the connected client
                const collection = db.collection(collectionName);

                // Create a document to store the data
                const document = {
                        roomNumber: r,
                        status: s,
                        heartRate: bp,
                        spo2: sp,
                        timestamp: Date.now()
                };

                // Insert the document into the collection
                const result = await collection.insertOne(document);
                console.log("Stored MQTT data:", result.insertedId);
        } catch (error) {
                console.error("Error parsing or storing MQTT data:", error);
                // Handle errors appropriately, e.g., log, retry, send error messages
        }
}

// Serve static files from the 'static_files' folder
app.use(express.static('static_files'));

// Set up web server to serve 
app.get('/', function (req, res) {
        res.sendFile(__dirname + "/static_files/mqtt-socket.html");
})

httpsServer.listen(PORT, '0.0.0.0', function () {
        console.log("listening on all interaces on port " + PORT)
})

client.subscribe('hospital/#');
console.log("Subscribed to all topics with wildcard #");

