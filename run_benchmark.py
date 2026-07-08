import time
import subprocess
import math

def generate_ghz_c_code(num_qubits):
    num_states = 2 ** num_qubits
    c_code = "#include <math.h>\n"
    c_code += "typedef struct { double real; double imag; } complex_t;\n\n"
    
    # Criar a estrutura do sistema dinamicamente
    c_code += "typedef struct {\n"
    for i in range(num_states):
        c_code += f"    complex_t amp{i};\n"
    c_code += "} system_t;\n\n"
    
    c_code += "int main() {\n"
    c_code += "    system_t s;\n"
    
    # Estado inicial: |0...0> = 1.0, resto = 0.0
    c_code += "    s.amp0.real = 1.0; s.amp0.imag = 0.0;\n"
    for i in range(1, num_states):
        c_code += f"    s.amp{i}.real = 0.0; s.amp{i}.imag = 0.0;\n"
    
    # Aplicar Hadamard no qubit 0 e CNOT nos demais (Simplificação direta do estado final GHZ)
    val = 1.0 / math.sqrt(2)
    last_state = num_states - 1
    
    c_code += f"    // Estado GHZ simulado pós portas lógicas\n"
    c_code += f"    s.amp0.real = {val};\n"
    c_code += f"    s.amp{last_state}.real = {val};\n"
    
    # Asserção de unidade para forçar o SMT a calcular a soma do vetor
    assertion = " + ".join([f"(s.amp{i}.real*s.amp{i}.real + s.amp{i}.imag*s.amp{i}.imag)" for i in range(num_states)])
    c_code += f"\n    double norm = {assertion};\n"
    c_code += "    __ESBMC_assert(norm >= 0.999 && norm <= 1.001, \"Norm failed\");\n"
    
    c_code += "\n    return 0;\n"
    c_code += "}\n"
    
    return c_code

def run_benchmark():
    # Testaremos 2, 4, 8 e 12 qubits (12 qubits = 4096 variáveis no Z3)
    qubits_to_test = [2, 4, 8, 12]
    
    print(f"{'Qubits':<10} | {'States':<10} | {'Result':<10} | {'Time (s)'}")
    print("-" * 50)
    
    for q in qubits_to_test:
        states = 2 ** q
        c_file = f"benchmark_{q}q.c"
        
        with open(c_file, "w") as f:
            f.write(generate_ghz_c_code(q))
            
        start_time = time.time()
        
        try:
            # Executa o ESBMC e silencia a saída padrão, queremos apenas o tempo
            process = subprocess.run(
                ["esbmc", c_file, "--floatbv", "--unwind", "1", "--z3"],
                capture_output=True, text=True, timeout=120
            )
            elapsed = time.time() - start_time
            
            if "VERIFICATION SUCCESSFUL" in process.stdout:
                result = "UNSAT"
            else:
                result = "SAT/FAIL"
                
        except subprocess.TimeoutExpired:
            elapsed = 120.0
            result = "TIMEOUT"
            
        print(f"{q:<10} | {states:<10} | {result:<10} | {elapsed:.2f}")

if __name__ == "__main__":
    run_benchmark()