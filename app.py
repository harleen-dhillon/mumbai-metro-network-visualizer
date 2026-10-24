import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

st.set_page_config(page_title="Mumbai Metro Visualizer", page_icon="🚇", layout="wide")
st.title("🚇 Mumbai Metro Visualizer")
st.caption("Shortest routes • BFS • DFS • Network centrality")

COLORS = {"Line 1": "#E53935", "Line 2A": "#1E88E5", "Line 7": "#43A047"}
LINES = {
    "Line 1": ["Versova", "DN Nagar", "Azad Nagar", "Andheri", "Western Express Highway", "Chakala", "Airport Road", "Marol Naka", "Saki Naka", "Asalpha", "Jagruti Nagar", "Ghatkopar"],
    "Line 2A": ["Dahisar East", "Anand Nagar", "Kandarpada", "Mandapeshwar (IC Colony)", "Eksar", "Borivali West", "Shimpoli", "Kandivali West", "Dahanukarwadi", "Valnai", "Malad West", "Lower Malad", "Bangur Nagar", "Goregaon West", "Oshiwara", "Lower Oshiwara", "Andheri West"],
    "Line 7": ["Gundavali", "Mogra", "Jogeshwari East", "Goregaon East", "Aarey", "Dindoshi", "Kurar", "Akurli", "Poisar", "Magathane", "Devipada", "Rashtriya Udyan", "Ovaripada"]
}
Y = {"Line 1": 14, "Line 2A": 0, "Line 7": -14}
LABELS = {
    "Mandapeshwar (IC Colony)":"Mandapeshwar\n(IC Colony)", "Western Express Highway":"Western Express\nHighway",
    "Dahanukarwadi":"Dahanukar-\nwadi", "Rashtriya Udyan":"Rashtriya\nUdyan", "Jogeshwari East":"Jogeshwari\nEast",
    "Goregaon East":"Goregaon\nEast", "Goregaon West":"Goregaon\nWest", "Borivali West":"Borivali\nWest",
    "Kandivali West":"Kandivali\nWest", "Lower Oshiwara":"Lower\nOshiwara", "Bangur Nagar":"Bangur\nNagar",
    "Dahisar East":"Dahisar\nEast", "Anand Nagar":"Anand\nNagar", "Jagruti Nagar":"Jagruti\nNagar",
    "Marol Naka":"Marol\nNaka", "Saki Naka":"Saki\nNaka", "Airport Road":"Airport\nRoad",
    "Azad Nagar":"Azad\nNagar", "Malad West":"Malad\nWest", "Lower Malad":"Lower\nMalad"
}

@st.cache_data
def read_csv():
    return pd.read_csv("metro_data.csv")

try:
    df = read_csv()
except Exception as e:
    st.error(f"Could not read metro_data.csv: {e}")
    st.info("Keep app.py and metro_data.csv in the same folder.")
    st.stop()

required = {"station", "next_station", "line", "edge_type"}
if not required.issubset(df.columns):
    st.error("metro_data.csv must have columns: station, next_station, line, edge_type")
    st.stop()

G = nx.Graph()
for _, r in df.iterrows():
    G.add_edge(str(r.station).strip(), str(r.next_station).strip(), line=str(r.line).strip(), edge_type=str(r.edge_type).strip())

pos = {}
for line, stations in LINES.items():
    for i, station in enumerate(stations):
        if station in G:
            pos[station] = (i * 5, Y[line])
for i, s in enumerate([s for s in G if s not in pos]):
    pos[s] = (i * 5, -21)
transfer_edges = [(u,v) for u,v,d in G.edges(data=True) if str(d.get("edge_type","")).lower()=="transfer"]
regular_edges = [(u,v) for u,v,d in G.edges(data=True) if str(d.get("edge_type","")).lower()!="transfer"]
transfer_nodes = {s for e in transfer_edges for s in e}
line_membership = {s: line for line, stations in LINES.items() for s in stations}
stations = sorted(G.nodes())

def bfs(start):
    seen, q, order = {start}, [start], []
    while q:
        u = q.pop(0); order.append(u)
        for v in sorted(G.neighbors(u)):
            if v not in seen:
                seen.add(v); q.append(v)
    return order

