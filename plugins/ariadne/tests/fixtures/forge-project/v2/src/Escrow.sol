// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

/// @notice Test material for ariadne's capture. Not a contract to deploy.
/// v2 against v1: a new function, and a storage variable inserted ahead of
/// balance so the layout moves. Both are deliberate, so the delta is real.
contract Escrow {
    address public owner;
    uint256 public deadline;
    uint256 public balance;

    constructor(uint256 deadline_) {
        owner = msg.sender;
        deadline = deadline_;
    }

    function deposit() external payable {
        balance += msg.value;
    }

    function sweep(address to) external {
        require(msg.sender == owner, "not owner");
        balance = 0;
        payable(to).transfer(address(this).balance);
    }
}
