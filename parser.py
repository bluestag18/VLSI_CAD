from dataclasses import dataclass, field
from typing import List, Optional
import re
import textwrap
from collections import defaultdict

@dataclass
class Gate:
    gtype: str
    name: Optional[str]
    output: str
    inputs: List[str]
    value_inp: List[Optional[int]] = field(default_factory=list)
    value_out: Optional[int] = None
    level: Optional[int] = None  # will be assigned later

@dataclass
class Netlist:
    inputs: List[str]
    outputs: List[str]
    wires: List[str]
    gates: List[Gate]

def remove_comments(text: str) -> str:
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return text

def find_identifiers(s: str) -> List[str]:
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", s)

def unique_preserve(seq: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def parse_netlist_text(text: str) -> Netlist:
    text = remove_comments(text)
    statements = [stmt.strip() for stmt in text.split(';') if stmt.strip()]
    inputs, outputs, wires, gates = [], [], [], []
    
    for stmt in statements:
        if stmt.startswith('module') or stmt.startswith('endmodule'):
            continue
        m = re.match(r'^(input|output|wire)\b(.*)$', stmt, re.I)
        if m:
            kind = m.group(1).lower()
            rest = m.group(2)
            ids = find_identifiers(rest)
            if kind == 'input':
                inputs += ids
            elif kind == 'output':
                outputs += ids
            elif kind == 'wire':
                wires += ids
            continue
        mg = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z0-9_]+)\s*\((.*)\)$', stmt, re.S)
        if mg:
            gtype = mg.group(1).lower()
            name = mg.group(2)
            ids = find_identifiers(mg.group(3))
            if ids:
                gates.append(Gate(gtype, name, ids[0], ids[1:]))
            continue
        mg2 = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)$', stmt, re.S)
        if mg2:
            gtype = mg2.group(1).lower()
            ids = find_identifiers(mg2.group(2))
            if ids:
                gates.append(Gate(gtype, None, ids[0], ids[1:]))
            continue
    return Netlist(unique_preserve(inputs), unique_preserve(outputs), unique_preserve(wires), gates)

def parse_netlist_file(path: str) -> Netlist:
    with open(path, 'r') as f:
        return parse_netlist_text(f.read())

def build_graph(netlist):
    graph = defaultdict(list)
    wire_to_gate = {gate.output: gate.name for gate in netlist.gates}
    for gate in netlist.gates:
        for inp in gate.inputs:
            if inp in wire_to_gate:
                graph[wire_to_gate[inp]].append(gate.name)
    return graph

def assign_levels(netlist):
    remaining_gates = list(netlist.gates)
    known_signals = set(netlist.inputs)
    level_num = 1

    while remaining_gates:
        current_level = []
        for gate in remaining_gates:
            if all(inp in known_signals for inp in gate.inputs):
                gate.level = level_num
                current_level.append(gate)
        if not current_level:
            raise ValueError("Cannot resolve remaining gates — possible cycle or missing signal.")
        for gate in current_level:
            known_signals.add(gate.output)
        remaining_gates = [g for g in remaining_gates if g.level is None]
        level_num += 1

if __name__ == "__main__":
    c17_example = textwrap.dedent("""
    module c17 (N1, N2, N3, N6, N7, N22, N23);
    input N1, N2, N3, N6, N7;
    output N22, N23;
    wire N10, N11, N16, N19;

    nand NAND2_1 (N10, N1, N3);
    nand NAND2_2 (N11, N3, N6);
    nand NAND2_3 (N16, N2, N11);
    nand NAND2_4 (N19, N11, N7);
    nand NAND2_5 (N22, N10, N16);
    nand NAND2_6 (N23, N16, N19);
    endmodule
    """)

    netlist = parse_netlist_text(c17_example)
    assign_levels(netlist)

    print("=== Parsed netlist summary ===")
    print("Inputs :", netlist.inputs)
    print("Outputs:", netlist.outputs)
    print("Wires  :", netlist.wires)
    print(f"Gates  : {len(netlist.gates)} instances\n")

    for g in netlist.gates:
        print(f"{g.name:10} out={g.output:4} ins={g.inputs} level={g.level}")
