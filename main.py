import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
import networkx as nx
import argparse
import numpy as np

# Argument parser for the input image path
parser = argparse.ArgumentParser(description="Path of the map")
parser.add_argument(
    "file_path",
    type=str,
    nargs="?",
    help="Absolute path of the map"
)

parser.add_argument(
    "--graph_name",
    type=str,
    nargs="?",
    help="Name of the graph"
)

args = parser.parse_args()

if args.file_path is not None:
    image_path = args.file_path
else:
    image_path = "manhattanlargezoom.png"

# Initialize graph variables
nodes = []
edges = []
mode = "Nodes"  # Default mode is creating nodes
current_edge = []
directionality = "None"  # Default edge directionality
show_labels = False  # Default to not showing labels

# Load the image
image = plt.imread(image_path)

def onclick(event):
    global mode, current_edge
    if event.inaxes and event.xdata is not None and event.ydata is not None:
        x, y = event.xdata, event.ydata
        # Prevent accidental (0,0) node creation by ignoring clicks outside the image
        if event.inaxes != ax or abs(x) < 1e-5 and abs(y) < 1e-5:
            return
        if mode == "Nodes":
            # Prevent duplicate nodes
            if not any(abs(node[0] - x) < 1e-5 and abs(node[1] - y) < 1e-5 for node in nodes):
                nodes.append((x, y))
                ax.plot(x, y, 'ro')
        elif mode == "Edges":
            # Find the nearest existing node to connect
            nearest_node_index = find_nearest_node(x, y)
            if nearest_node_index is not None:
                current_edge.append(nearest_node_index)
                nearest_node = nodes[nearest_node_index]
                ax.plot(nearest_node[0], nearest_node[1], 'bo')  # Highlight selected nodes
                if len(current_edge) == 2:
                    edge = tuple(current_edge)
                    if edge[0] != edge[1]:  # Avoid self-loops
                        if directionality == "Directed":
                            edges.append(edge)
                            x_vals = [nodes[edge[0]][0], nodes[edge[1]][0]]
                            y_vals = [nodes[edge[0]][1], nodes[edge[1]][1]]
                            ax.annotate("", xy=(x_vals[1], y_vals[1]), xytext=(x_vals[0], y_vals[0]),
                                        arrowprops=dict(arrowstyle="->", color="green", lw=2))
                        elif directionality == "None":
                            edges.append(edge)
                            x_vals = [nodes[edge[0]][0], nodes[edge[1]][0]]
                            y_vals = [nodes[edge[0]][1], nodes[edge[1]][1]]
                            ax.plot(x_vals, y_vals, 'g-', lw=2)  # Draw undirected edge
                    current_edge.clear()
        fig.canvas.draw()

def find_nearest_node(x, y):
    """Find the nearest node to the given coordinates."""
    threshold = 10
    for i, node in enumerate(nodes):
        if abs(node[0] - x) < threshold and abs(node[1] - y) < threshold:
            return i
    return None

def clear(event):
    global nodes, edges, current_edge
    nodes = []
    edges = []
    current_edge = []
    ax.clear()
    ax.imshow(image)
    fig.canvas.draw()

def delete(event):
    global nodes, edges
    if mode == "Nodes" and nodes:
        nodes.pop()
    elif mode == "Edges" and edges:
        edges.pop()
    redraw()

def redraw():
    """Redraw the graph on the canvas."""
    ax.clear()
    ax.imshow(image)

    # Redraw nodes and edges
    for i, node in enumerate(nodes):
        ax.plot(node[0], node[1], 'ro')
        if show_labels:
            ax.text(node[0], node[1], str(i), fontsize=8, color='blue')

    for edge in edges:
        src_index, dst_index = edge
        src = nodes[src_index]
        dst = nodes[dst_index]
        x_vals = [src[0], dst[0]]
        y_vals = [src[1], dst[1]]
        if directionality == "None":
            ax.plot(x_vals, y_vals, 'g-', lw=2)
        elif directionality == "Directed":
            ax.annotate("", xy=dst, xytext=src,
                        arrowprops=dict(arrowstyle="->", color="green", lw=2))

    fig.canvas.draw()

def toggle_labels(label):
    global show_labels
    show_labels = label == "Show"
    redraw()

def load_graph(event):
    """Load a graph from a GML file."""
    global nodes, edges, directionality
    try:
        # Use the provided graph name or default to "graph_corrected.gml"
        graph_file = args.graph_name if args.graph_name else "graph_corrected.gml"

        # Load the graph
        graph = nx.read_gml(graph_file)

        # Clear existing data
        nodes.clear()
        edges.clear()

        # Extract node positions and attributes
        node_map = {}
        for node, data in graph.nodes(data=True):
            if 'pos' in data and isinstance(data['pos'], (list, tuple)) and len(data['pos']) == 2:
                pos = tuple(map(float, data['pos']))
            else:
                pos = (0, 0)  # Default to (0, 0) if missing or invalid
            node_map[node] = pos
            nodes.append(pos)

        # Determine if the graph is directed
        directionality = "Directed" if graph.is_directed() else "None"

        # Extract edges
        edges.extend([(list(node_map.keys()).index(src), list(node_map.keys()).index(dst))
                      for src, dst in graph.edges])

        redraw()
        print(f"Graph loaded successfully from {graph_file}!")
    except FileNotFoundError:
        print(f"Graph file {graph_file} not found. Please export and try again.")
    except Exception as e:
        print(f"Error parsing graph file: {e}")

def export(event):
    """Export the graph as a NetworkX graph."""
    graph = nx.DiGraph() if directionality != "None" else nx.Graph()
    for i, node in enumerate(nodes):
        graph.add_node(i, pos=node)
    for edge in edges:
        graph.add_edge(edge[0], edge[1])
    nx.write_gml(graph, "graph_corrected.gml")
    print("Graph exported to graph_corrected.gml")

def select_mode(label):
    global mode
    mode = label

def select_directionality(label):
    global directionality
    directionality = label

# Set up the figure and axes
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.3)
ax.imshow(image)

# Add buttons for functionality
ax_clear = plt.axes([0.4, 0.05, 0.1, 0.075])
b_clear = Button(ax_clear, "Clear")
b_clear.on_clicked(clear)

ax_delete = plt.axes([0.51, 0.05, 0.1, 0.075])
b_delete = Button(ax_delete, "Delete")
b_delete.on_clicked(delete)

ax_load = plt.axes([0.62, 0.05, 0.1, 0.075])
b_load = Button(ax_load, "Load Graph")
b_load.on_clicked(load_graph)

ax_export = plt.axes([0.73, 0.05, 0.1, 0.075])
b_export = Button(ax_export, "Export")
b_export.on_clicked(export)

# Add radio buttons for mode selection
ax_mode = plt.axes([0.01, 0.05, 0.15, 0.15])
radio = RadioButtons(ax_mode, ("Nodes", "Edges"))
radio.on_clicked(select_mode)

# Add radio buttons for edge directionality
ax_directionality = plt.axes([0.17, 0.05, 0.3, 0.15])
radio_dir = RadioButtons(ax_directionality, ("None", "Directed"))
radio_dir.on_clicked(select_directionality)

# Add radio buttons for toggling node labels
ax_labels = plt.axes([0.05, 0.25, 0.2, 0.15])
radio_labels = RadioButtons(ax_labels, ("Hide", "Show"))
radio_labels.on_clicked(toggle_labels)

fig.canvas.mpl_connect("button_press_event", onclick)

plt.show()