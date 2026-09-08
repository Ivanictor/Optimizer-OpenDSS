import py_dss_interface
from py_dss_toolkit import dss_tools
import pandas as pd

def initialize_opendss():

    dss = py_dss_interface.DSS()

    dss_file = r"C:\Dados_teste\OpenDSS\GWO\Alim_Meia_Ponte_5_REDUZIDO\Master_PyDSS_Interface.dss"

    dss_tools.update_dss(dss)

    dss.text(f"compile [{dss_file}]")

    dss.text(f"buscoords BusCoords.csv")

    dss.text("set mode=daily")
    dss.text("set stepsize=1h")
    dss.text("set number=24")

    trafo_df = dss_tools.model.transformers_df
    loads_df = dss_tools.model.loads_df

    loads_df["kw"] = pd.to_numeric(loads_df["kw"], errors="coerce")
    loads_df = loads_df.sort_values(by='kw', ascending=False)

    return dss, dss_tools, trafo_df, loads_df

def solve_circuit(dss: py_dss_interface.DSS, buses: list, trafo_df: pd.DataFrame):

    dss_file = r"C:\Dados_teste\OpenDSS\GWO\Alim_Meia_Ponte_5_REDUZIDO\Master_PyDSS_Interface.dss"
    dss.text(f"compile [{dss_file}]")
    
    dss.text(f"buscoords BusCoords.csv")

    dss.text("set mode=daily")
    dss.text("set stepsize=1h")
    dss.text("set number=24")
    for i, bus in enumerate(buses):
        dss.text(f"New Storage.Battery_{i} phases=3 bus1={bus} kv=0.38 kWrated=100 kWhrated=800 dispmode=follow %stored=50")

        trafo_name = trafo_df.query(f"bus == '{bus}'")["name"].iloc[0]

        dss.text(f"New StorageController.SC_{i} element=Transformer.{trafo_name} terminal=1 modedis=peakShave elementList=[Battery_{i}]\n"
        f"~ MonPhase=AVG kwtarget=5 modecharge=peakShaveLow kwtargetLow=0\n\n")
    
    dss.solution.solve()

    soma = 0
    for name in dss.monitors.names:
        if "voltage" in name:
            continue

        dss.monitors.name = name
        monitor = dss.monitors.channel(1)

        soma += sum(x for x in monitor if x < 0)

    return soma





