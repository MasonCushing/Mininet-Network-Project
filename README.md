# Mininet Network Monitoring and QoS Management System

## Overview

The Mininet Network Monitoring and QoS Management System is a Software-Defined Networking (SDN) platform designed to simulate, monitor, analyze, and manage network traffic within a virtual environment.

Built using Mininet, Open vSwitch, Ryu SDN Controller, Flask, SNMP, and Cytoscape.js, the system allows users to visualize network topology, monitor network performance, generate network traffic, test routing algorithms, and apply Quality of Service (QoS) policies through a web-based dashboard.

The project demonstrates modern network management concepts including:

- Network Topology Visualization
- SNMP-Based Monitoring
- Traffic Generation
- Routing Algorithms
- QoS Management
- Performance Analysis
- Rule-Based Network Optimization

---

## Features

### Network Topology Visualization

- Interactive Cytoscape.js topology display
- Dynamic topology generation from Mininet
- Visual representation of:
  - Hosts
  - Switches
  - Routers
- Real-time node selection and inspection

---

### SNMP Monitoring

The monitoring subsystem collects statistics from hosts throughout the simulated network.

Metrics include:

- Bytes Received
- Bytes Sent
- Packets Received
- Packets Sent
- Interface Errors
- Interface Utilization

Statistics are accessible through REST APIs and displayed within the monitoring dashboard.

---

### Network Performance Monitoring

The platform measures:

- Latency
- Packet Loss
- Throughput

Example endpoint:

```http
GET /api/performance
```

Example response:

```json
{
    "latency": 2.8,
    "packet-loss": 0,
    "throughput": 95.2
}
```

---

### Traffic Generation

The system supports multiple traffic profiles:

- Voice
- Video
- Gaming
- Streaming
- Web
- Bulk Transfer
- Random Traffic

Traffic flows are generated using iPerf3.

Each traffic class includes predefined DSCP values to simulate realistic enterprise traffic patterns.

---

### Routing Algorithms

#### Shortest Path Routing

Uses Breadth-First Search (BFS) to determine the route with the fewest hops between source and destination.

#### Least Cost Routing

Uses Dijkstra's Algorithm combined with network statistics to identify the most efficient path based on network conditions.

Example endpoint:

```http
GET /api/route
```

Example response:

```json
{
    "source": "h1",
    "target": "h54",
    "shortest_path": [
        "h1",
        "s4",
        "r1",
        "r2",
        "r3",
        "s12",
        "h54"
    ],
    "least_traffic_path": [
        "h1",
        "s4",
        "r1",
        "r2",
        "r3",
        "s12",
        "h54"
    ]
}
```

---

## Quality of Service (QoS)

The QoS subsystem provides traffic management functionality through multiple scheduling algorithms.

### Traffic Classification

Traffic classes are assigned DSCP values to support differentiated services.

| Traffic Type | DSCP |
|-------------|------|
| Voice | EF |
| Gaming | CS5 |
| Video | AF41 |
| Streaming | AF31 |
| Web | BE |
| Bulk | CS1 |

---

### QoS Scheduling Algorithms

#### 1. Priority Queue (PQ)

Provides strict priority scheduling.

Priority Levels:

- Priority 1
  - Voice
  - Gaming

- Priority 2
  - Video
  - Streaming

- Priority 3
  - Web

- Priority 4
  - Bulk

---

#### 2. Weighted Fair Queuing (WFQ)

Allocates bandwidth according to class weights.

Example allocation:

| Traffic Type | Weight |
|-------------|----------|
| Voice | 40% |
| Gaming | 20% |
| Video | 20% |
| Streaming | 10% |
| Web | 7% |
| Bulk | 3% |

---

#### 3. Weighted Round Robin (WRR)

Provides fair scheduling by allowing each traffic class to transmit according to assigned weights while preventing starvation of lower-priority traffic.

---

## QoS APIs

### Check QoS Status

```http
GET /api/qos/status
```

### View Policy Details

```http
GET /api/qos/policy/<policy>
```

### Apply Policy

```http
POST /api/qos/apply/<policy>
```

### Reset Policy

```http
POST /api/qos/reset
```

### Change Scheduler

```http
POST /api/qos/scheduler/<scheduler>
```

---

## System Architecture

```text
+---------------------+
|     Dashboard       |
+----------+----------+
           |
           v
+---------------------+
|      Flask API      |
+----------+----------+
           |
+----------+----------+----------+
|                     |          |
v                     v          v
Monitoring      Routing      QoS Engine
Subsystem      Algorithms
|                     |          |
+----------+----------+----------+
           |
           v
+---------------------+
|      Mininet        |
+----------+----------+
           |
           v
+---------------------+
|  Ryu Controller     |
+---------------------+
```

