/*
* Copyright (c) Huawei Technologies Co., Ltd. 2022. All rights reserved.
* skylark licensed under the Mulan PSL v2.
* You can use this software according to the terms and conditions of the Mulan PSL v2.
* You may obtain a copy of Mulan PSL v2 at:
*     http://license.coscl.org.cn/MulanPSL2
* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
* PURPOSE.
* See the Mulan PSL v2 for more details.
* Author: Jinhao Gao
* Create: 2022-05-30
* Description: This file is used for providing a dynamic link library
*/

#ifdef __x86_64__

#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>

#define MSR_IA32_MPERF      0x000000e7
#define MSR_IA32_APERF      0x000000e8
#define Genu                0x756e6547
#define inel                0x6c65746e
#define inte                0x49656e69

int *fd_percpu;
static int fd_percpu_max_num;

typedef struct StructPerf {
    unsigned long long aperf;
    unsigned long long mperf;
} StructPerf, *StructPerfPointer;

static inline void cpuid(unsigned int *eax, unsigned int *ebx,
                         unsigned int *ecx, unsigned int *edx)
{
    asm volatile("cpuid"
        : "=a" (*eax),
          "=b" (*ebx),
          "=c" (*ecx),
          "=d" (*edx)
        :  "a" (*eax));
}

int get_cpu_microarch(void)
{
    unsigned int eax, ebx, ecx, edx;
    unsigned int genuine_intel = 0;

    eax = ebx = ecx = edx = 0;

    cpuid(&eax, &ebx, &ecx, &edx);
    if (ebx == Genu && ecx == inel && edx == inte) {
        genuine_intel = 1;
    }
    return genuine_intel;
}

unsigned int get_family_model(void)
{
    unsigned int eax, ebx, ecx, edx;

    eax = 1;
    ebx = ecx = edx = 0;
    cpuid(&eax, &ebx, &ecx, &edx);
    return eax;
}

unsigned int check_has_aperf(void)
{
    unsigned int eax, ebx, ecx, edx;
    unsigned int has_aperf;

    eax = 6; /* The cpuid of checking aperf instruction is 6 */
    ebx = ecx = edx = 0;
    cpuid(&eax, &ebx, &ecx, &edx);
    has_aperf = ecx & (1 << 0);
    return has_aperf;
}

int allocate_fd_percpu(int max_cpu_num)
{
    if (max_cpu_num <= 0) {
        return -1;
    }

    fd_percpu = calloc(max_cpu_num, sizeof(int));
    if (fd_percpu == NULL) {
        return -1;
    }
    fd_percpu_max_num = max_cpu_num;
    return 0;
}

void free_fd_percpu(void)
{
    int i;

    if (fd_percpu != NULL) {
        for (i = 0; i < fd_percpu_max_num; i++) {
            if (fd_percpu[i]) {
                close(fd_percpu[i]);
            }
        }

        free(fd_percpu);
        fd_percpu = NULL;
        fd_percpu_max_num = 0;
    }
}

static unsigned long long rdtsc(void)
{
    unsigned int low, high;

    asm volatile ("rdtsc":"=a" (low), "=d"(high));
    return low | (((unsigned long long)high) << 32); /* High denotes high 32 bits. */
}

static int get_msr_fd(int cpu)
{
    char pathname[32];
    int fd;

    if (cpu < 0 || cpu >= fd_percpu_max_num) {
        return -1;
    }

    fd = fd_percpu[cpu];
    if (fd) {
        return fd;
    }

    sprintf(pathname, "/dev/cpu/%d/msr", cpu);
    fd = open(pathname, O_RDONLY);
    if (fd < 0) {
        return -1;
    }

    fd_percpu[cpu] = fd;
    return fd;
}

int get_msr(int cpu, long offset, unsigned long long *msr)
{
    long retval;

    retval = pread(get_msr_fd(cpu), msr, sizeof(*msr), offset);
    if (retval != sizeof(*msr)) {
        return -1;
    }
    return 0;
}

int get_cpu_status_data(int cpu, StructPerfPointer p)
{
    unsigned long long tsc_before, tsc_between, tsc_after, aperf_time, mperf_time;
    int aperf_mperf_retry_count = 0;
    int retry_max_count = 5;
    int timeout_times = 2;

    while (aperf_mperf_retry_count < retry_max_count) {
        if (get_msr(cpu, MSR_IA32_APERF, &p->aperf)) {
            return -1;
        }
        tsc_before = rdtsc();
        if (get_msr(cpu, MSR_IA32_APERF, &p->aperf)) {
            return -1;
        }
        tsc_between = rdtsc();
        if (get_msr(cpu, MSR_IA32_MPERF, &p->mperf)) {
            return -1;
        }
        tsc_after = rdtsc();

        aperf_time = tsc_between - tsc_before;
        mperf_time = tsc_after - tsc_between;
        if ((aperf_time > (timeout_times * mperf_time)) || (mperf_time > (timeout_times * aperf_time))) {
            aperf_mperf_retry_count++;
            continue;
        }
        return 0;
    }
    return -2; /* -2 denotes timeout error. */
}

#endif /* __x86_64__ */
