#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""vdsm hardware prerequisites plugin."""


import os
import struct
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import util
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """Detect hardware virtualization properties.

    Environment:
        VdsmEnv.CHECK_VIRT_HARDWARE -- enable hardware detection.

    """

    CPU_INTEL = 'GenuineIntel'
    CPU_AMD = 'AuthenticAMD'
    CPU_POWR = 'IBM_POWER'

    def _getCPUVendor(self):
        ret = None

        with open('/proc/cpuinfo', 'r') as f:
            for line in f.readlines():
                self.logger.debug('cpuinfo: %s', line.strip())

                if ':' in line:
                    k, v = line.split(':', 1)
                    k = k.strip()
                    v = v.strip()
                    if (
                        k == 'vendor_id' and
                        v in (self.CPU_INTEL, self.CPU_AMD)
                    ):
                        ret = v
                    if k == 'cpu' and 'power' in v.lower():
                        ret = self.CPU_POWER

        if ret is None:
            raise RuntimeError(_('Architecture is unsupported'))

        return ret

    def _cpuid(self, func):
        cpuid = '/dev/cpu/0/cpuid'
        if not os.path.exists(cpuid):
            raise AttributeError('No %s' % cpuid)
        with open('/dev/cpu/0/cpuid') as f:
            f.seek(func)
            ret = struct.unpack('IIII', f.read(16))
        self.logger.debug('cpuid: %s', ret)
        return ret

    def _cpu_has_vmx_support(self):
        eax, ebx, ecx, edx = self._cpuid(1)
        # CPUID.1:ECX.VMX[bit 5] -> VT
        ret = ecx & (1 << 5) != 0
        self.logger.debug('vmx support: %s', ret)
        return ret

    def _cpu_has_svm_support(self):
        SVM_CPUID_FEATURE_SHIFT = 2
        SVM_CPUID_FUNC = 0x8000000a

        ret = False

        eax, ebx, ecx, edx = self._cpuid(0x80000000)
        if eax >= SVM_CPUID_FUNC:
            eax, ebx, ecx, edx = self._cpuid(0x80000001)
            ret = (ecx & (1 << SVM_CPUID_FEATURE_SHIFT)) != 0

        self.logger.debug('svm support: %s', ret)
        return ret

    def _prdmsr(self, cpu, index):
        ret = -1

        msr = '/dev/cpu/%d/msr' % cpu
        if not os.path.exists(msr):
            raise AttributeError('No %s' % msr)
        with open(msr, 'r') as f:
            try:
                f.seek(index)
                ret = struct.unpack('L', f.read(8))[0]
            except struct.error:
                pass

        self.logger.debug('prdmsr: %s', ret)
        return ret

    def _vmx_enabled_by_bios(self):
        MSR_IA32_FEATURE_CONTROL = 0x3a
        MSR_IA32_FEATURE_CONTROL_LOCKED = 0x1
        MSR_IA32_FEATURE_CONTROL_VMXON_ENABLED = 0x4

        msr = self._prdmsr(0, MSR_IA32_FEATURE_CONTROL)
        ret = (
            msr & (
                MSR_IA32_FEATURE_CONTROL_LOCKED |
                MSR_IA32_FEATURE_CONTROL_VMXON_ENABLED
            )
        ) != MSR_IA32_FEATURE_CONTROL_LOCKED

        self.logger.debug('vmx bios: %s', ret)
        return ret

    def _svm_enabled_by_bios(self):
        SVM_VM_CR_SVM_DISABLE = 4
        MSR_VM_CR = 0xc0010114

        vm_cr = self._prdmsr(0, MSR_VM_CR)
        ret = (vm_cr & (1 << SVM_VM_CR_SVM_DISABLE)) == 0
        self.logger.debug('svm bios: %s', ret)
        return ret

    def _check_kvm_support_on_power(self):
        ret = False
        with open('/proc/cpuinfo', 'r') as f:
            for line in f.readlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    k = k.strip()
                    v = v.strip()
                    if k == 'platform' and 'powernv' in v.lower():
                        ret = True
                        break
        self.logger.debug('kvm power: %s', ret)
        return ret

    def _isVirtualizationEnabled(self):
        cpu_ok = bios_ok = False

        vendor = self._getCPUVendor()
        if vendor == self.CPU_INTEL:
            bios_ok = self._vmx_enabled_by_bios()
            cpu_ok = self._cpu_has_vmx_support()
        elif vendor == self.CPU_AMD:
            bios_ok = self._svm_enabled_by_bios()
            cpu_ok = self._cpu_has_svm_support()
        elif vendor == self.CPU_POWER:
            if self._check_kvm_support_on_power():
                bios_ok = True
                cpu_ok = True

        self.logger.debug(
            'virtualization support %s (cpu: %s, bios: %s)',
            vendor,
            cpu_ok,
            bios_ok
        )
        return bios_ok and cpu_ok

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.CHECK_VIRT_HARDWARE,
            True
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.CHECK_VIRT_HARDWARE
        ],
    )
    def _validate_virtualization(self):
        try:
            if not self._isVirtualizationEnabled():
                raise RuntimeError(
                    _('Hardware does not support virtualization')
                )
            self.logger.info(_('Hardware supports virtualization'))
        except AttributeError:
            self.logger.debug('Cannot detect virualization', exc_info=True)
            self.logger.warning(
                _('Cannot detect if hardware supports virtualization')
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.CHECK_VIRT_HARDWARE
        ],
    )
    def _validate_optional(self):
        if self._getCPUVendor() in (self.CPU_INTEL, self.CPU_AMD):
            with open('/proc/cpuinfo', 'r') as f:
                if 'constant_tsc' not in f.read():
                    self.logger.warning(
                        _(
                            'Machine does not support constant '
                            'timestamp counter, this may effect performance'
                        )
                    )


# vim: expandtab tabstop=4 shiftwidth=4
