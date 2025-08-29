from parser import Netlist, Gate
from typing import Dict

def evaluate_gate(gate: Gate, signal_values: Dict[str, int]) -> int:
    inputs = [signal_values.get(inp, None) for inp in gate.inputs]
    if None in inputs:
        raise ValueError(f"Missing input signal value for gate {gate.name}")

    # NAND gate logic
    if gate.gtype == 'nand':
        return 0 if all(inputs) else 1

    # AND gate logic
    elif gate.gtype == 'and':
        return 1 if all(inputs) else 0

    # OR gate logic
    elif gate.gtype == 'or':
        return 1 if any(inputs) else 0

    # NOR gate logic
    elif gate.gtype == 'nor':
        return 0 if any(inputs) else 1

    # XOR gate logic
    elif gate.gtype == 'xor':
        return sum(inputs) % 2

    # NOT gate logic (single input)
    elif gate.gtype == 'not':
        return 0 if inputs[0] else 1

    else:
        raise NotImplementedError(f"Gate type '{gate.gtype}' not supported in simulation.")

def simulate(netlist: Netlist, input_values: Dict[str, int]) -> Dict[str, int]:
    # Initialize signal values with primary inputs
    signal_values = dict(input_values)

    # Organize gates by level for level-wise simulation
    gates_by_level = {}
    for gate in netlist.gates:
        gates_by_level.setdefault(gate.level, []).append(gate)

    max_level = max(gates_by_level.keys())

    for lvl in range(1, max_level + 1):
        for gate in gates_by_level.get(lvl, []):
            output_val = evaluate_gate(gate, signal_values)
            signal_values[gate.output] = output_val

    # Return outputs signal values
    return {out: signal_values.get(out, None) for out in netlist.outputs}

def get_user_inputs(input_names: list) -> Dict[str, int]:
    print("Please enter logic values for primary inputs (0 or 1):")
    inputs = {}
    for inp in input_names:
        while True:
            val = input(f"  {inp} = ").strip()
            if val in ('0', '1'):
                inputs[inp] = int(val)
                break
            else:
                print("Invalid input. Enter 0 or 1.")
    return inputs

if __name__ == "__main__":
    import textwrap
    from parser import parse_netlist_text, assign_levels

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

    user_inputs = get_user_inputs(netlist.inputs)
    outputs = simulate(netlist, user_inputs)

    print("\nSimulation Results:")
    for out, val in outputs.items():
        print(f"  {out} = {val}")
