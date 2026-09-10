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
Description: This file is used for setting and updating of VMs info
"""
# @code

import re
import time
import os

import libvirt

from logger import LOGGER

DEFAULT_PRIORITY = "machine"
HIGH_PRIORITY = "high_prio_machine"
LOW_PRIORITY = "low_prio_machine"
PIDS_CGRP_PATH = "/sys/fs/cgroup/pids"
DOMAIN_STOP_MSG = "domain is not running"


class DomainInfo:
    def __init__(self):
        self.domain_id = 0
        self.domain_name = 0
        self.domain_usage = 0
        self.running_time = []
        self.priority = 0
        self.cpu_usage = []
        self.package_usage_dict = {}
        self.last_update_time = 0
        self.global_quota_config = 0
        self.cgroup_name = None

    def set_domain_attribute(self, domain, host_topo):
        self.domain_name = domain.name()
        self.domain_id = int(domain.ID())

        quota_parameter = re.search("<global_quota>(.*)</global_quota>", domain.XMLDesc())
        if quota_parameter:
            self.global_quota_config = int(quota_parameter.groups()[0])
        else:
            self.global_quota_config = -1
        LOGGER.debug("Domain %s(%d) global quota setting is %d"
                     % (self.domain_name, self.domain_id, self.global_quota_config))

        self.last_update_time = time.time_ns()
        domain_running_time_list = domain.getCPUStats(total=False)

        for cpu in domain_running_time_list:
            self.running_time.append(cpu.get('cpu_time'))
            self.cpu_usage.append(0)
        for package in host_topo.package_set:
            self.package_usage_dict[package] = 0

        priority_info = re.search("<partition>/(.*)</partition>", domain.XMLDesc())
        if not priority_info or len(priority_info.groups()) != 1:
            LOGGER.error("Domain %s(%d) cgroup partition setting in XML is missing or wrong!"
                         % (self.domain_name, self.domain_id))
            return -1
        if priority_info.groups()[0] == HIGH_PRIORITY or \
           priority_info.groups()[0] == DEFAULT_PRIORITY:
            self.priority = 0
        elif priority_info.groups()[0] == LOW_PRIORITY:
            self.priority = 1
        else:
            LOGGER.error("Domain %s(%d) priority setting (%s) is wrong!"
                         % (self.domain_name, self.domain_id, priority_info.groups()[0]))
            return -1
        vms_cgrp_path = os.path.join(PIDS_CGRP_PATH, priority_info.groups()[0] + ".slice")
        for subpath in os.listdir(vms_cgrp_path):
            if "machine-qemu\\x2d%d\\x2d" % self.domain_id in subpath:
                self.cgroup_name = subpath
                break
        else:
            LOGGER.error("Domain %d cgroup path can't found" % self.domain_id)
            raise IOError

        LOGGER.debug("Domain %s(%d) Priority is %s"
                     % (self.domain_name, self.domain_id, priority_info.groups()[0]))
        return 0

    def update_domain_info(self, domain, host_topo):
        current_time = time.time_ns()
        domain_running_time_list = domain.getCPUStats(total=False)

        domain_usage = 0
        for package in self.package_usage_dict:
            self.package_usage_dict[package] = 0

        for cpu in range(len(domain_running_time_list)):
            if (current_time - self.last_update_time) != 0:
                self.cpu_usage[cpu] = (domain_running_time_list[cpu].get("cpu_time") -
                                       self.running_time[cpu]) / (current_time - self.last_update_time)
            else:
                self.cpu_usage[cpu] = 0
            domain_usage += self.cpu_usage[cpu]
            self.running_time[cpu] = domain_running_time_list[cpu].get("cpu_time")
            package = host_topo.cpu_topo_list[cpu]
            self.package_usage_dict[package] += self.cpu_usage[cpu]

        self.domain_usage = domain_usage
        self.last_update_time = current_time
        LOGGER.debug("Domain %s(%d) usage is %.2f, update time is %d"
                     % (self.domain_name, self.domain_id, self.domain_usage, current_time))
        return 0


class GuestInfo:
    def __init__(self):
        self.vm_dict = {}
        self.low_prio_vm_dict = {}
        self.vm_online_dict = {}
        self.domain_online = []
        self.running_domain_in_cpus = []

    def update_guest_info(self, conn, host_topo):
        self.running_domain_in_cpus.clear()
        self.vm_online_dict.clear()
        self.domain_online.clear()
        self.low_prio_vm_dict.clear()

        for cpu in range(host_topo.max_cpu_nums):
            self.running_domain_in_cpus.append([])

        self.get_all_active_domain(conn)
        for dom in self.domain_online:
            self.vm_online_dict[dom.ID()] = dom
        # Remove ever see but now stopped domains
        for vm_id in list(self.vm_dict):
            if vm_id not in self.vm_online_dict:
                del self.vm_dict[vm_id]

        for vm_id in self.vm_online_dict:
            try:
                if vm_id in self.vm_dict:
                    ret = self.vm_dict.get(vm_id).update_domain_info(self.vm_online_dict.get(vm_id), host_topo)
                else:
                    self.vm_dict[vm_id] = DomainInfo()
                    ret = self.vm_dict.get(vm_id).set_domain_attribute(self.vm_online_dict.get(vm_id), host_topo)
            except libvirt.libvirtError as e:
                ret = -1
                # If domain doesn't stop, raise exception
                if e.get_error_code() != libvirt.VIR_ERR_NO_DOMAIN and \
                   DOMAIN_STOP_MSG not in e.get_error_message():
                    raise
            if ret < 0:
                del self.vm_dict[vm_id]
                continue

            if self.vm_dict.get(vm_id).priority == 1:
                self.low_prio_vm_dict[vm_id] = self.vm_dict.get(vm_id)
            for cpu in range(host_topo.max_cpu_nums):
                self.running_domain_in_cpus[cpu].append((self.vm_dict.get(vm_id).cpu_usage[cpu],
                                                         self.vm_dict.get(vm_id).domain_id,
                                                         self.vm_dict.get(vm_id).domain_name,
                                                         self.vm_dict.get(vm_id).priority))

    def get_all_active_domain(self, conn):
        try:
            self.domain_online = conn.listAllDomains(flags=libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
        except libvirt.libvirtError:
            LOGGER.error("Failed to get all active domain info")
            raise
        else:
            LOGGER.info("Active domain number is %d" % len(self.domain_online))
