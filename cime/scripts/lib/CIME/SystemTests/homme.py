"""
CIME HOMME test. This class inherits from SystemTestsCommon
"""
from CIME.XML.standard_module_setup import *
from CIME.SystemTests.system_tests_common import SystemTestsCommon
from CIME.build import post_build
from CIME.utils import append_testlog
from CIME.test_status import *
import shutil

logger = logging.getLogger(__name__)

class HOMME(SystemTestsCommon):

    def __init__(self, case):
        """
        initialize an object interface to the SMS system test
        """
        SystemTestsCommon.__init__(self, case)
        case.load_env()

    def build_phase(self, sharedlib_only=False, model_only=False):
        if not sharedlib_only:
            # Build HOMME
            srcroot  = self._case.get_value("SRCROOT")
            mach     = self._case.get_value("MACH")
            procs    = self._case.get_value("TOTALPES")
            exeroot  = self._case.get_value("EXEROOT")
            baseline = self._case.get_value("BASELINE_ROOT")
            basecmp  = self._case.get_value("BASECMP_CASE")
            compare  = self._case.get_value("COMPARE_BASELINE")
            gmake    = self._case.get_value("GMAKE")
            cprnc    = self._case.get_value("CCSM_CPRNC")

            if compare:
                basename = basecmp
                baselinedir = baseline
            else:
                basename = ""
                baselinedir = exeroot

            if (mach in ["sandiatoss3"]):
                preqx_kokkos_args = "-DBUILD_HOMME_PREQX_KOKKOS=ON -DKOKKOS_PATH=/home/onguba/kokkos/build-omp-nodebug"
            elif (mach in ["anvil"]):
                preqx_kokkos_args = "-DBUILD_HOMME_PREQX_KOKKOS=ON -DKOKKOS_PATH=/home/onguba/kokkos/build-serial-omp-nodebug"
            else :
                preqx_kokkos_args = ""


            cmake_cmd_fast = "cmake -C {}/components/homme/cmake/machineFiles/{}.cmake -DUSE_NUM_PROCS={} {} {}/components/homme -DHOMME_TESTING_PROFILE=dev -DHOMME_BASELINE_DIR={}/{} -DCPRNC_DIR={}/..".format(srcroot, mach, procs, preqx_kokkos_args, srcroot, baselinedir, basename, cprnc)
            cmake_cmd_strict = "cmake -C {}/components/homme/cmake/machineFiles/{}-strict.cmake -DUSE_NUM_PROCS={} {} {}/components/homme -DHOMME_TESTING_PROFILE=dev -DHOMME_BASELINE_DIR={}/{} -DCPRNC_DIR={}/..".format(srcroot, mach, procs, preqx_kokkos_args, srcroot, baselinedir, basename, cprnc)

            exeroot_fast = os.path.join(exeroot, "fast")
            exeroot_strict = os.path.join(exeroot, "strict")

            os.mkdir(exeroot_fast)
            os.mkdir(exeroot_strict)
            run_cmd_no_fail(cmake_cmd_fast, arg_stdout=os.path.join(exeroot_fast, "homme.bldlog"), combine_output=True, from_dir=exeroot_fast)
            if (mach in ["anvil", "sandiatoss3"]):
                run_cmd_no_fail(cmake_cmd_strict, arg_stdout=os.path.join(exeroot_strict, "homme.bldlog"), combine_output=True, from_dir=exeroot_strict)

            run_cmd_no_fail("{} -j8".format(gmake), arg_stdout=os.path.join(exeroot_fast, "homme.bldlog"), combine_output=True, from_dir=exeroot_fast)
            if (mach in ["anvil", "sandiatoss3"]):
                run_cmd_no_fail("{} -j8".format(gmake), arg_stdout=os.path.join(exeroot_strict, "homme.bldlog"), combine_output=True, from_dir=exeroot_strict)

            post_build(self._case, [os.path.join(exeroot_fast, "homme.bldlog")], build_complete=True)
            post_build(self._case, [os.path.join(exeroot_strict, "homme.bldlog")], build_complete=True)

    def run_phase(self):

        rundir   = self._case.get_value("RUNDIR")
        exeroot  = self._case.get_value("EXEROOT")
        baseline = self._case.get_value("BASELINE_ROOT")
        compare  = self._case.get_value("COMPARE_BASELINE")
        generate = self._case.get_value("GENERATE_BASELINE")
        basegen  = self._case.get_value("BASEGEN_CASE")
        gmake    = self._case.get_value("GMAKE")
        mach     = self._case.get_value("MACH")

        log = os.path.join(rundir, "homme.log")
        if os.path.exists(log):
            os.remove(log)

        exeroot_fast = os.path.join(exeroot, "fast")
        exeroot_strict = os.path.join(exeroot, "strict")

        if generate:
            full_baseline_dir = os.path.join(baseline, basegen, "tests", "baseline")
            stat = run_cmd("{} -j 4 baseline".format(gmake), arg_stdout=log, combine_output=True, from_dir=exeroot_fast)[0]
            if (mach in ["anvil", "sandiatoss3"]):
                stat = run_cmd("{} -j 4 baseline".format(gmake), arg_stdout=log, combine_output=True, from_dir=exeroot_strict)[0]
            if stat == 0:
                if os.path.isdir(full_baseline_dir):
                    shutil.rmtree(full_baseline_dir)

                shutil.copytree(os.path.join(exeroot_fast, "tests", "baseline"), full_baseline_dir)
                if (mach in ["anvil", "sandiatoss3"]):
                    shutil.copytree(os.path.join(exeroot_strict, "tests", "baseline"), full_baseline_dir)

        elif compare:
            stat = run_cmd("ctest -E cxx", arg_stdout=log, combine_output=True, from_dir=exeroot_fast)[0]
            if (mach in ["anvil", "sandiatoss3"]):
                stat = run_cmd("ctest", arg_stdout=log, combine_output=True, from_dir=exeroot_strict)[0]

        else:
            stat = run_cmd("{} -j 4 baseline".format(gmake), arg_stdout=log, combine_output=True, from_dir=exeroot_fast)[0]
            if (mach in ["anvil", "sandiatoss3"]):
                stat = run_cmd("{} -j 4 baseline".format(gmake), arg_stdout=log, combine_output=True, from_dir=exeroot_strict)[0]

            stat = run_cmd("ctest -E cxx", arg_stdout=log, combine_output=True, from_dir=exeroot_fast)[0]
            if (mach in ["anvil", "sandiatoss3"]):
                stat = run_cmd("ctest", arg_stdout=log, combine_output=True, from_dir=exeroot_strict)[0]

        # Add homme.log output to TestStatus.log so that it can
        # appear on the dashboard. Otherwise, the TestStatus.log
        # is pretty useless for this test.
        append_testlog(open(log, "r").read())

        expect(stat == 0, "RUN FAIL for HOMME")

    # Homme is a bit of an oddball test since it's not really running the E3SM model
    # We need to override some methods to make the core infrastructure work.

    def _generate_baseline(self):
        with self._test_status:
            self._test_status.set_status(GENERATE_PHASE, TEST_PASS_STATUS)

    def _compare_baseline(self):
        with self._test_status:
            self._test_status.set_status(BASELINE_PHASE, TEST_PASS_STATUS)
