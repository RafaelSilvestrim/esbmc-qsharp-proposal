#include <math.h>
typedef struct { double real; double imag; } complex_t;

typedef struct {
    complex_t amp0;
    complex_t amp1;
    complex_t amp2;
    complex_t amp3;
    complex_t amp4;
    complex_t amp5;
    complex_t amp6;
    complex_t amp7;
    complex_t amp8;
    complex_t amp9;
    complex_t amp10;
    complex_t amp11;
    complex_t amp12;
    complex_t amp13;
    complex_t amp14;
    complex_t amp15;
} system_t;

int main() {
    system_t s;
    s.amp0.real = 1.0; s.amp0.imag = 0.0;
    s.amp1.real = 0.0; s.amp1.imag = 0.0;
    s.amp2.real = 0.0; s.amp2.imag = 0.0;
    s.amp3.real = 0.0; s.amp3.imag = 0.0;
    s.amp4.real = 0.0; s.amp4.imag = 0.0;
    s.amp5.real = 0.0; s.amp5.imag = 0.0;
    s.amp6.real = 0.0; s.amp6.imag = 0.0;
    s.amp7.real = 0.0; s.amp7.imag = 0.0;
    s.amp8.real = 0.0; s.amp8.imag = 0.0;
    s.amp9.real = 0.0; s.amp9.imag = 0.0;
    s.amp10.real = 0.0; s.amp10.imag = 0.0;
    s.amp11.real = 0.0; s.amp11.imag = 0.0;
    s.amp12.real = 0.0; s.amp12.imag = 0.0;
    s.amp13.real = 0.0; s.amp13.imag = 0.0;
    s.amp14.real = 0.0; s.amp14.imag = 0.0;
    s.amp15.real = 0.0; s.amp15.imag = 0.0;
    // Estado GHZ simulado pós portas lógicas
    s.amp0.real = 0.7071067811865475;
    s.amp15.real = 0.7071067811865475;

    double norm = (s.amp0.real*s.amp0.real + s.amp0.imag*s.amp0.imag) + (s.amp1.real*s.amp1.real + s.amp1.imag*s.amp1.imag) + (s.amp2.real*s.amp2.real + s.amp2.imag*s.amp2.imag) + (s.amp3.real*s.amp3.real + s.amp3.imag*s.amp3.imag) + (s.amp4.real*s.amp4.real + s.amp4.imag*s.amp4.imag) + (s.amp5.real*s.amp5.real + s.amp5.imag*s.amp5.imag) + (s.amp6.real*s.amp6.real + s.amp6.imag*s.amp6.imag) + (s.amp7.real*s.amp7.real + s.amp7.imag*s.amp7.imag) + (s.amp8.real*s.amp8.real + s.amp8.imag*s.amp8.imag) + (s.amp9.real*s.amp9.real + s.amp9.imag*s.amp9.imag) + (s.amp10.real*s.amp10.real + s.amp10.imag*s.amp10.imag) + (s.amp11.real*s.amp11.real + s.amp11.imag*s.amp11.imag) + (s.amp12.real*s.amp12.real + s.amp12.imag*s.amp12.imag) + (s.amp13.real*s.amp13.real + s.amp13.imag*s.amp13.imag) + (s.amp14.real*s.amp14.real + s.amp14.imag*s.amp14.imag) + (s.amp15.real*s.amp15.real + s.amp15.imag*s.amp15.imag);
    __ESBMC_assert(norm >= 0.999 && norm <= 1.001, "Norm failed");

    return 0;
}
