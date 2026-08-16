// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {Observation, Observe} from "../../src/Observation.sol";
import {RecordedClaimNeverShrinks} from "../../src/laws/RecordedClaimNeverShrinks.sol";
import {QueueOrderPreserved} from "../../src/laws/QueueOrderPreserved.sol";
import {ReservesCoverPayableClaims} from "../../src/laws/ReservesCoverPayableClaims.sol";
import {ClaimHaircut} from "../../specimens/ClaimHaircut.sol";
import {QueueJumped} from "../../specimens/QueueJumped.sol";
import {PayableBeyondReserves} from "../../specimens/PayableBeyondReserves.sol";

/// @title The counterexamples for the withdrawal-claim family.
/// @notice One reduced sequence per law, replayable with no fuzzer, no seed
/// and no engine.
///
/// All three run at a scale of one or two units. That is not a stylistic
/// preference: a queue defect is about which entry moves rather than how much,
/// so the smallest amounts that keep the entries distinct are the ones that
/// show it, and a counterexample moving a hundred units would be hiding its
/// shape behind its size.
contract ClaimsCounterexamples {
    /// `ClaimHaircut.deposit(1)`, `reserve(1)`, `haircut(0, 1)`. Three calls,
    /// and three is the floor: there is no claim to write down without a
    /// reservation, and nothing to reserve without a deposit.
    ///
    /// The claim recorded at one is rewritten to nothing, and the unit is moved
    /// into fees. Conservation holds across the write-down, the reserves are
    /// recomputed so they stay within claims, and the queue is still in order.
    /// The only thing that changed is a number a lender was given.
    function test_recorded_claim_never_shrinks_counterexample() external {
        ClaimHaircut target = new ClaimHaircut();
        target.deposit(1);
        target.reserve(1);

        Observation memory earlier = Observe.takeWithQueue(target);
        require(earlier.queue.length == 1, "the queue does not hold one claim");
        require(earlier.queue[0].owed == 1, "the claim is not owed 1");

        target.haircut(0, 1);
        Observation memory later = Observe.takeWithQueue(target);
        require(later.queue[0].owed == 0, "the claim was not written down");
        require(later.accruedFees == 1, "the unit did not become a fee");

        RecordedClaimNeverShrinks law = new RecordedClaimNeverShrinks();
        (bool held, ) = law.check(earlier, later);
        require(!held, "the counterexample no longer reproduces");
    }

    /// `QueueJumped.deposit(2)`, `reserve(1)`, `reserve(1)`, `payClaim(1)`.
    /// Four calls. Two claims are the minimum for an ordering to exist at all,
    /// and each needs its own reservation.
    ///
    /// The second claim is paid in full while the first has received nothing.
    /// Every amount involved is correct: one unit left the system, one unit of
    /// claim was retired, and the reserves fell by one. A single state is
    /// enough to see it, because the payment is recorded against the claim.
    function test_queue_order_preserved_counterexample() external {
        QueueJumped target = new QueueJumped();
        target.deposit(2);
        target.reserve(1);
        target.reserve(1);
        target.payClaim(1);

        (uint256 firstOwed, uint256 firstPaid) = target.claimAt(0);
        (, uint256 secondPaid) = target.claimAt(1);
        require(firstOwed == 1 && firstPaid == 0, "the older claim was not skipped");
        require(secondPaid == 1, "the newer claim was not paid");

        QueueOrderPreserved law = new QueueOrderPreserved();
        (bool held, ) = law.check(target);
        require(!held, "the counterexample no longer reproduces");
    }

    /// `PayableBeyondReserves.deposit(1)`, `reserve(1)`, `reserve(1)`. Three
    /// calls, and no payment at all.
    ///
    /// Both reservations are individually within what the system holds, so each
    /// is recorded; together they ask for two units against the one unit
    /// deposited, so only one unit is ever set aside. A correct system declares
    /// the first claim payable and stops. This one declares both, and the
    /// second lender is holding a promise the system cannot keep.
    ///
    /// Nothing has gone wrong yet in any observable except the declaration,
    /// which is the point: the lie is available to read before anybody acts on
    /// it.
    function test_reserves_cover_payable_counterexample() external {
        PayableBeyondReserves target = new PayableBeyondReserves();
        target.deposit(1);
        target.reserve(1);
        target.reserve(1);

        require(target.claimCount() == 2, "two claims were not recorded");
        require(target.reservedAssets() == 1, "more than one unit was set aside");
        require(target.payableThrough() == 2, "the system did not declare both payable");

        ReservesCoverPayableClaims law = new ReservesCoverPayableClaims();
        (bool held, ) = law.check(target);
        require(!held, "the counterexample no longer reproduces");
    }
}
