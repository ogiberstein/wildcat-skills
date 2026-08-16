// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {AccruesAtRestCampaign, MintedClaimsCampaign} from "../src/campaigns/Specimens.sol";

/// @title The reason a campaign gives, after it fails.
/// @notice A property function can only say no. `explain` is where the reason
/// lives, and this asserts that replaying a failing sequence and calling it
/// returns the law's own words rather than something the harness invented.
contract ExplainTest {
    function test_explain_names_the_quantities_that_disagreed() external {
        MintedClaimsCampaign campaign = new MintedClaimsCampaign();
        campaign.deposit(1);
        string[8] memory details = campaign.explain();
        require(bytes(details[0]).length > 0, "no reason given");
        require(
            keccak256(bytes(details[0]))
                == keccak256("held plus owed differs from claimed plus accrued"),
            "the reason is not the one the law gives"
        );
    }

    /// @notice The same, for a law that judges a transition rather than a state.
    /// @dev Worth its own case. A pair law's reason has to survive the harness
    /// holding one of the two observations in storage between calls, and a
    /// harness that lost the earlier one would still return a string -- just
    /// the wrong one.
    function test_explain_carries_the_reason_a_pair_law_gave() external {
        AccruesAtRestCampaign campaign = new AccruesAtRestCampaign();
        campaign.poke(1);
        string[8] memory details = campaign.explain();
        require(
            keccak256(bytes(details[6]))
                == keccak256("debt rose while time stood still and assets stayed"),
            "the reason is not the one the law gives"
        );
    }

    /// @notice Before any call, a pair law has nothing to compare and says so.
    function test_explain_is_empty_for_the_pair_laws_before_the_first_call()
        external
    {
        AccruesAtRestCampaign campaign = new AccruesAtRestCampaign();
        string[8] memory details = campaign.explain();
        require(bytes(details[0]).length > 0, "a one-state law gave no reason");
        require(bytes(details[5]).length == 0, "a pair law judged a pair it did not have");
    }
}