---

## Technologies Used

### Networking

- Mininet
- Open vSwitch (OVS)
- Ryu SDN Controller
- SNMP
- Linux Traffic Control (tc)
- iPerf3

### Backend

- Python 3
- Flask

### Frontend

- HTML5
- CSS3
- JavaScript
- Cytoscape.js

### Algorithms

- Breadth-First Search (BFS)
- Dijkstra's Algorithm
- Priority Queuing
- Weighted Fair Queuing
- Weighted Round Robin

---

## Installation

### Prerequisites

The project was developed and tested using:

- VMware Workstation / VMware Player
- Mininet Virtual Machine
- Ubuntu Linux
- Python 3
- Flask
- Ryu SDN Controller
- Git

---

### Environment Setup

#### 1. Install VMware

Download and install one of the following:

- VMware Workstation Pro
- VMware Workstation Player

---

#### 2. Install a Linux Virtual Machine with Mininet

Download the Mininet Virtual Machine from:

https://mininet.org/download/

Import the VM into VMware and verify that Mininet is installed.

You can test Mininet using:

```bash
sudo mn --test pingall
```

Expected output:

```text
*** Ping**testing ping**eachability
*** Results**0% dropped
```

---

**## 3. Start the Virtual Machine

**Launch the Mininet** through VMware and log into the Linux environment.

**-

#### 4. Install Required Softw**e

Update system packages:

```bash
sudo apt update
sudo apt upgrade**``

Install Python and pip:

```bash
sudo apt install python3 python**pip -y**``

Install Flask:

```bash
pip3 **stall flask
```

Install Ryu:

``**bash
pip3 install ryu
```

Install**Perf3:

```bash
sudo apt install **erf3 -y
```

Install Git:

```bash sudo apt install git -y
```

Install Visual Studio Code (optional but recommended):

```bash
sudo snap **stall code --classic
```

---

##** 5. Download the Project

Clone tth repository:

```bash
git clone <**pository-url>
```

Navigate into the project folder:

```bash
cd Mininet-Network-Project
```

---

####**. Open the Project in an IDE

Using Visual Studio Code:

```bash
code.
```

The project should now be open and ready for development.

--**
## Running the System

### Step ** Start the Ryu Controller

Open a terminal and run:

```bash
ryu-manager ryu.app.simple_switch_13
```

Leave this terminal running.

---

**# Step 2: Start the Flask Application

Open a second terminal:

```bash
cd Mininet-Network-Project

sudo mn -c

sudo python3 app.py
```

-**

### Step 3: Open the Dashboard
navigate to:

```text
http://127.0**.1:5000
```

---

### Login Credentials

```text
Username: admin
Pas**ord: 1234
```

---

## Verificati**

Verify the following APIs are operational:

### Topology

```text
http://127.0.0.1:5000/api/topology
**`

### Performance Monitoring

```text
http://127.0.0.1:5000/api/performance
```

### Routing Algorithm**
```text
http://127.0.0.1:5000/app/route
```

### QoS Status

```tex**http://127.0.0.1:5000/api/qos/status
```

A successful response from**hese endpoints indicates that the controller, Mininet topology, moni**ring system, routing algorithms, and QoS subsystem are functioning correctly.
---

## Available API Endpoints

### Topology

```http
GET /api/topology
```

### Node Statistics

```http
GET /api/stats/<node>
```

### Performance Monitoring

```http
GET /api/performance
```

### Routing

```http
GET /api/route
POST /api/route
```

### Traffic Management

```http
POST /api/traffic/custom
POST /api/traffic/random
POST /api/traffic/stop
GET  /api/traffic/active
```

### QoS Management

```http
GET  /api/qos/status
GET  /api/qos/policy/<policy>
POST /api/qos/apply/<policy>
POST /api/qos/reset
POST /api/qos/scheduler/<scheduler>
```

---

## Future Improvements

- Dynamic congestion-aware routing
- Advanced bandwidth shaping
- Historical performance reporting
- Network anomaly detection
- Automated rule-based QoS recommendations
- Enhanced traffic engineering policies
- Real-time scheduler visualization
- Additional QoS algorithms

---

## Project Goals

This project demonstrates:

- Software Defined Networking concepts
- Network performance monitoring
- Routing algorithm implementation
- QoS enforcement techniques
- REST API development
- Real-time network visualization
- Traffic engineering and management

---

## License

This project was developed for educational and research purposes.