def dfs(start):
    seen, stack, order = set(), [start], []
    while stack:
        u = stack.pop()
        if u in seen: continue
        seen.add(u); order.append(u)
        for v in sorted(G.neighbors(u), reverse=True):
            if v not in seen: stack.append(v)
    return order

def route_info(route):
    lines, transfers = [], []
    for u,v in zip(route[:-1], route[1:]):
        d = G[u][v]
        if str(d.get("edge_type", "")).lower() == "transfer":
            a, b = line_membership.get(u, "Unknown line"), line_membership.get(v, "Unknown line")
            transfers.append(f"{u} ({a}) → {v} ({b})")
            for line in (a,b):
                if line != "Unknown line" and line not in lines: lines.append(line)
        else:
            line = d.get("line", "")
            if line and line not in lines: lines.append(line)
    return lines, transfers

def draw_map(title, route=None, order=None, source=None, destination=None):
    route, order = route or [], order or []
    route_keys = {frozenset((u,v)) for u,v in zip(route[:-1], route[1:])}
    fig, ax = plt.subplots(figsize=(17, 8))
    for line, color in COLORS.items():
        edges = [(u,v) for u,v in regular_edges if G[u][v].get("line")==line]
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color, width=2.7, ax=ax)
    for u,v in transfer_edges:
        x1,y1=pos[u]; x2,y2=pos[v]
        ax.plot([x1,x2],[y1,y2], color="#AEB4BA", linestyle="--", linewidth=1.2, zorder=1)
    normal_route, transfer_route = [], []
    for u,v in zip(route[:-1], route[1:]):
        (transfer_route if str(G[u][v].get("edge_type","")).lower()=="transfer" else normal_route).append((u,v))
    if normal_route:
        nx.draw_networkx_edges(G,pos,edgelist=normal_route,edge_color="#FF8F00",width=5,ax=ax)
    for u,v in transfer_route:
        x1,y1=pos[u]; x2,y2=pos[v]
        ax.plot([x1,x2],[y1,y2],color="#FF8F00",linestyle="--",linewidth=4,zorder=4)
    visited=set(order)
    nx.draw_networkx_nodes(G,pos,nodelist=[s for s in G if s not in transfer_nodes and s not in visited],node_color="#B3E5FC",node_size=430,edgecolors="#263238",linewidths=1.1,ax=ax)
    nx.draw_networkx_nodes(G,pos,nodelist=[s for s in transfer_nodes if s not in visited],node_color="#FFD54F",node_size=470,edgecolors="#263238",linewidths=1.1,ax=ax)
    if order:
        nx.draw_networkx_nodes(G,pos,nodelist=order,node_color="#CE93D8",node_size=470,edgecolors="#4A148C",linewidths=1.1,ax=ax)
        nx.draw_networkx_labels(G,pos,labels={s:str(i) for i,s in enumerate(order,1)},font_size=7,font_weight="bold",ax=ax)
    if source in G:
        nx.draw_networkx_nodes(G,pos,nodelist=[source],node_color="#00C853",node_size=620,edgecolors="black",linewidths=1.7,ax=ax)
    if destination in G and destination != source:
        nx.draw_networkx_nodes(G,pos,nodelist=[destination],node_color="#AB47BC",node_size=620,edgecolors="black",linewidths=1.7,ax=ax)
    label_pos, label_text = {}, {}
    offsets=[1.9,-1.9,3.0,-3.0]
    for line, names in LINES.items():
        for i,s in enumerate(names):
            if s in pos:
                x,y=pos[s]; label_pos[s]=(x,y+offsets[i%4]); label_text[s]=LABELS.get(s,s)
    nx.draw_networkx_labels(G,label_pos,labels=label_text,font_size=6.3,font_color="#263238",ax=ax)
    legend=[Line2D([0],[0],color=c,lw=3,label=l) for l,c in COLORS.items()]
    legend += [Line2D([0],[0],color="#888",lw=1.5,ls="--",label="Transfer connection"), Line2D([0],[0],color="#FF8F00",lw=4,label="Selected route (dashed transfer)")]
    ax.legend(handles=legend,loc="upper center",bbox_to_anchor=(0.5,-0.06),ncol=5,fontsize=8)
    ax.set_title(title,fontsize=15,fontweight="bold",pad=18); ax.set_axis_off(); ax.margins(x=.04,y=.32)
    fig.tight_layout()
    return fig

