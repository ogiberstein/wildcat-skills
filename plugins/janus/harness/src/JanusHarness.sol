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

  /// @dev The transitive closure of the hook's causal effects: a call is the
  ///      hook's if its accessor is the hook, or the accessor is a target the
  ///      hook already reached. Attributing by the immediate accessor alone
  ///      would only see the hook's direct callees, and a hook could launder a
  ///      forbidden call one hop through a permitted target. Iterating to a
  ///      fixpoint over (accessor, target) pairs closes that hole with no need
  ///      for frame depth.
  function _hookAttributed(
    Delta memory delta,
    address hookAddr
  ) internal pure returns (bool[] memory attributed) {
    uint256 n = delta.calls.length;
    attributed = new bool[](n);
    bool changed = true;
    while (changed) {
      changed = false;
      for (uint256 i; i < n; ++i) {
        if (attributed[i]) continue;
        address acc = delta.calls[i].accessor;
        bool causal = acc == hookAddr;
        if (!causal) {
          for (uint256 k; k < n; ++k) {
            if (attributed[k] && delta.calls[k].target == acc) {
              causal = true;
              break;
            }
          }
        }
        if (causal) {
          attributed[i] = true;
          changed = true;
        }
      }
    }
  }

  /// @dev The number of external calls the hook caused, directly or through a
  ///      target it reached.
  function _hookCallCount(Delta memory delta, address hookAddr) internal pure returns (uint256 n) {
    bool[] memory attributed = _hookAttributed(delta, hookAddr);
    for (uint256 i; i < attributed.length; ++i) {
      if (attributed[i]) ++n;
    }
  }

  /// @dev Gate 1: every call the hook caused targets an allowed address. A call
  ///      anywhere in the hook's causal subtree to a target outside `allowed`
  ///      is an effect the manifest did not enumerate, so it is forbidden.
  function _gate1_hookCallsWithinAllowed(
    Delta memory delta,
    address hookAddr,
    address[] memory allowed
  ) internal pure returns (bool) {
    bool[] memory attributed = _hookAttributed(delta, hookAddr);
    for (uint256 i; i < delta.calls.length; ++i) {
      if (!attributed[i]) continue;
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

  /// @dev The fresh value the hook caused to move, across its whole causal
  ///      subtree, counting only kinds that move fresh value.
  function _hookValueMoved(Delta memory delta, address hookAddr) internal pure returns (uint256 v) {
    bool[] memory attributed = _hookAttributed(delta, hookAddr);
    for (uint256 i; i < delta.calls.length; ++i) {
      if (attributed[i] && _movesValue(delta.calls[i].kind)) v += delta.calls[i].value;
    }
  }

  /// @dev Whether a recording captured any effect at all. A gate for an action
  ///      expected to do something must assert this, so it cannot pass
  ///      vacuously on an action that reverted or did nothing.
  function _deltaHasEffects(Delta memory delta) internal pure returns (bool) {
    return delta.writes.length > 0 || delta.calls.length > 0;
  }
}
