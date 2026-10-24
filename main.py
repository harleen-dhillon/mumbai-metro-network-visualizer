import textwrap
from collections import deque

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# =========================================================
# 1. LOAD DATA
# =========================================================

df = pd.read_csv("metro_data.csv")

required_columns = {"station", "next_station", "line", "edge_type"}
if not required_columns.issubset(df.columns):
    raise ValueError(
        "metro_data.csv must contain: station, next_station, line, edge_type"
    )

G = nx.Graph()

for _, row in df.iterrows():
    station = str(row["station"]).strip()
    next_station = str(row["next_station"]).strip()
    line = str(row["line"]).strip()
    edge_type = str(row["edge_type"]).strip()

    G.add_edge(
        station,
        next_station,
        line=line,
        edge_type=edge_type
    )

print("\n========== MUMBAI METRO VISUALIZER ==========")
print("Total stations:", G.number_of_nodes())
print("Total connections:", G.number_of_edges())
print("Network connected:", nx.is_connected(G))

# =========================================================
# 2. LINE COLORS AND STATION ORDER
# =========================================================

line_colors = {
    "Line 1": "#E53935",
    "Line 2A": "#1E88E5",
    "Line 7": "#43A047"
}

line_stations = {
    "Line 1": [
        "Versova", "DN Nagar", "Azad Nagar", "Andheri",
        "Western Express Highway", "Chakala", "Airport Road",
        "Marol Naka", "Saki Naka", "Asalpha",
        "Jagruti Nagar", "Ghatkopar"
    ],
    "Line 2A": [
        "Dahisar East", "Anand Nagar", "Kandarpada",
        "Mandapeshwar (IC Colony)", "Eksar", "Borivali West",
        "Shimpoli", "Kandivali West", "Dahanukarwadi",
        "Valnai", "Malad West", "Lower Malad", "Bangur Nagar",
        "Goregaon West", "Oshiwara", "Lower Oshiwara",
        "Andheri West"
    ],
    "Line 7": [
        "Gundavali", "Mogra", "Jogeshwari East",
        "Goregaon East", "Aarey", "Dindoshi", "Kurar",
        "Akurli", "Poisar", "Magathane", "Devipada",
        "Rashtriya Udyan", "Ovaripada"
    ]
}

# =========================================================
# 3. BUILD WIDE HORIZONTAL LAYOUT
# =========================================================

pos = {}

line_y = {
    "Line 1": 14,
    "Line 2A": 0,
    "Line 7": -14
}

station_spacing = 5.0

for line, stations in line_stations.items():
    for index, station in enumerate(stations):
        if station in G:
            pos[station] = (index * station_spacing, line_y[line])

unplaced = [station for station in G.nodes if station not in pos]

if unplaced:
    print("\nStations not listed in layout:", unplaced)
    for index, station in enumerate(unplaced):
        pos[station] = (index * station_spacing, -20)

# =========================================================
# 4. CONNECTION TYPES AND LOOKUP
# =========================================================

transfer_edges = []
regular_edges = []

for u, v, data in G.edges(data=True):
    if data["edge_type"].casefold() == "transfer":
        transfer_edges.append((u, v))
    else:
        regular_edges.append((u, v))

transfer_stations = {
    station
    for edge in transfer_edges
    for station in edge
}

normal_stations = [
    station for station in G.nodes
    if station not in transfer_stations
]

station_lookup = {
    station.casefold(): station
    for station in G.nodes
}