with st.sidebar:
    st.header("Plan and explore")
    mode=st.radio("Operation",["Shortest route","BFS traversal","DFS traversal","Network analysis"])
    if mode=="Shortest route":
        source=st.selectbox("Starting station",stations,index=stations.index("Versova") if "Versova" in stations else 0)
        destination=st.selectbox("Destination station",stations,index=stations.index("Andheri West") if "Andheri West" in stations else 0)
    elif mode in ("BFS traversal","DFS traversal"):
        source=st.selectbox("Starting station",stations); destination=None
    else: source=destination=None
    st.caption("Shortest route minimizes edge count, not real travel time.")

m1,m2,m3=st.columns(3)
m1.metric("Stations",G.number_of_nodes()); m2.metric("Connections",G.number_of_edges()); m3.metric("Connected components",nx.number_connected_components(G))

if mode=="Shortest route":
    if source==destination: st.info("Choose two different stations.")
    else:
        try:
            route=nx.shortest_path(G,source,target=destination)
            lines,transfers=route_info(route)
            a,b,c=st.columns(3); a.metric("Stations on route",len(route)); b.metric("Connections",len(route)-1); c.metric("Transfers",len(transfers))
            st.subheader("Route sequence"); st.write(" → ".join(route))
            st.write("**Lines used:** "+(" → ".join(lines) if lines else "Unknown"))
            if transfers:
                st.write("**Transfer details**")
                for t in transfers: st.write("- "+t)
            fig=draw_map(f"Shortest route: {source} → {destination}",route=route,source=source,destination=destination)
            st.pyplot(fig,use_container_width=True); plt.close(fig)
        except nx.NetworkXNoPath: st.error("No route exists between these stations.")
elif mode in ("BFS traversal","DFS traversal"):
    order=bfs(source) if mode=="BFS traversal" else dfs(source)
    st.metric("Stations visited",len(order)); st.subheader("Traversal order"); st.write(" → ".join(order))
    fig=draw_map(f"{mode}: from {source}",order=order,source=source)
    st.pyplot(fig,use_container_width=True); plt.close(fig)
else:
    degree=nx.degree_centrality(G); between=nx.betweenness_centrality(G); close=nx.closeness_centrality(G)
    a,b,c=st.columns(3); a.metric("Density",f"{nx.density(G):.4f}"); b.metric("Average degree",f"{sum(dict(G.degree()).values())/G.number_of_nodes():.2f}"); c.metric("Connected", "Yes" if nx.is_connected(G) else "No")
    table=pd.DataFrame({"Station":list(G.nodes()),"Degree":[G.degree(s) for s in G.nodes()],"Degree centrality":[degree[s] for s in G.nodes()],"Betweenness centrality":[between[s] for s in G.nodes()],"Closeness centrality":[close[s] for s in G.nodes()]})
    st.subheader("Station centrality rankings"); st.dataframe(table.sort_values("Betweenness centrality",ascending=False).head(10),use_container_width=True,hide_index=True)
    top=table.nlargest(10,"Degree centrality").sort_values("Degree centrality")
    fig,ax=plt.subplots(figsize=(10,5)); ax.barh(top.Station,top["Degree centrality"]); ax.set_title("Top 10 stations by degree centrality"); ax.set_xlabel("Degree centrality"); ax.grid(axis="x",alpha=.25); fig.tight_layout()
    st.pyplot(fig,use_container_width=True); plt.close(fig)

with st.expander("Project notes"):
    st.write("This graph models the stations and connections listed in metro_data.csv. It demonstrates shortest-path search, BFS, DFS and centrality. It is a selected-line educational model, not a complete official Mumbai Metro map. Route cost currently means number of edges, not travel time or distance.")
