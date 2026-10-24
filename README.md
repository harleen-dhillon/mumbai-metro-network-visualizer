# Mumbai Metro Network Visualizer

A graph visualization project that models selected Mumbai Metro corridors using Python, NetworkX, Matplotlib, and Streamlit. It demonstrates fundamental graph algorithms through interactive route planning and network analysis.

## Features

- **Shortest Path Finder:** Finds a route between two stations using NetworkX shortest-path algorithms.
- **BFS Traversal:** Visualizes Breadth-First Search and the order in which stations are visited.
- **DFS Traversal:** Demonstrates Depth-First Search across the metro network.
- **BFS vs DFS Comparison:** Compares traversal orders side by side.
- **Network Analysis:** Examines degree, betweenness, and closeness centrality to identify structurally important stations.
- **Interactive Interface:** Uses Streamlit for station selection and visualization.

## Network Coverage

The dataset models three metro corridors:

- Mumbai Metro Line 1
- Mumbai Metro Line 2A
- Mumbai Metro Line 7

The current dataset contains 42 stations and 42 connections, including regular links and transfer connections.

**Note:** This is a selected-corridor academic model, not a complete representation of the entire Mumbai Metro network. Routes are calculated using the connections in the supplied dataset and do not represent real-world travel times.

## Technologies

- Python
- NetworkX
- Pandas
- Matplotlib
- Streamlit
- Graph Theory and Data Structures

## Run Locally

Clone the repository:

```bash
git clone https://github.com/harleen-dhillon/mumbai-metro-network-visualizer.git
cd mumbai-metro-network-visualizer
```

Create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas networkx matplotlib streamlit
```

Launch the application:

```bash
streamlit run app.py
```

## Visualizations

The project generates visualizations for:

- Metro network structure
- Shortest-route highlighting
- BFS and DFS traversal comparison
- Network centrality analysis

## Learning Objectives

- Represent a transport network as a graph.
- Apply BFS, DFS, and shortest-path algorithms.
- Analyze network connectivity and station centrality.
- Communicate algorithmic results through graph visualizations and an interactive interface.