def get_route_details(route, graph):
    """Return the metro lines used and clearly identify transfer endpoints.

    Transfer rows in metro_data.csv connect two stations belonging to different
    metro lines. The line name on such an edge is "Interchange", so determine
    the actual lines from the stations' membership in line_stations.
    """
    station_lines = {}
    for metro_line, stations in line_stations.items():
        for station in stations:
            station_lines.setdefault(station, []).append(metro_line)

    lines_used = []
    transfers = []

    for u, v in zip(route[:-1], route[1:]):
        edge = graph[u][v]
        edge_type = str(edge.get("edge_type", "")).strip().casefold()
        line = str(edge.get("line", "")).strip()

        if edge_type == "transfer" or line.casefold() == "interchange":
            from_lines = station_lines.get(u, [])
            to_lines = station_lines.get(v, [])
            from_line = from_lines[0] if from_lines else "line unknown"
            to_line = to_lines[0] if to_lines else "line unknown"

            description = f"{u} ({from_line}) → {v} ({to_line})"
            transfers.append(description)

            for actual_line in (from_line, to_line):
                if actual_line != "line unknown" and actual_line not in lines_used:
                    lines_used.append(actual_line)
        elif line and line not in lines_used:
            lines_used.append(line)

    return lines_used, transfers

# Wrap long labels onto multiple lines.
def format_station_name(station):
    replacements = {
        "Mandapeshwar (IC Colony)": "Mandapeshwar\n(IC Colony)",
        "Western Express Highway": "Western Express\nHighway",
        "Dahanukarwadi": "Dahanukar-\nwadi",
        "Rashtriya Udyan": "Rashtriya\nUdyan",
        "Jogeshwari East": "Jogeshwari\nEast",
        "Goregaon East": "Goregaon\nEast",
        "Goregaon West": "Goregaon\nWest",
        "Borivali West": "Borivali\nWest",
        "Kandivali West": "Kandivali\nWest",
        "Lower Oshiwara": "Lower\nOshiwara",
        "Bangur Nagar": "Bangur\nNagar",
        "Dahisar East": "Dahisar\nEast",
        "Anand Nagar": "Anand\nNagar",
        "Jagruti Nagar": "Jagruti\nNagar",
        "Marol Naka": "Marol\nNaka",
        "Saki Naka": "Saki\nNaka",
        "Airport Road": "Airport\nRoad",
        "Azad Nagar": "Azad\nNagar",
        "Malad West": "Malad\nWest",
        "Lower Malad": "Lower\nMalad"
    }

    return replacements.get(station, station)

# =========================================================
# 5. BFS
# =========================================================

def bfs_traversal(graph, start):
    visited = {start}
    queue = deque([start])
    order = []

    while queue:
        current = queue.popleft()
        order.append(current)

        for neighbor in sorted(graph.neighbors(current)):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return order

# =========================================================
# 6. DFS
# =========================================================

def dfs_traversal(graph, start):
    visited = set()
    stack = [start]
    order = []

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)
        order.append(current)

        for neighbor in sorted(
            graph.neighbors(current), reverse=True
        ):
            if neighbor not in visited:
                stack.append(neighbor)

    return order

# =========================================================
# 7. DRAW METRO GRAPH
# =========================================================

