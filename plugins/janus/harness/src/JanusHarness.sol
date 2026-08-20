// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.25;

import {StateDeltaRecorder} from "./StateDeltaRecorder.sol";
import {HostAdapter} from "./HostAdapter.sol";

/// @dev The gate engine. It drives one action through a host adapter, records
///      the delta around it, and offers the checks a conformance test uses to
///      compare the delta against a manifest. It attributes an effect to the
///      hook by the recorded accessor: a call the hook made is one whose
///      accessor is the hook address, which is how gate 1 tells the hook's own
///      calls apart from the host's.
abstract contract JanusHarness is StateDeltaRecorder {
  struct DriveResult {
    bool reverted;
    bytes revertData;
    Delta delta;
    uint256 valueBefore;
    uint256 valueAfter;
  }

  /// @dev Drive an action and record the state delta around it. A revert is
  ///      caught so the harness can inspect the delta and the rollback rather
  ///      than aborting the test.
  function _drive(
    HostAdapter adapter,
    string memory action,
    address caller,
    bytes memory params
  ) internal returns (DriveResult memory result) {
    result.valueBefore = adapter.valueSnapshot();
    _beginRecording();
    try adapter.driveAction(action, caller, params) {
      result.reverted = false;
    } catch (bytes memory data) {
      result.reverted = true;
      result.revertData = data;
    }
    result.delta = _endRecording(0);
    result.valueAfter = adapter.valueSnapshot();
  }

  /// @dev The number of external calls the hook itself initiated.
  function _hookCallCount(Delta memory delta, address hookAddr) internal pure returns (uint256 n) {
    for (uint256 i; i < delta.calls.length; ++i) {
      if (delta.calls[i].accessor == hookAddr) ++n;
    }
  }

  /// @dev Gate 1: every call the hook made targets an allowed address. A call
  ///      the hook made to anything outside `allowed` is an effect the manifest
  ///      did not enumerate, so it is forbidden.
  function _gate1_hookCallsWithinAllowed(
    Delta memory delta,
    address hookAddr,
    address[] memory allowed
  ) internal pure returns (bool) {
    for (uint256 i; i < delta.calls.length; ++i) {
      if (delta.calls[i].accessor != hookAddr) continue;
      bool ok;
      for (uint256 j; j < allowed.length; ++j) {
        if (delta.calls[i].target == allowed[j]) {
          ok = true;
          break;
        }
      }
      if (!ok) return false;
    }
    return true;
  }

  /// @dev The ETH value the hook itself moved.
  function _hookValueMoved(Delta memory delta, address hookAddr) internal pure returns (uint256 v) {
    for (uint256 i; i < delta.calls.length; ++i) {
      if (delta.calls[i].accessor == hookAddr) v += delta.calls[i].value;
    }
  }
}
