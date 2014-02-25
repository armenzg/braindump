import unittest
from check_pending_builds import pending_builds_status

### THINGS TO TEST/ASSERT ###
# 1) OK from 0 to warning_threshold - 1
# 2) WARNING from warning_threshold to critical_threshold - 1
# 3) CRITICAL from critical_threshold and up

## THINGS NOT BEING TESTED FOR ###
# 1) UNKNOWN since that is in main and only executed when an exception occurs
# 2) Ranges of warning and critical thresholds since testing boundaries for 1 set, should hold true for any set

class TestSequenceFunctions(unittest.TestCase):

    warning_threshold = 100
    critical_threshold = 200

    def test_0_boundary(self):
        """Test 0 and 0 + 1 are OK"""
        for x in range(0, 2):
            assert pending_builds_status(x, self.critical_threshold, self.warning_threshold) == 'OK'

    def test_warning_boundary(self):
        """Test warning_threshold - 1 to warning_threshold + 1"""
        assert pending_builds_status(self.warning_threshold - 1, self.critical_threshold, self.warning_threshold) == 'OK'
        for x in range(self.warning_threshold, self.warning_threshold + 2):
            assert pending_builds_status(x, self.critical_threshold, self.warning_threshold) == 'WARNING'

    def test_critical_boundary(self):
        """Test critical_threshold - 1 to critical_threshold + 1"""
        assert pending_builds_status(self.critical_threshold - 1, self.critical_threshold, self.warning_threshold) == 'WARNING'
        for x in range(self.critical_threshold, self.critical_threshold + 2):
            assert pending_builds_status(x, self.critical_threshold, self.warning_threshold) == 'CRITICAL'

if __name__ == '__main__':
    unittest.main()