import json
import plotly.graph_objects as go
import streamlit as st
from api import run_algorithm

st.set_page_config(
    page_title="Optimasi Truck Peti Kemas",
    layout="wide",
)

st.markdown(
    """
    <style>
        [data-testid="stToolbar"] {
            display: none !important;
        }

        [data-testid="stDecoration"] {
            display: none !important;
        }

        #MainMenu {
            visibility: hidden;
        }

        header {
            visibility: hidden;
            height: 0;
        }

        footer {
            visibility: hidden;
        }

        .block-container {
            max-width: 1150px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .stButton > button {
            background-color: #444444 !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
        }

        .stButton > button:hover {
            background-color: #333333 !important;
            color: white !important;
        }

        :root {
            --primary-color: #444444;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

def oriented_dimensions(package, orientation):
    dims = package["dimensions"]
    axes = { "x": dims["w"], "y": dims["l"], "z": dims["h"] }

    return (
        axes[orientation["w"]], axes[orientation["l"]], axes[orientation["h"]],
    )

def add_cuboid(fig, x, y, z, w, l, h, name, hover_text, ):
    vx = [
        x, x + w, x + w, x,
        x, x + w, x + w, x,
    ]
    vy = [
        y, y, y + l, y + l,
        y, y, y + l, y + l,
    ]
    vz = [
        z, z, z, z,
        z + h, z + h, z + h, z + h,
    ]
    fig.add_trace(
        go.Mesh3d(x=vx, y=vy, z=vz,
            i=[
                0, 0, 0, 1,
                1, 2, 3, 4,
                4, 5, 6, 3,
            ],
            j=[
                1, 2, 4, 2,
                5, 3, 2, 5,
                5, 6, 7, 7,
            ],
            k=[
                2, 3, 5, 5,
                6, 7, 6, 7,
                6, 7, 4, 6,
            ],
            opacity=0.75,
            name=name,
            hovertext=hover_text,
            hoverinfo="text",
        )
    )

def add_truck(fig, w, l, h):
    edges = [
        ((0, 0, 0), (w, 0, 0)),
        ((0, l, 0), (w, l, 0)),
        ((0, 0, h), (w, 0, h)),
        ((0, l, h), (w, l, h)),

        ((0, 0, 0), (0, l, 0)),
        ((w, 0, 0), (w, l, 0)),
        ((0, 0, h), (0, l, h)),
        ((w, 0, h), (w, l, h)),

        ((0, 0, 0), (0, 0, h)),
        ((w, 0, 0), (w, 0, h)),
        ((0, l, 0), (0, l, h)),
        ((w, l, 0), (w, l, h)),
    ]

    for start, end in edges:
        fig.add_trace(
            go.Scatter3d(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                z=[start[2], end[2]],
                mode="lines",
                showlegend=False,
                hoverinfo="skip",
                line={"width": 4},
            )
        )

def get_trucks(problem):
    if "trucks" in problem:
        return problem["trucks"]
    return [{"id": "truck-1", **problem["truck"]}]

def truck_figure(problem, truck, state, title):
    dims = truck["dimensions"]

    truck_w = dims["w"]
    truck_l = dims["l"]
    truck_h = dims["h"]

    package_lookup = {
        package["id"]: package
        for package in problem["packages"]
    }

    fig = go.Figure()

    add_truck(fig, truck_w, truck_l, truck_h, )

    placements = state.get(
        "placements",
        {},
    )

    for package_id, placement in placements.items():
        if placement is None or placement["truck_id"] != truck["id"]:
            continue

        package = package_lookup[package_id]
        position = placement["position"]
        orientation = placement["orientation"]

        w, l, h = oriented_dimensions(package, orientation, )

        hover = (
            f"<b>{package_id}</b><br>"
            f"Position: "
            f"({position['x']}, {position['y']}, {position['z']})<br>"
            f"Size: {w} x {l} x {h}<br>"
            f"Value: {package['value']}<br>"
            f"Weight: {package['weight']}<br>"
            f"Fragile: {package['is_fragile']}"
        )

        add_cuboid(fig, position["x"], position["y"], position["z"], w, l, h, package_id, hover, )

    fig.update_layout(
        title=title,

        scene={
            "xaxis_title": "X",
            "yaxis_title": "Y",
            "zaxis_title": "Z",

            "xaxis": {
                "range": [0, truck_w]
            },

            "yaxis": {
                "range": [0, truck_l]
            },

            "zaxis": {
                "range": [0, truck_h]
            },

            "aspectmode": "data",
        },

        margin={
            "l": 0,
            "r": 0,
            "t": 40,
            "b": 0,
        },
    )

    return fig

def score_chart(result, algorithm):
    fig = go.Figure()

    best_history = result.get(
        "score_history",
        [],
    )

    if best_history:
        fig.add_trace(
            go.Scatter(
                x=list(range(len(best_history))),
                y=best_history,
                mode="lines",
                name=(
                    "Maximum Fitness"
                    if algorithm == "genetic_algorithm"
                    else "Best Score"
                ),
            )
        )

    if algorithm == "simulated_annealing":
        current_history = (
            result
            .get("metrics", {})
            .get("current_score_history", [])
        )
        if current_history:
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(current_history))),
                    y=current_history,
                    mode="lines",
                    name="Current Score",
                )
            )

    if algorithm == "genetic_algorithm":

        average_history = result.get(
            "average_history",
            [],
        )

        if average_history:
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(average_history))),
                    y=average_history,
                    mode="lines",
                    name="Average Fitness",
                )
            )

    fig.update_layout(
        xaxis_title=(
            "Generation"
            if algorithm == "genetic_algorithm"
            else "Iteration"
        ),
        yaxis_title="Objective Value",
        margin={
            "l": 20,
            "r": 20,
            "t": 20,
            "b": 20,
        },
    )

    return fig


st.title("Optimasi Truck Peti Kemas")
st.subheader("Input")

uploaded_file = st.file_uploader(
    "Testcase JSON",
    type="json",
)
problem = None

if uploaded_file:

    try:
        problem = json.load(uploaded_file)

    except Exception as error:
        st.error(
            f"File tidak valid: {error}"
        )

st.subheader("Konfigurasi")
col1, col2, col3 = st.columns(3)

with col1:
    algorithm = st.selectbox(
        "Algoritma",
        [
            "simulated_annealing",
            "hill_climbing",
            "genetic_algorithm",
        ],
        format_func=lambda x: {
            "simulated_annealing": "Simulated Annealing",
            "hill_climbing": "Hill Climbing",
            "genetic_algorithm": "Genetic Algorithm",
        }[x],
    )

with col2:
    seed = st.number_input(
        "Seed",
        value=42,
        step=1,
    )

with col3:
    objective_mode = st.selectbox(
        "Objective",
        [
            "value",
            "eta_weighted",
        ],
        format_func=lambda x: {
            "value": "Value",
            "eta_weighted": "ETA Weighted",
        }[x],
    )

params = {}
if algorithm == "simulated_annealing":

    st.write("Parameter Simulated Annealing")

    col1, col2, col3 = st.columns(3)

    with col1:
        params["initial_temperature"] = (
            st.number_input(
                "Initial Temperature",
                value=500.0,
                min_value=0.01,
            )
        )
        params["max_iterations"] = (
            st.number_input(
                "Maximum Iterations",
                value=2000,
                min_value=1,
                step=100,
            )
        )

    with col2:
        params["cooling_rate"] = (
            st.number_input(
                "Cooling Rate",
                value=0.995,
                min_value=0.001,
                max_value=0.9999,
                format="%.4f",
            )
        )
        params["max_neighbor_attempts"] = (
            st.number_input(
                "Neighbor Attempts",
                value=200,
                min_value=1,
                step=10,
            )
        )

    with col3:
        params["min_temperature"] = (
            st.number_input(
                "Minimum Temperature",
                value=0.01,
                min_value=0.0001,
            )
        )
        params["stuck_threshold"] = (
            st.number_input(
                "Stuck Threshold",
                value=100,
                min_value=1,
                step=10,
            )
        )

elif algorithm == "hill_climbing":
    params["variant"] = st.selectbox(
        "Hill Climbing Variant",
        ["steepest", "sideways", "stochastic", "random_restart"],
        format_func=lambda x: {
            "steepest": "Steepest Ascent",
            "sideways": "Sideways Moves",
            "stochastic": "Stochastic",
            "random_restart": "Random Restart",
        }[x],
    )
    if params["variant"] == "random_restart":
        params["max_restarts"] = st.number_input(
            "Maximum Restarts",
            value=10,
            min_value=0,
            step=1,
        )
        params["max_iterations_per_restart"] = st.number_input(
            "Maximum Iterations per Restart",
            value=1000,
            min_value=1,
            step=100,
        )
    else:
        params["max_iterations"] = st.number_input(
            "Maximum Iterations",
            value=2000,
            min_value=1,
            step=100,
        )
        if params["variant"] == "sideways":
            params["max_sideways_moves"] = st.number_input(
                "Maximum Sideways Moves",
                value=100,
                min_value=0,
                step=1,
            )

elif algorithm == "genetic_algorithm":
    col1, col2 = st.columns(2)
    with col1:
        params["population_size"] = (
            st.number_input(
                "Population Size",
                value=50,
                min_value=2,
                step=10,
            )
        )

    with col2:
        params["max_iterations"] = (
            st.number_input(
                "Iterations",
                value=500,
                min_value=1,
                step=50,
            )
        )

eta_bonus = 0.0
if objective_mode == "eta_weighted":
    eta_bonus = st.number_input(
        "ETA Bonus",
        value=100.0,
        min_value=0.0,
        step=10.0,
    )

if st.button(
    "Run Algorithm",
    disabled=problem is None,
):

    payload = {
        "problem": problem,
        "algorithm": algorithm,
        "seed": int(seed),
        "objective": {
            "mode": objective_mode,
            "eta_bonus": eta_bonus,
        },
        "params": params,
    }

    try:

        with st.spinner(
            "Menjalankan algoritma..."
        ):
            result = run_algorithm(
                payload
            )

        st.session_state.result = result
        st.session_state.problem = problem
        st.session_state.algorithm = algorithm

    except Exception as error:
        st.error(
            f"Gagal menjalankan algoritma: {error}"
        )

if "result" in st.session_state:
    result = st.session_state.result
    problem = st.session_state.problem
    algorithm = st.session_state.algorithm

    st.divider()
    st.subheader("Hasil")

    initial_score = result.get(
        "initial_score",
        0,
    )

    final_score = result.get(
        "final_score",
        0,
    )

    iterations = result.get(
        "iterations",
        0,
    )

    duration = result.get(
        "duration_seconds",
        result.get("duration", 0),
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Initial Score",
        initial_score,
    )

    col2.metric(
        "Final Score",
        final_score,
    )

    col3.metric(
        "Iterations",
        iterations,
    )

    col4.metric(
        "Runtime",
        (
            f"{duration:.3f} s"
            if isinstance(
                duration,
                (int, float),
            )
            else str(duration)
        ),
    )
    st.subheader("Visualisasi State")
    initial_tab, final_tab = st.tabs(
        [
            "Initial State",
            "Final State",
        ]
    )

    with initial_tab:
        initial_state = result.get("initial_state")
        if initial_state:

            for truck in get_trucks(problem):
                st.plotly_chart(
                    truck_figure(
                        problem,
                        truck,
                        initial_state,
                        f"Initial State - {truck['id']}",
                    ),
                    use_container_width=True,
                )

    with final_tab:
        final_state = result.get("final_state")

        if final_state:
            for truck in get_trucks(problem):
                st.plotly_chart(
                    truck_figure(
                        problem,
                        truck,
                        final_state,
                        f"Final State - {truck['id']}",
                    ),
                    use_container_width=True,
                )

    st.subheader("Perkembangan Objective")
    st.plotly_chart(
        score_chart(
            result,
            algorithm,
        ),
        use_container_width=True,
    )

    if algorithm == "simulated_annealing":
        st.subheader("Simulated Annealing")

        metrics = result.get(
            "metrics",
            {},
        )
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Accepted Worse",
            metrics.get(
                "accepted_worse",
                0,
            ),
        )

        col2.metric(
            "Rejected",
            metrics.get(
                "rejected",
                0,
            ),
        )

        col3.metric(
            "Stuck Frequency",
            metrics.get(
                "stuck_frequency",
                0,
            ),
        )

        probabilities = metrics.get(
            "acceptance_probability_history",
            [],
        )
        points = [
            (iteration, probability)
            for iteration, probability in enumerate(probabilities, start=1)
            if probability is not None
        ]
        if points:
            probability_fig = go.Figure(
                go.Scatter(
                    x=[point[0] for point in points],
                    y=[point[1] for point in points],
                    mode="markers",
                    marker={"size": 4},
                    name="e^(ΔE/T)",
                )
            )
            probability_fig.update_layout(
                xaxis_title="Iteration",
                yaxis_title="e^(ΔE/T)",
                margin={
                    "l": 20,
                    "r": 20,
                    "t": 20,
                    "b": 20,
                },
            )
            st.plotly_chart(
                probability_fig,
                use_container_width=True,
            )

    st.subheader("Final Placement")
    final_state = result.get(
        "final_state",
        {},
    )

    placements = final_state.get(
        "placements",
        {},
    )

    rows = []
    for package_id, placement in placements.items():
        if placement is None:
            rows.append(
                {
                    "Package": package_id,
                    "Status": "Outside",
                    "Truck": "-",
                    "Position": "-",
                    "Orientation": "-",
                }
            )

        else:
            pos = placement["position"]
            ori = placement["orientation"]
            rows.append(
                {
                    "Package":
                        package_id,

                    "Status":
                        "Inside",

                    "Truck":
                        placement["truck_id"],

                    "Position":
                        (
                            f"({pos['x']}, "
                            f"{pos['y']}, "
                            f"{pos['z']})"
                        ),

                    "Orientation":
                        (
                            f"{ori['w']}, "
                            f"{ori['l']}, "
                            f"{ori['h']}"
                        ),
                }
            )

    st.dataframe(rows,
        hide_index=True,
        use_container_width=True,
    )
