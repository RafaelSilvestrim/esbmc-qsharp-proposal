// classical/toggle_twice.c

// Declaração compatível com a intrínseca do ESBMC
extern _Bool __VERIFIER_nondet_bool(void);

static _Bool toggle(_Bool b) {
  return !b;
}

int main(void) {
  _Bool b = __VERIFIER_nondet_bool();
  _Bool after = toggle(toggle(b));

  // Pode usar assert padrão; ESBMC transforma em verificação
  __ESBMC_assert(after == b, "toggle twice returns original");

  return 0;
}
