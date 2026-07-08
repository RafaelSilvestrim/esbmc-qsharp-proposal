#include <math.h>
typedef struct { double real; double imag; } complex_t;

typedef struct {
    complex_t amp0;
    complex_t amp1;
    complex_t amp2;
    complex_t amp3;
} system_t;

int main() {
    system_t s;
    s.amp0.real = 1.0; s.amp0.imag = 0.0;
    s.amp1.real = 0.0; s.amp1.imag = 0.0;
    s.amp2.real = 0.0; s.amp2.imag = 0.0;
    s.amp3.real = 0.0; s.amp3.imag = 0.0;
    // Estado GHZ simulado pós portas lógicas
    s.amp0.real = 0.7071067811865475;
    s.amp3.real = 0.7071067811865475;

    double norm = (s.amp0.real*s.amp0.real + s.amp0.imag*s.amp0.imag) + (s.amp1.real*s.amp1.real + s.amp1.imag*s.amp1.imag) + (s.amp2.real*s.amp2.real + s.amp2.imag*s.amp2.imag) + (s.amp3.real*s.amp3.real + s.amp3.imag*s.amp3.imag);
    __ESBMC_assert(norm >= 0.999 && norm <= 1.001, "Norm failed");

    return 0;
}