def draw_metro_graph(
    ax,
    title,
    traversal_order=None,
    route_edges=None,
    source=None,
    destination=None,
    show_station_labels=True
):
    traversal_order = traversal_order or []
    route_edges = route_edges or []
    highlighted = set(traversal_order)

    # Draw each regular metro line.
    for line, color in line_colors.items():
        edges = [
            (u, v)
            for u, v in regular_edges
            if G[u][v]["line"] == line
        ]

        nx.draw_networkx_edges(
            G, pos,
            edgelist=edges,
            edge_color=color,
            width=3,
            ax=ax
        )

    # Draw dashed transfer connections.
    for u, v in transfer_edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]

        ax.plot(
            [x1, x2],
            [y1, y2],
            color="#AEB4BA",
            linestyle="--",
            linewidth=0.95,
            alpha=0.48,
            zorder=1
        )

    # Highlight regular route segments in solid orange. Highlight transfer
    # connections as dashed orange so the diagram preserves their meaning.
    if route_edges:
        regular_route_edges = [
            (u, v) for u, v in route_edges
            if str(G[u][v].get("edge_type", "")).strip().casefold() != "transfer"
        ]
        transfer_route_edges = [
            (u, v) for u, v in route_edges
            if str(G[u][v].get("edge_type", "")).strip().casefold() == "transfer"
        ]

        if regular_route_edges:
            nx.draw_networkx_edges(
                G, pos,
                edgelist=regular_route_edges,
                edge_color="#FF8F00",
                width=5.5,
                ax=ax
            )

        if transfer_route_edges:
            nx.draw_networkx_edges(
                G, pos,
                edgelist=transfer_route_edges,
                edge_color="#FF8F00",
                style="dashed",
                width=3.5,
                ax=ax
            )

    remaining_normal = [
        s for s in normal_stations if s not in highlighted
    ]

    remaining_transfers = [
        s for s in transfer_stations if s not in highlighted
    ]

    nx.draw_networkx_nodes(
        G, pos,
        nodelist=remaining_normal,
        node_color="#B3E5FC",
        node_size=500,
        edgecolors="#263238",
        linewidths=1.2,
        ax=ax
    )

    nx.draw_networkx_nodes(
        G, pos,
        nodelist=remaining_transfers,
        node_color="#FFD54F",
        node_size=570,
        edgecolors="#263238",
        linewidths=1.4,
        ax=ax
    )

    if traversal_order:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=traversal_order,
            node_color="#CE93D8",
            node_size=570,
            edgecolors="#4A148C",
            linewidths=1.4,
            ax=ax
        )

    # Mark route start and destination.
    if source is not None and not traversal_order:
        if source == destination:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=[source],
                node_color="#00C853",
                node_size=780,
                edgecolors="black",
                linewidths=2,
                ax=ax
            )
        else:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=[source],
                node_color="#00C853",
                node_size=760,
                edgecolors="black",
                linewidths=2,
                ax=ax
            )

            if destination is not None:
                nx.draw_networkx_nodes(
                    G, pos,
                    nodelist=[destination],
                    node_color="#AB47BC",
                    node_size=760,
                    edgecolors="black",
                    linewidths=2,
                    ax=ax
                )

    # Station names are optional. In the side-by-side comparison, names are
    # shown only on the BFS panel; the DFS panel uses the exact same positions
    # and keeps the visit numbers, reducing duplicated text and clutter.
    if show_station_labels:
        label_positions = {}
        label_text = {}
        offsets = [2.0, -2.0, 4.0, -4.0]

        for line, stations in line_stations.items():
            y = line_y[line]

            for index, station in enumerate(stations):
                if station not in pos:
                    continue

                x, _ = pos[station]
                label_positions[station] = (
                    x, y + offsets[index % len(offsets)]
                )
                label_text[station] = format_station_name(station)

        for station in unplaced:
            x, y = pos[station]
            label_positions[station] = (x, y + 2.0)
            label_text[station] = format_station_name(station)

        nx.draw_networkx_labels(
            G, label_positions,
            labels=label_text,
            font_size=6.2,
            font_color="#263238",
            font_weight="medium",
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.92,
                "pad": 1.4
            },
            ax=ax
        )

    # Visit numbers go inside station circles.
    if traversal_order:
        visit_numbers = {
            station: str(index)
            for index, station in enumerate(traversal_order, start=1)
        }

        nx.draw_networkx_labels(
            G, pos,
            labels=visit_numbers,
            font_size=7,
            font_color="black",
            font_weight="bold",
            ax=ax
        )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=18)
    ax.set_axis_off()
    ax.margins(x=0.035, y=0.30)

# =========================================================
# 8. LEGEND
# =========================================================

