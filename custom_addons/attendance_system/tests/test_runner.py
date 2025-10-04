# -*- coding: utf-8 -*-
"""
Test Runner cho Attendance System Unit Tests
Chạy tất cả các test cases và tạo báo cáo kết quả
"""

import unittest
import sys
import os
from io import StringIO

# Import các test modules
from .test_check_in_cases import TestCheckInCases, TestCheckInEdgeCases
from .test_register_cases import TestRegisterFaceCases, TestRegisterFaceEdgeCases, TestRegisterFaceValidationCases


class AttendanceTestRunner:
    """Test runner cho Attendance System"""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
    
    def run_all_tests(self, verbosity=2):
        """Chạy tất cả các test cases"""
        print("=" * 70)
        print("ATTENDANCE SYSTEM UNIT TESTS")
        print("=" * 70)
        
        # Tạo test suite
        test_suite = unittest.TestSuite()
        
        # Thêm test cases cho check-in
        test_suite.addTest(unittest.makeSuite(TestCheckInCases))
        test_suite.addTest(unittest.makeSuite(TestCheckInEdgeCases))
        
        # Thêm test cases cho register
        test_suite.addTest(unittest.makeSuite(TestRegisterFaceCases))
        test_suite.addTest(unittest.makeSuite(TestRegisterFaceEdgeCases))
        test_suite.addTest(unittest.makeSuite(TestRegisterFaceValidationCases))
        
        # Chạy tests
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            stream=sys.stdout,
            buffer=True
        )
        
        result = runner.run(test_suite)
        
        # Lưu kết quả
        self.total_tests = result.testsRun
        self.failed_tests = len(result.failures)
        self.error_tests = len(result.errors)
        self.passed_tests = self.total_tests - self.failed_tests - self.error_tests
        
        # In báo cáo tổng kết
        self._print_summary(result)
        
        return result
    
    def _print_summary(self, result):
        """In báo cáo tổng kết"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Errors: {self.error_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%" if self.total_tests > 0 else "0%")
        
        if result.failures:
            print(f"\nFAILED TESTS ({len(result.failures)}):")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
        
        if result.errors:
            print(f"\nERROR TESTS ({len(result.errors)}):")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback.split('\\n')[-2]}")
        
        print("=" * 70)
    
    def run_check_in_tests_only(self):
        """Chỉ chạy tests cho check-in"""
        print("Running Check-in Tests Only...")
        
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.makeSuite(TestCheckInCases))
        test_suite.addTest(unittest.makeSuite(TestCheckInEdgeCases))
        
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(test_suite)
    
    def run_register_tests_only(self):
        """Chỉ chạy tests cho register"""
        print("Running Register Tests Only...")
        
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.makeSuite(TestRegisterFaceCases))
        test_suite.addTest(unittest.makeSuite(TestRegisterFaceEdgeCases))
        test_suite.addTest(unittest.makeSuite(TestRegisterFaceValidationCases))
        
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(test_suite)
    
    def run_specific_test_case(self, test_case_name):
        """Chạy một test case cụ thể"""
        print(f"Running specific test case: {test_case_name}")
        
        # Mapping test case names
        test_cases = {
            'check_in': TestCheckInCases,
            'check_in_edge': TestCheckInEdgeCases,
            'register': TestRegisterFaceCases,
            'register_edge': TestRegisterFaceEdgeCases,
            'register_validation': TestRegisterFaceValidationCases
        }
        
        if test_case_name not in test_cases:
            print(f"Test case '{test_case_name}' not found!")
            print(f"Available test cases: {list(test_cases.keys())}")
            return None
        
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.makeSuite(test_cases[test_case_name]))
        
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(test_suite)


def main():
    """Main function để chạy tests từ command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Attendance System Test Runner')
    parser.add_argument('--test-type', choices=['all', 'check_in', 'register'], 
                       default='all', help='Loại test cần chạy')
    parser.add_argument('--test-case', help='Tên test case cụ thể cần chạy')
    parser.add_argument('--verbosity', type=int, choices=[0, 1, 2], default=2,
                       help='Mức độ chi tiết của output')
    
    args = parser.parse_args()
    
    runner = AttendanceTestRunner()
    
    if args.test_case:
        result = runner.run_specific_test_case(args.test_case)
    elif args.test_type == 'check_in':
        result = runner.run_check_in_tests_only()
    elif args.test_type == 'register':
        result = runner.run_register_tests_only()
    else:
        result = runner.run_all_tests(verbosity=args.verbosity)
    
    # Exit với code phù hợp
    if result and (result.failures or result.errors):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
