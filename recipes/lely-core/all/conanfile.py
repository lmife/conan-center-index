import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rm, rmdir
from conan.tools.gnu import AutotoolsToolchain, Autotools
from conan.tools.layout import basic_layout

required_conan_version = ">=1.53.0"


class LelyConan(ConanFile):
    name = "lely-core"
    description = (
        "The Lely core libraries are a collection of C and C++ libraries and tools, "
        "providing high-performance I/O and sensor/actuator control for robotics and IoT applications. "
        "The libraries are cross-platform and have few dependencies. "
        "They can be even be used on bare-metal microcontrollers with as little as 32 kB RAM."
    )
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.com/lely_industries/lely-core/"
    topics = ("canopen",)
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "rt": [True, False],
        "threads": [True, False],
        "ecss-compliance": [True, False],
        "errno": [True, False],
        "malloc": [True, False],
        "stdio": [True, False],
        "cxx": [True, False],
        "daemon": [True, False],
        "diag": [True, False],
        "canfd": [True, False],
        "dcf": [True, False],
        "dcf-restore": [True, False],
        "obj-default": [True, False],
        "obj-file": [True, False],
        "obj-limits": [True, False],
        "obj-name": [True, False],
        "obj-upload": [True, False],
        "sdev": [True, False],
        "csdo": [True, False],
        "rpdo": [True, False],
        "tpdo": [True, False],
        "mpdo": [True, False],
        "sync": [True, False],
        "time": [True, False],
        "emcy": [True, False],
        "lss": [True, False],
        "wtm": [True, False],
        "master": [True, False],
        "ng": [True, False],
        "nmt-boot": [True, False],
        "nmt-cfg": [True, False],
        "gw": [True, False],
        "gw-txt": [True, False],
        "coapp-master": [True, False],
        "coapp-slave": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "rt": True,
        "threads": True,
        "ecss-compliance": False,
        "errno": True,
        "malloc": True,
        "stdio": True,
        "cxx": True,
        "daemon": True,
        "diag": True,
        "canfd": True,
        "dcf": True,
        "dcf-restore": True,
        "obj-default": True,
        "obj-file": True,
        "obj-limits": True,
        "obj-name": True,
        "obj-upload": True,
        "sdev": True,
        "csdo": True,
        "rpdo": True,
        "tpdo": True,
        "mpdo": True,
        "sync": True,
        "time": True,
        "emcy": True,
        "lss": True,
        "wtm": True,
        "master": True,
        "ng": True,
        "nmt-boot": True,
        "nmt-cfg": True,
        "gw": True,
        "gw-txt": True,
        "coapp-master": True,
        "coapp-slave": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(
                f"{self.ref} is only compatible with Linux. "
                "Windows requires proprietary software from https://www.ixxat.com/technical-support/support/windows-driver-software "
                "hence support for it will be skipped for now "
            )
        if self.settings.compiler != "gcc":
            raise ConanInvalidConfiguration(
                f"{self.ref} can only be compiled with GCC currently"
            )

    def build_requirements(self):
        self.tool_requires("libtool/2.4.7")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()

        tc = AutotoolsToolchain(self)
        tc.configure_args += [
            "--disable-cython",
            "--disable-python",
            "--disable-tools",
            "--disable-dependency-tracking",
            "--disable-maintainer-mode",
        ]
        if self.options.get_safe("ecss-compliance"):
            tc.configure_args.append("--enable-ecss-compliance")

        disable_options = {
            "threads",
            "rt",
            "errno",
            "malloc",
            "stdio",
            "cxx",
            "daemon",
            "diag",
            "canfd",
            "dcf",
            "dcf-restore",
            "obj-default",
            "obj-file",
            "obj-limits",
            "obj-name",
            "obj-upload",
            "sdev",
            "csdo",
            "rpdo",
            "tpdo",
            "mpdo",
            "sync",
            "time",
            "emcy",
            "lss",
            "wtm",
            "master",
            "ng",
            "nmt-boot",
            "nmt-cfg",
            "gw",
            "gw-txt",
            "coapp-master",
            "coapp-slave",
        }
        for option in disable_options:
            if not self.options.get_safe(option):
                tc.configure_args.append(f"--disable-{option}")

        tc.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install()

        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        components = {
            "can": {"requires": ["libc", "util"]},
            "co": {"requires": ["libc", "util", "can"]},
            "coapp": {"requires": ["libc", "io2", "co"]},
            "ev": {"requires": ["libc", "util"]},
            "io2": {"requires": ["libc", "util", "can", "ev"]},
            "libc": {
                "requires": [],
                "system_libs": ["pthread"] if self.options.threads else [],
            },
            "tap": {"requires": ["libc"]},
            "util": {"requires": ["libc"], "system_libs": ["m"]},
        }
        for component, dependencies in components.items():
            self.cpp_info.components[component].set_property("pkg_config_name", f"liblely-{component}")
            self.cpp_info.components[component].libs = [f"lely-{component}"]
            self.cpp_info.components[component].requires = dependencies.get(
                "requires", []
            )
            self.cpp_info.components[component].system_libs = dependencies.get(
                "system_libs", []
            )
