import React, { useState, useEffect, useRef } from "react";
import * as Realm from "realm-web";
import "./styles.css";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Navbar from "react-bootstrap/Navbar";

import { Line } from "react-chartjs-2";

// Inputted Room
var room = "NA";

// BP Chart options
const BP_Chart_Options = {
  legend: {
    display: false,
  },
  maintainAspectRatio: false,
  animation: {
    duration: 0,
  },
  scales: {
    xAxes: [{ display: false }],
    yAxes: [
      {
        ticks: {
          beginAtZero: false,
          max: 200,
          min: 0,
        },
      },
    ],
  },
};

// SPO2 Chart options
const SPO2_Chart_Options = {
  legend: {
    display: false,
  },
  maintainAspectRatio: false,
  animation: {
    duration: 0,
  },
  scales: {
    xAxes: [{ display: false }],
    yAxes: [
      {
        display: true,
        ticks: {
          beginAtZero: false,
          max: 100,
          min: 0,
        },
      },
    ],
  },
};

// Create the Application
const app = new Realm.App({ id: "knit-nurse-app-hghfw" });

const App = () => {
  // Set state variables
  const [user, setUser] = useState();
  const [events, setEvents] = useState([]);
  const [bp, setBP] = useState("NA");
  const [spo2, setSpo2] = useState("NA");
  const [bpvalid, setBPValid] = useState(1);
  const [spo2valid, setSpo2Valid] = useState(1);
  const [BP_Array, setBP_Array] = useState([]);
  const [SPO2_Array, setSPO2_Array] = useState([]);
  const linechart = useRef();
  const roomRef = useRef(null);

  // Handle room number input
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Set room number
    if (roomRef.current.value.trim() > 0) {
      room = roomRef.current.value.trim();
    } else {
      room = 1;
    }

    // Reset
    setBP_Array([]);
    setSPO2_Array([]);
  };

  useEffect(() => {
    const login = async () => {
      // Authenticate anonymously
      const user = await app.logIn(Realm.Credentials.anonymous());
      setUser(user); // Connect to the database

      const mongodb = app.currentUser.mongoClient("mongodb-atlas");
      // Everytime a change happens in the stream, add it to the list of events
      const collection = mongodb.db("data").collection("changestream"); 

      for await (const change of collection.watch([{}])) {
        try {
          // Check if there was a documente inserted into MongoDB
          if (change.operationType == "insert") {
            // Check if room value in document equals the current room value inputted
            if (change.fullDocument.room == room) {
              setEvents((events) => [...events, change]);
              // Assign BP and SPO2 readings to variables
              setBP(change.fullDocument.bp);
              setSpo2(change.fullDocument.spo2);
              setBPValid(parseInt(change.fullDocument.bpvalid));
              setSpo2Valid(parseInt(change.fullDocument.spo2valid));

              // If length of BP_Array is equal to 10, remove the first element
              if (BP_Array.length == 10) {
                setBP_Array((oldArray) => oldArray.slice(1));
              }
              // If length of SPO2_Array is equal to 10, remove the first element
              if (SPO2_Array.length == 10) {
                setSPO2_Array((oldArray) => oldArray.slice(1));
              }

              // Add new BP and SPO2 readings to arrays
              setBP_Array((oldArray) => [...oldArray, change.fullDocument.bp]);
              setSPO2_Array((oldArray) => [
                ...oldArray,
                change.fullDocument.spo2,
              ]);
            }
          }
        } catch (e) {
          console.error(e);
        }
      }
    };
    login();
  }, []);

  // Return the JSX that will generate HTML for the page
  return (
    <div className="App">
      {/* Navbar */}
      <Navbar bg="light" expand="lg" sticky="top">
        <Container fluid>
          <Navbar.Brand href="#">KNIT Patient Monitor</Navbar.Brand>
          <Form className="d-flex" onSubmit={handleSubmit}>
            <Form.Group
              as={Row}
              // className="mb-3"
              controlId="formPlaintextEmail"
            >
              <Form.Label column sm="2">
                Room:
              </Form.Label>
              <Col column sm="6">
                <Form.Control
                  type="number"
                  placeholder="Room No."
                  className="me-2"
                  aria-label="Search"
                  ref={roomRef}
                />
              </Col>
            </Form.Group>
          </Form>
        </Container>
      </Navbar>
      {/* BP & SPO2 Charts */}
      <Container
        className="d-flex align-items-center"
        fluid
        style={{ height: "90vh", paddingRight: "15px", paddingLeft: "15px" }}
      >
        <Container fluid>
          {/* Display current room number inputted */}
          <Row>
            <Col className="d-flex align-items-center justify-content-center">
              <Col sm={1}></Col>
              <Col className="d-flex justify-content-start">
                <h1>Room: {room}</h1>
              </Col>
            </Col>
            <Col sm={8}></Col>
          </Row>

          <Row className="row mt-5">
            {/* Display BP Readings */}
            <Col className="d-flex align-items-center justify-content-center">
              <Col sm={1}></Col>
              <Col className="d-flex align-items-center">
                <h1>BP: {bp}</h1>
                {bpvalid === 0 && (
                  <p style={{ color: "red" }}>Error in reading</p>
                )}
              </Col>
            </Col>
            {/* Display BP Chart*/}
            <Col sm={8}>
              <Line
                data={{
                  labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                  datasets: [
                    {
                      label: "BP",
                      data: BP_Array,
                      fill: false,
                      lineTension: 0,
                      backgroundColor: "rgba(75,192,192,0.2)",
                      borderColor: "rgba(75,192,192,1)",
                    },
                  ],
                }}
                options={BP_Chart_Options}
                height={200}
                width={10}
                ref={linechart}
              />
            </Col>
          </Row>
          {/* Display SPO2 Readings */}
          <Row className="row mt-5">
            <Col className="d-flex align-items-center justify-content-center">
              <Col sm={1}></Col>
              <Col className="d-flex align-items-center">
                <h1>O2: {spo2}</h1>
                {spo2valid === 0 && (
                  <p style={{ color: "red" }}>Error in reading</p>
                )}
              </Col>
            </Col>
            {/* Display SPO2 Chart */}
            <Col sm={8}>
              <Line
                data={{
                  labels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                  datasets: [
                    {
                      label: "SPO2",
                      data: SPO2_Array,
                      fill: false,
                      lineTension: 0,
                      backgroundColor: "rgba(75,192,192,0.2)",
                      borderColor: "rgba(75,192,192,1)",
                    },
                  ],
                }}
                options={SPO2_Chart_Options}
                height={200}
                width={10}
                ref={linechart}
              />
            </Col>
          </Row>
        </Container>
      </Container>
    </div>
  );
};

export default App;
