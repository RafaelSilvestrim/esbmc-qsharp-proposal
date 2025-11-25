// C_HARNESS_TEMPLATE.c — versão corrigida para ESBMC
// O ESBMC já define __VERIFIER_nondet_bool como _Bool
// Nunca use 'bool' aqui.

extern _Bool __VERIFIER_nondet_bool(void);

int main(void) {
  _Bool q = __VERIFIER_nondet_bool();

  // === INJETADO PELO TRADUTOR ===
  /* {{OPERACOES_EM_C}} */
  // === FIM ===

  _Bool r = q;

  // Verificação de identidade (X∘X = I)
  __ESBMC_assert(r == __INITIAL_Q__, "Quantum identity property violated");

  return 0;
}
