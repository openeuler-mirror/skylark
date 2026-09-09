#! /usr/bin/python
# coding=UTF-8
"""
Copyright (c) Huawei Technologies Co., Ltd. 2022. All rights reserved.
skylark licensed under the Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
    http://license.coscl.org.cn/MulanPSL2
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
PURPOSE.
See the Mulan PSL v2 for more details.
Author: Jinhao Gao
Create: 2022-05-30
Description: This file is used for providing MSR Library class
"""
# @code

import ctypes

from logger import LOGGER


class MsrLibrary:
    def __init__(self):
        self.c_lib = ctypes.cdll.LoadLibrary("/usr/lib/libskylarkmsr.so")

    def allocate_fd_percpu(self, max_cpu_nums):
        ret = self.c_lib.allocate_fd_percpu(max_cpu_nums)
        if ret:
            LOGGER.error("Failed to calloc fd_percpu!")
            raise OSError

    def clear_memory(self):
        self.c_lib.free_fd_percpu()

    def get_cpu_microarch(self):
        return self.c_lib.get_cpu_microarch()

    def get_family_model(self):
        return self.c_lib.get_family_model()

    def check_has_aperf(self):
        return self.c_lib.check_has_aperf()

    def get_msr(self, cpu, offset):
        msr = ctypes.c_ulonglong(0)
        if self.c_lib.get_msr(cpu, offset, ctypes.byref(msr)):
            LOGGER.error("CPU %d: msr offset %d read failed" % (cpu, offset))
            raise OSError
        else:
            return msr.value

    def get_cpu_status_data(self, cpuid, perf_data_pointer):
        return self.c_lib.get_cpu_status_data(cpuid, perf_data_pointer)
