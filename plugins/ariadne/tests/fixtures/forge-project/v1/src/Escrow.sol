// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

/// @notice Test material for ariadne's capture. Not a contract to deploy.
contract Escrow {
    address public owner;
    uint256 public balance;

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balance += msg.value;
    }
}
