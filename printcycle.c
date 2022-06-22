#include <stdio.h>

#define READ_CSR(reg)                             \
  ({                                              \
    unsigned long __tmp;                          \
    asm volatile("csrr %0, " #reg : "=r"(__tmp)); \
    __tmp;                                        \
  })

int main() {
  printf("time: %lu\n", READ_CSR(time));
  printf("cycle: %lu\n", READ_CSR(cycle));
  printf("instret: %lu\n", READ_CSR(instret));
  return 0;
}