def make_legend_items(include_route=False, include_traversal=False):
    items = [
        Line2D(
            [0], [0],
            color=color,
            linewidth=3,
            label=line
        )
        for line, color in line_colors.items()
    ]

    items.append(
        Line2D(
            [0], [0],
            color="#858585",
            linestyle="--",
            linewidth=2,
            label="Transfer connection"
        )
    )

    if include_route:
        items.append(
            Line2D(
                [0], [0],
                color="#FF8F00",
                linewidth=5,
                label="Selected route (solid = metro, dashed = transfer)"
            )
        )

    if include_traversal:
        items.append(
            Line2D(
                [0], [0],
                marker="o",
                color="white",
                markerfacecolor="#CE93D8",
                markeredgecolor="#4A148C",
                markersize=9,
                label="Visited station (number = order)"
            )
        )

    items.extend([
        Line2D(
            [0], [0],
            marker="o",
            color="white",
            markerfacecolor="#00C853",
            markeredgecolor="black",
            markersize=9,
            label="Starting station"
        ),
        Line2D(
            [0], [0],
            marker="o",
            color="white",
            markerfacecolor="#AB47BC",
            markeredgecolor="black",
            markersize=9,
            label="Destination"
        ),
        Line2D(
            [0], [0],
            marker="o",
            color="white",
            markerfacecolor="#FFD54F",
            markeredgecolor="#263238",
            markersize=8,
            label="Transfer endpoint"
        ),
        Line2D(
            [0], [0],
            marker="o",
            color="white",
            markerfacecolor="#B3E5FC",
            markeredgecolor="#263238",
            markersize=8,
            label="Metro station"
        )
    ])

    return items

# =========================================================
# 9. MENU
# =========================================================

print("\n========== MENU ==========")
print("1. Find shortest route")
print("2. BFS traversal")
print("3. DFS traversal")
print("4. Compare BFS and DFS side-by-side")
print("5. Network analysis and important stations")

choice = input("\nChoose an option (1/2/3/4): ").strip()

source = None
destination = None
route = []
route_edges = []
traversal_order = []
operation_title = "MUMBAI METRO NETWORK"

# OPTION 1: SHORTEST ROUTE
if choice == "1":
    start_input = input("Enter starting station: ").strip()
    end_input = input("Enter destination station: ").strip()

    source = station_lookup.get(start_input.casefold())
    destination = station_lookup.get(end_input.casefold())

    if source is None:
        print("Starting station not found:", start_input)

    elif destination is None:
        print("Destination station not found:", end_input)

    else:
        try:
            route = nx.shortest_path(
                G, source=source, target=destination
            )
            route_edges = list(zip(route[:-1], route[1:]))

            print("\n========== SHORTEST ROUTE ==========")
            for index, station in enumerate(route, start=1):
                print(f"{index}. {station}")

            total_connections = len(route) - 1
            total_stations = len(route)

            # Explain which metro lines are used and where transfer edges occur.
            lines_used, transfer_details = get_route_details(route, G)
            transfer_count = len(transfer_details)

            print("\nTotal connections:", total_connections)
            print("Total stations:", total_stations)
            print("Transfers:", transfer_count)
            print(
                "Metro lines used:",
                " -> ".join(lines_used) if lines_used else "Not available"
            )

            if transfer_details:
                print("\nTransfer details:")
                for index, detail in enumerate(transfer_details, start=1):
                    print(f"{index}. {detail}")
            else:
                print("\nNo transfer connections required.")

            print("\nRoute summary:")
            print(" -> ".join(route))
            operation_title = f"SHORTEST ROUTE: {source} TO {destination}"

        except nx.NetworkXNoPath:
            print("No route exists between these stations.")

# OPTION 2: BFS
elif choice == "2":
    start_input = input("Enter BFS starting station: ").strip()
    source = station_lookup.get(start_input.casefold())

    if source is None:
        print("Station not found:", start_input)
    else:
        traversal_order = bfs_traversal(G, source)

        print("\n========== BFS TRAVERSAL ==========")
        for index, station in enumerate(traversal_order, start=1):
            print(f"{index}. {station}")

        print("\nStations visited:", len(traversal_order))
        operation_title = f"BFS TRAVERSAL FROM {source}"

# OPTION 3: DFS
elif choice == "3":
    start_input = input("Enter DFS starting station: ").strip()
    source = station_lookup.get(start_input.casefold())

    if source is None:
        print("Station not found:", start_input)
    else:
        traversal_order = dfs_traversal(G, source)

        print("\n========== DFS TRAVERSAL ==========")
        for index, station in enumerate(traversal_order, start=1):
            print(f"{index}. {station}")

        print("\nStations visited:", len(traversal_order))
        operation_title = f"DFS TRAVERSAL FROM {source}"

