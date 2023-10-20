// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract FileContract {
    mapping(address => string) ACL;
    mapping(address => string) addressToKey;

    event LogEvent(address invoker, uint256 timestamp, string description);

    struct LogData{
        uint256 timestamp;
        address invoker;
        string description;
    }

    LogData[] logList;
    string[] blockTag;
    string filename;
    string description;

    uint256 create;
    uint256 update;
    uint256 size;
    uint256 blocks;

    uint256[] challenge;
    string[] response;

    address ownerAddress;

    constructor(
        string[] memory _blockTag,
        string memory _filename,
        string memory _description,
        string memory _owner_key,
        uint256 _size
    ) public {
        // Initialize the file metadata
        blockTag = _blockTag;
        filename = _filename;
        description = _description;
        size = _size;
        blocks = _blockTag.length;
        create = block.timestamp;
        update = block.timestamp;

        ownerAddress = msg.sender;
        addressToKey[msg.sender] = _owner_key;
        ACL[msg.sender] = "rw";

        logList.push(LogData(block.timestamp, msg.sender, "Initially store file"));
        emit LogEvent(msg.sender, block.timestamp, "Initially store file");
    }

    function get_metadata() public view returns (
        string memory,
        string memory,
        uint256,
        uint256,
        uint256,
        uint256,
        address
    ){
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission");
        return(
            filename,
            description,
            create,
            update,
            size,
            blocks,
            ownerAddress
        );
    }

    function get_all_tag() public view returns (
        string[] memory
    ){
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission");
        return blockTag;
    }

    function get_tags(
        uint256[] memory TagList
    ) public view returns (string[] memory) {
        require(msg.sender == ownerAddress, "You don't have permission");
        string[] memory temp = new string[](TagList.length);

        for (uint256 i = 0; i < TagList.length; i++) {
            temp[i] = blockTag[TagList[i]];
        }

        return temp;
    }

    function get_owner_address() public view returns(address){
        return ownerAddress;
    }

    function get_ACL(address userAddress) public view returns(string memory){
        return ACL[userAddress];
    }

    function assign_ACL(
        string[] memory permissions,
        string[] memory keys,
        address[] memory users
    ) public {
        require(msg.sender == ownerAddress, "You don't have permission");

        for (uint256 i = 0; i < users.length; i++) {
            ACL[users[i]] = permissions[i];
            addressToKey[users[i]] = keys[i];
            logList.push(LogData(block.timestamp,msg.sender,string(abi.encodePacked("Assign permission ", permissions[i], " to address ", addressToString(users[i])))));
            emit LogEvent(msg.sender,block.timestamp,string(abi.encodePacked("Assign permission ", permissions[i], " to address ", addressToString(users[i]))));
        }
    }

    function revoke_users(
        address[] memory users
    ) public {
        require(msg.sender == ownerAddress, "You don't have permission");
        for (uint256 i = 0; i < users.length; i++) {
            ACL[users[i]] = "";
            addressToKey[users[i]] = "";
            logList.push(LogData(block.timestamp,msg.sender,string(abi.encodePacked("Revoke user address ", addressToString(users[i])))));
            emit LogEvent(msg.sender,block.timestamp,string(abi.encodePacked("Revoke user address ", addressToString(users[i]))));
        }
    }

    function get_key() public returns(
        string memory
    ){
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission");
        logList.push(LogData(block.timestamp,msg.sender,string(abi.encodePacked("User ", addressToString(msg.sender)," retrieve file"))));
        emit LogEvent(msg.sender,block.timestamp,string(abi.encodePacked("User ", addressToString(msg.sender)," retrieve file")));
        return addressToKey[msg.sender];
    }

    function submit_challenge(
        uint256[] memory BlockList
    ) public {
        require(msg.sender == ownerAddress, "You don't have permission");
        logList.push(LogData(block.timestamp,msg.sender,"Submit challenge"));
        emit LogEvent(msg.sender,block.timestamp,"Submit challenge");
        challenge = BlockList;
    }

    function get_challenge() public view returns (uint256[] memory) {
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission");
        return challenge;
    }

    function submit_response(
        string[] memory _blockList
    ) public {
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission");
        logList.push(LogData(block.timestamp,msg.sender,"Submit response"));
        emit LogEvent(msg.sender,block.timestamp,"Submit response");
        response = _blockList;
    }

    function get_response() public view returns (
        string[] memory
    ) {
        require(msg.sender == ownerAddress, "You don't have permission");
        return response;
    }

    function get_log() public view returns(LogData[] memory){
        require(msg.sender == ownerAddress, "You don't have permission");
        return logList;
    }

    function addressToString(address addr) internal pure returns (string memory) {
        bytes32 value = bytes32(uint256(uint160(addr)));
        bytes memory alphabet = "0123456789abcdef";

        bytes memory str = new bytes(42);
        str[0] = "0";
        str[1] = "x";

        for (uint256 i = 0; i < 20; i++) {
            str[2 + i * 2] = alphabet[uint8(value[i + 12] >> 4)];
            str[3 + i * 2] = alphabet[uint8(value[i + 12] & 0x0f)];
        }

        return string(str);
    }
}
