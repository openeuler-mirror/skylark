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
Description: This file is used for skylark main framework
"""
# @code

from __future__ import division

import atexit
import fcntl
import os
import platform
import signal
import stat
import subprocess
import sys

from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR
import libvirt

from data_collector.datacollector import DataCollector
from data_collector.msrlibrary import MsrLibrary
from logger import LOGGER
from qos_analyzer.poweranalyzer import PowerAnalyzer
from qos_controller.cpucontroller import CpuController
from qos_controller.netcontroller import NetController
from qos_controller.cachembwcontroller import CacheMBWController
import util

QOS_MANAGER_ENTRY = None
LIBVIRT_URI = None
LIBVIRT_CONN = None
LIBVIRT_DRIVE_TYPE = None
PID_FILE = None
MSR_PATH = "/dev/cpu/0/msr"
PID_FILE_NAME = "/var/run/skylarkd.pid"
LOW_VMS_PID_CGRP_PATH = "/sys/fs/cgroup/pids/low_prio_machine.slice"


class QosManager:
    def __init__(self, vir_conn):
        self.vir_conn = vir_conn
        self.data_collector = DataCollector()
        self.power_analyzer = PowerAnalyzer()
        self.cpu_controller = CpuController()
        self.net_controller = NetController()
        self.cachembw_controller = CacheMBWController()

    def scheduler_listener(self, event):
        if event.exception:
            LOGGER.info("The Scheduler detects an exception, send SIGABRT and restart skylark...")
            self.scheduler.remove_all_jobs()
            os.kill(os.getpid(), signal.SIGABRT)

    def init_scheduler(self):
        self.scheduler = BlockingScheduler(logger=LOGGER)
        if os.getenv("POWER_QOS_MANAGEMENT", "false").lower() == "true":
            self.scheduler.add_job(self.__do_power_manage, trigger='interval', seconds=1, id='do_power_manage')
        self.scheduler.add_job(self.__do_resctrl_sync, trigger='interval', seconds=0.5, id='do_resctrl_sync')
        self.scheduler.add_listener(self.scheduler_listener, EVENT_JOB_ERROR)

    def init_data_collector(self):
        self.data_collector.set_static_base_info()
        self.data_collector.update_base_info(self.vir_conn)
        if os.getenv("POWER_QOS_MANAGEMENT", "false").lower() == "true":
            self.data_collector.set_static_power_info()

    def init_qos_analyzer(self):
        if os.getenv("POWER_QOS_MANAGEMENT", "false").lower() == "true":
            self.power_analyzer.set_hotspot_threshold(self.data_collector)

    def init_qos_controller(self):
        self.cpu_controller.set_low_priority_cgroup()
        if os.getenv("POWER_QOS_MANAGEMENT", "false").lower() == "true":
            atexit.register(self.cpu_controller.reset_domain_bandwidth, self.data_collector.guest_info)
        self.cachembw_controller.init_cachembw_controller(self.data_collector.host_info.resctrl_info)
        self.net_controller.init_net_controller()

    def start_scheduler(self):
        self.scheduler.start()

    def __do_power_manage(self):
        self.data_collector.update_base_info(self.vir_conn)
        self.data_collector.update_power_info()
        self.power_analyzer.power_manage(self.data_collector, self.cpu_controller)

    def __do_resctrl_sync(self):
        with os.scandir(LOW_VMS_PID_CGRP_PATH) as it:
            for entry in it:
                if entry.is_file():
                    continue
                tasks_path = os.path.join(LOW_VMS_PID_CGRP_PATH, entry.name, "tasks")
                self.cachembw_controller.add_vm_pids(tasks_path)


def create_pid_file():
    global PID_FILE

    fd = os.open(PID_FILE_NAME, os.O_RDWR | os.O_CREAT, stat.S_IRUSR | stat.S_IWUSR)
    os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
    os.close(fd)
    try:
        PID_FILE = open(PID_FILE_NAME, 'a')
    except IOError:
        LOGGER.error("Failed to open pid file")
        sys.exit(1)

    try:
        fcntl.flock(PID_FILE.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        LOGGER.error("A running service instance already creates the pid file! This service will exit!")
        PID_FILE.close()
        os._exit(0)

    process_pid = os.getpid()
    PID_FILE.seek(0)
    PID_FILE.truncate()
    PID_FILE.write(str(process_pid))
    PID_FILE.flush()


def remove_pid_file():
    if PID_FILE is not None:
        PID_FILE.close()
        util.remove_file(PID_FILE.name)


def sigterm_handler(signo, stack):
    sys.exit(0)

def sigabrt_handler(signo, stack):
    sys.exit(1)


def func_daemon():
    global LIBVIRT_CONN
    global QOS_MANAGER_ENTRY

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGABRT, sigabrt_handler)

    @atexit.register
    def daemon_exit_func():
        LIBVIRT_CONN.close()

    LOGGER.info("Try to open libvirtd connection")
    try:
        LIBVIRT_CONN = libvirt.open(LIBVIRT_URI)
    except libvirt.libvirtError:
        LIBVIRT_CONN = None
        LOGGER.error("System internal error, failed to open libvirtd connection!")
        sys.exit(1)

    LOGGER.info("Libvirtd connected.")

    QOS_MANAGER_ENTRY = QosManager(LIBVIRT_CONN)
    QOS_MANAGER_ENTRY.init_scheduler()
    QOS_MANAGER_ENTRY.init_data_collector()
    QOS_MANAGER_ENTRY.init_qos_analyzer()
    QOS_MANAGER_ENTRY.init_qos_controller()

    LOGGER.info("QoS management ready to start.")
    QOS_MANAGER_ENTRY.start_scheduler()

    sys.exit(1)


def create_daemon():
    try:
        pid = os.fork()
    except OSError as error:
        LOGGER.error('Fork daemon process failed: %d (%s)' % (error.errno, error.strerror))
        os._exit(1)
    else:
        if pid == 0:
            atexit.register(remove_pid_file)
            create_pid_file()
        else:
            os._exit(0)
        os.chdir('/')
        os.umask(0o022)
        os.setsid()
        func_daemon()


def setup_vm_env():
    global LIBVIRT_DRIVE_TYPE
    global LIBVIRT_URI

    conn = None
    try:
        conn = libvirt.open()
    except libvirt.libvirtError:
        if not conn:
            LOGGER.error("Can't connect libvirtd!")
        else:
            LOGGER.error("Can't get VMM type")
            conn.close()
        os._exit(1)
    else:
        LIBVIRT_DRIVE_TYPE = conn.getType()
        conn.close()
        if LIBVIRT_DRIVE_TYPE == 'QEMU':
            LIBVIRT_URI = 'qemu:///system'
        else:
            LOGGER.error('Unknown VMM type {}!'.format(LIBVIRT_DRIVE_TYPE))
            os._exit(1)
        LOGGER.info('The VMM type is {}'.format(LIBVIRT_DRIVE_TYPE))


def check_dev_msr():
    if os.getenv("POWER_QOS_MANAGEMENT", "false").lower() != "true":
        return

    try:
        os.stat(MSR_PATH)
    except FileNotFoundError:
        child = subprocess.Popen(["/sbin/modprobe", "msr"])
        child.communicate(timeout=5)
        if child.returncode:
            LOGGER.error("No /dev/cpu/0/msr and failed to execute modprobe msr!")
            os._exit(1)

    if not os.access(MSR_PATH, os.R_OK):
        LOGGER.error(MSR_PATH + " open failed, try chown or chmod +r "
                                "/dev/cpu/*/msr")
        if os.getuid() != 0:
            LOGGER.error("Or simply run skylark as root.")
        os._exit(1)


def check_os_platform():
    if platform.system() != "Linux":
        LOGGER.warning("Skylark only supports linux platform.")
        os._exit(1)


def check_cpu_arch():
    if os.getenv("POWER_QOS_MANAGEMENT", "false").lower() != "true":
        return

    extern_lib = None
    genuine_intel = 0

    child = subprocess.Popen(["/usr/bin/uname", "-a"], stdout=subprocess.PIPE)
    ret = child.communicate(timeout=5)[0].decode().find('x86')
    child.stdout.close()
    if ret == -1:
        LOGGER.warning("Skylark only supports x86 architecture.")
        os._exit(1)

    try:
        extern_lib = MsrLibrary()
    except OSError as error:
        LOGGER.error(str(error))
        os._exit(1)

    if extern_lib:
        genuine_intel = extern_lib.get_cpu_microarch()
    if not genuine_intel:
        LOGGER.warning("Skylark only supports Intel architecture.")
        os._exit(1)


def main():
    check_os_platform()
    check_cpu_arch()
    check_dev_msr()
    setup_vm_env()
    create_daemon()


if __name__ == '__main__':
    main()