# OPTION 4: SIDE-BY-SIDE COMPARISON
elif choice == "4":
    start_input = input(
        "Enter starting station for comparison: "
    ).strip()

    source = station_lookup.get(start_input.casefold())

    if source is None:
        print("Station not found:", start_input)
    else:
        bfs_order = bfs_traversal(G, source)
        dfs_order = dfs_traversal(G, source)

        print("\n========== BFS VS DFS COMPARISON ==========")
        print("Starting station:", source)
        print("Total graph stations:", G.number_of_nodes())
        print("Total graph connections:", G.number_of_edges())
        print("BFS stations visited:", len(bfs_order))
        print("DFS stations visited:", len(dfs_order))
        print("BFS time complexity: O(V + E)")
        print("DFS time complexity: O(V + E)")
        print("BFS auxiliary space: O(V)")
        print("DFS auxiliary space: O(V)")

        with open(
            "bfs_dfs_comparison.txt", "w", encoding="utf-8"
        ) as file:
            file.write("MUMBAI METRO: BFS VS DFS COMPARISON\n")
            file.write("=" * 44 + "\n\n")
            file.write(f"Starting station: {source}\n")
            file.write(f"Total stations: {G.number_of_nodes()}\n")
            file.write(f"Total connections: {G.number_of_edges()}\n\n")

            file.write("BFS TRAVERSAL ORDER\n")
            for index, station in enumerate(bfs_order, start=1):
                file.write(f"{index}. {station}\n")

            file.write("\nDFS TRAVERSAL ORDER\n")
            for index, station in enumerate(dfs_order, start=1):
                file.write(f"{index}. {station}\n")

            file.write("\nBFS time complexity: O(V + E)\n")
            file.write("DFS time complexity: O(V + E)\n")
            file.write("BFS auxiliary space: O(V)\n")
            file.write("DFS auxiliary space: O(V)\n")

        print("\nSaved: bfs_dfs_comparison.txt")

        # Side-by-side comparison: both panels show station names and use
        # identical station coordinates, while a separated legend avoids overlap.
        fig, axes = plt.subplots(1, 2, figsize=(40, 17), constrained_layout=False)
        fig.patch.set_facecolor("white")

        fig.suptitle(
            f"BFS vs DFS: Traversal from {source}",
            fontsize=21,
            fontweight="bold",
            y=0.975
        )
        fig.text(
            0.5, 0.942,
            f"{G.number_of_nodes()} stations  •  {G.number_of_edges()} connections  •  "
            "Numbers inside circles show visit order",
            ha="center", va="center", fontsize=11, color="#555555"
        )

        draw_metro_graph(
            axes[0],
            "BFS — Breadth-First Search",
            traversal_order=bfs_order,
            show_station_labels=True
        )

        draw_metro_graph(
            axes[1],
            "DFS — Depth-First Search",
            traversal_order=dfs_order,
            show_station_labels=True
        )

        fig.legend(
            handles=make_legend_items(include_traversal=True),
            loc="lower center",
            ncol=4,
            fontsize=9,
            frameon=True,
            fancybox=True,
            framealpha=0.95,
            bbox_to_anchor=(0.5, 0.015)
        )

        fig.subplots_adjust(
            left=0.025,
            right=0.985,
            top=0.87,
            bottom=0.17,
            wspace=0.08
        )

        fig.savefig(
            "mumbai_metro_comparison.png",
            dpi=300,
            bbox_inches="tight",
            facecolor="white"
        )

        print("Saved: mumbai_metro_comparison.png")
        plt.show()
        raise SystemExit


