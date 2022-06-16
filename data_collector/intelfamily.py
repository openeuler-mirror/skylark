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
Description: This file is used for providing the encoding of intel model
"""
# @code

INTEL_NUMTOMODEL_DICT = {
    0x0E: 'INTEL_FAM6_CORE_YONAH',
    0x0F: 'INTEL_FAM6_CORE2_MEROM',
    0x16: 'INTEL_FAM6_CORE2_MEROM_L',
    0x17: 'INTEL_FAM6_CORE2_PENRYN',
    0x1D: 'INTEL_FAM6_CORE2_DUNNINGTON',
    0x1E: 'INTEL_FAM6_NEHALEM',
    0x1F: 'INTEL_FAM6_NEHALEM_G',
    0x1A: 'INTEL_FAM6_NEHALEM_EP',
    0x2E: 'INTEL_FAM6_NEHALEM_EX',
    0x25: 'INTEL_FAM6_WESTMERE',
    0x2C: 'INTEL_FAM6_WESTMERE_EP',
    0x2F: 'INTEL_FAM6_WESTMERE_EX',
    0x2A: 'INTEL_FAM6_SANDYBRIDGE',
    0x2D: 'INTEL_FAM6_SANDYBRIDGE_X',
    0x3A: 'INTEL_FAM6_IVYBRIDGE',
    0x3E: 'INTEL_FAM6_IVYBRIDGE_X',
    0x3C: 'INTEL_FAM6_HASWELL',
    0x3F: 'INTEL_FAM6_HASWELL_X',
    0x45: 'INTEL_FAM6_HASWELL_L',
    0x46: 'INTEL_FAM6_HASWELL_G',
    0x3D: 'INTEL_FAM6_BROADWELL',
    0x47: 'INTEL_FAM6_BROADWELL_G',
    0x4F: 'INTEL_FAM6_BROADWELL_X',
    0x56: 'INTEL_FAM6_BROADWELL_D',
    0x4E: 'INTEL_FAM6_SKYLAKE_L',
    0x5E: 'INTEL_FAM6_SKYLAKE',
    0x55: 'INTEL_FAM6_SKYLAKE_X',
    0x8E: 'INTEL_FAM6_KABYLAKE_L',
    0x9E: 'INTEL_FAM6_KABYLAKE',
    0xA5: 'INTEL_FAM6_COMETLAKE',
    0xA6: 'INTEL_FAM6_COMETLAKE_L',
    0x66: 'INTEL_FAM6_CANNONLAKE_L',
    0x6A: 'INTEL_FAM6_ICELAKE_X',
    0x6C: 'INTEL_FAM6_ICELAKE_D',
    0x7D: 'INTEL_FAM6_ICELAKE',
    0x7E: 'INTEL_FAM6_ICELAKE_L',
    0x9D: 'INTEL_FAM6_ICELAKE_NNPI',
    0x8A: 'INTEL_FAM6_LAKEFIELD',
    0xA7: 'INTEL_FAM6_ROCKETLAKE',
    0x8C: 'INTEL_FAM6_TIGERLAKE_L',
    0x8D: 'INTEL_FAM6_TIGERLAKE',
    0x8F: 'INTEL_FAM6_SAPPHIRERAPIDS_X',
    0x97: 'INTEL_FAM6_ALDERLAKE',
    0x9A: 'INTEL_FAM6_ALDERLAKE_L',
    0xB7: 'INTEL_FAM6_RAPTORLAKE',
    0x1C: 'INTEL_FAM6_ATOM_BONNELL',
    0x26: 'INTEL_FAM6_ATOM_BONNELL_MID',
    0x36: 'INTEL_FAM6_ATOM_SALTWELL',
    0x27: 'INTEL_FAM6_ATOM_SALTWELL_MID',
    0x35: 'INTEL_FAM6_ATOM_SALTWELL_TABLET',
    0x37: 'INTEL_FAM6_ATOM_SILVERMONT',
    0x4D: 'INTEL_FAM6_ATOM_SILVERMONT_D',
    0x4A: 'INTEL_FAM6_ATOM_SILVERMONT_MID',
    0x4C: 'INTEL_FAM6_ATOM_AIRMONT',
    0x5A: 'INTEL_FAM6_ATOM_AIRMONT_MID',
    0x75: 'INTEL_FAM6_ATOM_AIRMONT_NP',
    0x5C: 'INTEL_FAM6_ATOM_GOLDMONT',
    0x5F: 'INTEL_FAM6_ATOM_GOLDMONT_D',
    0x7A: 'INTEL_FAM6_ATOM_GOLDMONT_PLUS',
    0x86: 'INTEL_FAM6_ATOM_TREMONT_D',
    0x96: 'INTEL_FAM6_ATOM_TREMONT',
    0x9C: 'INTEL_FAM6_ATOM_TREMONT_L',
    0x57: 'INTEL_FAM6_XEON_PHI_KNL',
    0x85: 'INTEL_FAM6_XEON_PHI_KNM',
    0x09: 'INTEL_FAM6_QUARK_X1000'
}