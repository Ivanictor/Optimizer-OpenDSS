import py_dss_interface
from py_dss_toolkit import dss_tools
import pandas as pd
from pathlib import Path

def initialize_opendss():
    """Inicializa o OpenDSS e gera os dataframes com transformadores, cargas e barras"""

    dss = py_dss_interface.DSS()

    BASE_DIR = Path(__file__).resolve().parent.parent

    dss_file = BASE_DIR / "Alim_Meia_Ponte_5_REDUZIDO" / "Master_PyDSS_Interface.dss"

    dss_tools.update_dss(dss)

    dss.text(f"compile [{dss_file}]")

    dss.text(f"buscoords BusCoords.csv")

    dss.text("set mode=daily")
    dss.text("set stepsize=1h")
    dss.text("set number=24")

    trafo_df = dss_tools.model.transformers_df
    loads_df = dss_tools.model.loads_df
    buses_df = dss_tools.model.buses_df
    lines_df = dss_tools.model.lines_df

    loads_df["kw"] = pd.to_numeric(loads_df["kw"], errors="coerce")
    loads_df = loads_df.sort_values(by='kw', ascending=False)

    trafo_df["bus_name"] = trafo_df["bus"].str.split(".").str[0]
    lines_df["bus_name"] = lines_df["bus1"].str.split(".").str[0]

    buses_df = buses_df[["name", "distance", "all_pce_active_bus", "all_pde_active_bus"]]

    loads_df = loads_df[["name", "bus1"]]

    return dss, dss_tools, trafo_df, loads_df, buses_df, lines_df

def solve_circuit(
        dss: py_dss_interface.DSS, 
        buses: list, 
        trafo_df: pd.DataFrame, 
        buses_df: pd.DataFrame, 
        lines_df: pd.DataFrame
        ) -> float:

    BASE_DIR = Path(__file__).resolve().parent.parent
    
    dss_file = BASE_DIR / "Alim_Meia_Ponte_5_REDUZIDO" / "Master_PyDSS_Interface.dss"
    dss.text(f"compile [{dss_file}]")
    dss.text("Redirect 'PV_System_120_MeiaPonte.dss'")
    
    dss.text(f"buscoords BusCoords.csv")

    dss.text("set mode=daily")
    dss.text("set stepsize=1h")
    dss.text("set number=24")
    dss.text("set maxcontroliter=100")

    for i, bus in enumerate(buses):
        
        element_type, element_name, kv = decide_element(bus, buses_df, trafo_df, lines_df)
        pot = 280

        dss.text(f"New Storage.Battery_{i} phases=3 bus1={bus} kv={kv} kWrated={pot} kWhrated={pot*8} dispmode=follow %stored=50")

        dss.text(f"New StorageController.SC_{i} element={element_type}.{element_name} terminal=1 modedis=peakShave elementList=[Battery_{i}]\n"
        f"~ MonPhase=AVG kwtarget=5 modecharge=peakShaveLow kwtargetLow=0\n\n")
    
    dss.solution.solve()

    soma = 0
    for name in dss.monitors.names:
        if "voltage" in name:
            continue

        dss.monitors.name = name
        monitor = dss.monitors.channel(1)

        soma += sum(x for x in monitor if x < 0)

    print(f"\nFluxo reverso dessa solução: {soma}")
    print(f"Barras da solução: {buses}")

    return soma

def decide_element(bus: str, buses_df: pd.DataFrame, trafo_df: pd.DataFrame, lines_df: pd.DataFrame) -> tuple:
    bus = bus.split(".")[0]
    elements_query = buses_df.query(f"name == '{bus}'")["all_pde_active_bus"].iloc[0]

    distance = 1e6
    for element in elements_query:
        element_type, element_name = element.split(".")

        if element_type == "Line":
            segment_df = lines_df.query(f"name == '{element_name}'")

            element_bus = segment_df["bus_name"].iloc[0]
            distance_bus = buses_df.query(f"name == '{element_bus}'")["distance"].iloc[0]

            if "mt" in element_name:
                kv = 13.8

            elif "bt" in element_name:
                kv = 0.38

            else:
                continue

        elif element_type == "Transformer":
            element_bus = trafo_df.query(f"name == '{element_name}'")["bus_name"].iloc[0]
            distance_bus = buses_df.query(f"name == '{element_bus}'")["distance"].iloc[0]
            kv = trafo_df.query(f"name == '{element_name}'")["kv"].iloc[0]

        else:
            continue

        if distance_bus < distance:
            distance = distance_bus
            selected_element = element_name
            selected_element_type = element_type
            selected_kv = kv

    return selected_element_type, selected_element, selected_kv