elif choice == "5":
    print("\n========== NETWORK ANALYSIS ==========")

    # Basic network statistics
    total_stations = G.number_of_nodes()
    total_connections = G.number_of_edges()
    degrees = dict(G.degree())
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)

    average_degree = (
        sum(degrees.values()) / total_stations
        if total_stations else 0
    )

    print("Total stations:", total_stations)
    print("Total connections:", total_connections)
    print("Network density:", round(nx.density(G), 4))
    print("Average degree:", round(average_degree, 2))
    print("Connected components:", nx.number_connected_components(G))
    print("Network connected:", nx.is_connected(G))

    # Rank stations by degree centrality
    ranked_stations = sorted(
        degree_centrality.items(),
        key=lambda item: (-item[1], item[0])
    )

    print("\nTOP 10 STATIONS BY DEGREE CENTRALITY")
    print("-" * 65)
    print(f"{'Station':<30} {'Degree':>8} {'Centrality':>12}")
    print("-" * 65)

    for station, centrality in ranked_stations[:10]:
        print(
            f"{station:<30} "
            f"{degrees[station]:>8} "
            f"{centrality:>12.4f}"
        )

    # Show stations with the highest betweenness centrality
    print("\nTOP 5 STATIONS BY BETWEENNESS CENTRALITY")

    ranked_betweenness = sorted(
        betweenness_centrality.items(),
        key=lambda item: (-item[1], item[0])
    )

    for station, score in ranked_betweenness[:5]:
        print(f"{station}: {score:.4f}")

    # Plot the 10 most connected stations
    top_stations = ranked_stations[:10]
    names = [item[0] for item in top_stations]
    scores = [item[1] for item in top_stations]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.barh(names[::-1], scores[::-1])
    ax.set_title(
        "Mumbai Metro: Top 10 Stations by Degree Centrality",
        fontsize=14,
        fontweight="bold"
    )
    ax.set_xlabel("Degree Centrality")
    ax.set_ylabel("Station")
    ax.grid(axis="x", alpha=0.25)

    fig.tight_layout()
    fig.savefig(
        "network_analysis.png",
        dpi=300,
        bbox_inches="tight"
    )

    print("\nSaved: network_analysis.png")
    plt.show()
    raise SystemExit

else:
    print("Invalid option. Please choose a number from 1 to 5.")


# =========================================================
# 10. SINGLE GRAPH FOR OPTIONS 1, 2 AND 3
# =========================================================

fig, ax = plt.subplots(figsize=(30, 18))
fig.patch.set_facecolor("white")

draw_metro_graph(
    ax,
    operation_title,
    traversal_order=traversal_order,
    route_edges=route_edges,
    source=source,
    destination=destination
)

# Add route statistics directly to the exported figure.
if route:
    lines_used, transfer_details = get_route_details(route, G)
    transfer_count = len(transfer_details)

    route_summary = (
        f"Stations: {len(route)}    |    Connections: {len(route) - 1}    |    "
        f"Transfers: {transfer_count}    |    Lines: "
        f"{' → '.join(lines_used) if lines_used else 'N/A'}"
    )
    fig.text(
        0.5, 0.035, route_summary,
        ha="center", va="center", fontsize=11, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFF3E0",
                  edgecolor="#FF8F00", alpha=0.98)
    )

ax.legend(
    handles=make_legend_items(
        include_route=bool(route_edges),
        include_traversal=bool(traversal_order)
    ),
    loc="upper center",
    bbox_to_anchor=(0.5, -0.055),
    ncol=3,
    fontsize=9,
    frameon=True,
    fancybox=True
)


fig.subplots_adjust(
    left=0.04,
    right=0.96,
    top=0.88,
    bottom=0.23 if route else 0.12
)

fig.savefig(
    "mumbai_metro_graph.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)
print("\nSaved: mumbai_metro_graph.png")

if route:
    fig.savefig(
        "mumbai_metro_route.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white"
    )
    print("Saved: mumbai_metro_route.png")

if traversal_order:
    fig.savefig(
        "mumbai_metro_traversal.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white"
    )
    print("Saved: mumbai_metro_traversal.png")

plt.show()